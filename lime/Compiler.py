from typing import cast

from llvmlite import ir

from AST import (
    AssignmentExpression,
    BooleanLiteral,
    CallExpression,
    FunctionParameter,
    IfStatement,
    Node,
    NodeType,
    Expression,
    Program,
    StringLiteral,
)
from AST import (
    ExpressionStatement,
    VariableDeclarationStatement,
    FunctionDeclarationStatement,
    BlockStatement,
    ReturnStatement,
)
from AST import BinaryExpression
from AST import IntegerLiteral, FloatLiteral, IdentifierLiteral
from Token import TokenType

from Environment import Environment


class Compiler:
    def __init__(self) -> None:
        string_type = ir.LiteralStructType(
            [ir.IntType(64), ir.PointerType(ir.IntType(8))]
        )

        self.type_map: dict[str, ir.Type] = {
            "int": ir.IntType(32),
            "float": ir.FloatType(),
            "bool": ir.IntType(1),
            "string": string_type,
            "void": ir.VoidType(),
        }

        self.module: ir.Module = ir.Module("main")
        self.builder: ir.IRBuilder = ir.IRBuilder()
        self.env = Environment()
        self.errors: list[str] = []
        self._string_counter = 0

        self._bool_str_cache: dict[bool, ir.GlobalVariable] = {}

        self.__init_builtins()

    def __init_builtins(self):
        def __init_print():
            ftype = ir.FunctionType(
                ir.IntType(32),
                [ir.IntType(8).as_pointer()],
                var_arg=True,
            )
            return ir.Function(self.module, ftype, "printf")

        def __init_lime_print_fns():
            int_fn = ir.Function(
                self.module,
                ir.FunctionType(ir.VoidType(), [ir.IntType(32)]),
                "lime_print_int",
            )
            float_fn = ir.Function(
                self.module,
                ir.FunctionType(ir.VoidType(), [ir.DoubleType()]),
                "lime_print_float",
            )
            bool_fn = ir.Function(
                self.module,
                ir.FunctionType(ir.VoidType(), [ir.IntType(32)]),
                "lime_print_bool",
            )
            str_fn = ir.Function(
                self.module,
                ir.FunctionType(
                    ir.VoidType(),
                    [ir.IntType(64), ir.PointerType(ir.IntType(8))],
                ),
                "lime_print_str",
            )
            return {"int": int_fn, "float": float_fn, "bool": bool_fn, "str": str_fn}

        self.env.define("print", __init_print(), ir.IntType(32))
        self._lime_print = __init_lime_print_fns()

    def compile(self, node: Node) -> None:
        match node.type():
            case NodeType.ProgramNode:
                self.__visit_program(cast(Program, node))

            case NodeType.ExpressionStatement:
                self.__visit_expr_stmt(cast(ExpressionStatement, node))
            case NodeType.VariableDeclarationStatement:
                self.__visit_var_decl_stmt(cast(VariableDeclarationStatement, node))
            case NodeType.IfStatement:
                self.__visit_if_stmt(cast(IfStatement, node))
            case NodeType.FunctionDeclarationStatement:
                self.__visit_fn_decl_stmt(cast(FunctionDeclarationStatement, node))
            case NodeType.BlockStatement:
                self.__visit_block_stmt(cast(BlockStatement, node))
            case NodeType.ReturnStatement:
                self.__visit_ret_stmt(cast(ReturnStatement, node))

            case NodeType.BinaryExpression:
                self.__visit_bin_expr(cast(BinaryExpression, node))
            case NodeType.AssignmentExpression:
                self.__visit_assign_expr(cast(AssignmentExpression, node))
            case NodeType.CallExpression:
                self.__visit_call_expr(cast(CallExpression, node))

            case _:
                raise ValueError(f"Unhandled compile path {node.type()}")

    def __visit_program(self, node: Program) -> None:
        for stmt in node.statements:
            if stmt.type() == NodeType.FunctionDeclarationStatement:
                self.__hoist_fn_sign(cast(FunctionDeclarationStatement, stmt))

        for stmt in node.statements:
            self.compile(stmt)

    # region Statements
    def __visit_expr_stmt(self, node: ExpressionStatement) -> None:
        self.compile(node.expr)

    def __visit_var_decl_stmt(self, node: VariableDeclarationStatement) -> None:
        name: str = cast(IdentifierLiteral, node.name).value

        if self.env.lookup_current(name) is not None:
            self.__error(f"Cannot redeclare identifier '{name}' in the same scope")
            return

        resolved = self.__resolve_val(cast(Expression, node.value), node.value_type)
        if resolved is None:
            self.__error(f"Cannot declare '{name}': its initializer failed to compile")
            return

        val, t = resolved
        ptr = self.builder.alloca(t)
        self.builder.store(val, ptr)
        self.env.define(name, ptr, t)

    def __visit_if_stmt(self, node: IfStatement) -> None:
        resolved = self.__resolve_val(node.condition)
        if resolved is None:
            self.__error(
                "Cannot compile 'if' statement: its condition failed to compile"
            )
            return

        cond, _ = resolved

        if node.alternate is None:
            with self.builder.if_then(cond):
                self.compile(node.consequence)
        else:
            with self.builder.if_else(cond) as (true, otherwise):
                with true:
                    self.compile(node.consequence)
                with otherwise:
                    self.compile(node.alternate)

            # if_then/if_else always creates a merge block for control flow to
            # rejoin. If every branch already terminated (e.g. via `return`),
            # the merge block is unreachable and would otherwise be left with
            # no terminator, which LLVM's verifier rejects.
            assert self.builder.block
            if not self.builder.block.is_terminated:
                self.builder.unreachable()

    def __visit_block_stmt(self, node: BlockStatement) -> None:
        for stmt in node.statements:
            self.compile(stmt)

    def __visit_ret_stmt(self, node: ReturnStatement) -> None:
        val_expr: Expression = cast(Expression, node.value)
        resolved = self.__resolve_val(val_expr)
        if resolved is None:
            self.__error(
                "Cannot compile 'return' statement: its value failed to compile"
            )
            return

        val, _ = resolved
        self.builder.ret(val)

    def __visit_fn_decl_stmt(self, node: FunctionDeclarationStatement) -> None:
        header = node.header
        assert node.body is not None

        name = cast(IdentifierLiteral, header.name).value
        body = node.body
        params = header.params
        param_names = [p.name for p in params]

        res = self.env.lookup_current(name)
        assert res is not None, f"'{name}' should have been hoisted already"
        fn = cast(ir.Function, res[0])
        fn_type = cast(ir.FunctionType, res[1])
        param_types = fn_type.args

        prev_builder = self.builder
        prev_env = self.env

        block = fn.append_basic_block(f"{name}_entry")
        self.env = Environment(parent=self.env)
        self.builder = ir.IRBuilder(block)

        params_ptr = []
        for i, typ in enumerate(param_types):
            ptr = self.builder.alloca(typ)
            self.builder.store(fn.args[i], ptr)
            params_ptr.append(ptr)

        for i, (t, pname) in enumerate(zip(param_types, param_names)):
            self.env.define(pname, params_ptr[i], t)

        self.compile(body)

        self.env = prev_env
        self.builder = prev_builder

    # endregion

    # region Expression
    def __visit_bin_expr(
        self, node: BinaryExpression
    ) -> tuple[ir.Value, ir.Type] | None:
        op = node.op

        left_resolved = self.__resolve_val(cast(Expression, node.left))
        if left_resolved is None:
            self.__error(
                f"Cannot compile binary expression: left-hand side of '{op}' failed to compile"
            )
            return None

        right_resolved = self.__resolve_val(cast(Expression, node.right))
        if right_resolved is None:
            self.__error(
                f"Cannot compile binary expression: right-hand side of '{op}' failed to compile"
            )
            return None

        left, ltype = left_resolved
        right, rtype = right_resolved

        val = None
        typ = None
        op_map = {
            TokenType.EQUAL: "==",
            TokenType.NOT_EQUAL: "!=",
            TokenType.LESS: "<",
            TokenType.LESS_EQUAL: "<=",
            TokenType.GREATER: ">",
            TokenType.GREATER_EQUAL: ">=",
        }

        if isinstance(ltype, ir.IntType) and isinstance(rtype, ir.IntType):
            if node.op in op_map:
                result = self.builder.icmp_signed(op_map[node.op], left, right)
                return result, self.type_map["bool"]

            typ = self.type_map["int"]
            match op:
                case TokenType.PLUS:
                    val = self.builder.add(left, right)
                case TokenType.MINUS:
                    val = self.builder.sub(left, right)
                case TokenType.ASTERISK:
                    val = self.builder.mul(left, right)
                case TokenType.SLASH:
                    val = self.builder.sdiv(left, right)
                case TokenType.MODULO:
                    val = self.builder.srem(left, right)
                case TokenType.POW:
                    # TODO: add pow
                    self.__error("Integer 'pow' operator is not yet implemented")
                    return None
                case _:
                    self.__error(f"Unsupported integer binary operator '{op}'")
                    return None
        elif isinstance(ltype, ir.FloatType) and isinstance(rtype, ir.FloatType):
            if node.op in op_map:
                result = self.builder.fcmp_ordered(op_map[node.op], left, right)
                return result, self.type_map["bool"]

            typ = self.type_map["float"]
            match op:
                case TokenType.PLUS:
                    val = self.builder.fadd(left, right)
                case TokenType.MINUS:
                    val = self.builder.fsub(left, right)
                case TokenType.ASTERISK:
                    val = self.builder.fmul(left, right)
                case TokenType.SLASH:
                    val = self.builder.fdiv(left, right)
                case TokenType.MODULO:
                    val = self.builder.frem(left, right)
                case TokenType.POW:
                    # TODO: add pow
                    self.__error("Float 'pow' operator is not yet implemented")
                    return None
                case _:
                    self.__error(f"Unsupported float binary operator '{op}'")
                    return None
        elif ltype == self.type_map["string"] and rtype == self.type_map["string"]:
            if op not in (TokenType.EQUAL, TokenType.NOT_EQUAL):
                self.__error(f"Unsupported string binary operator '{op}'")
                return None

            l_len = self.builder.extract_value(left, 0)
            l_ptr = self.builder.extract_value(left, 1)
            r_len = self.builder.extract_value(right, 0)
            r_ptr = self.builder.extract_value(right, 1)

            entry_block = self.builder.block

            same_len = self.builder.icmp_signed("==", l_len, r_len)

            loop_cond_block = self.builder.append_basic_block("streq_loop_cond")
            loop_body_block = self.builder.append_basic_block("streq_loop_body")
            merge_block = self.builder.append_basic_block("streq_merge")

            self.builder.cbranch(same_len, loop_cond_block, merge_block)

            self.builder.position_at_end(loop_cond_block)
            i_phi = self.builder.phi(ir.IntType(64), name="i")
            i_phi.add_incoming(ir.Constant(ir.IntType(64), 0), entry_block)

            in_bounds = self.builder.icmp_signed("<", i_phi, l_len)
            self.builder.cbranch(in_bounds, loop_body_block, merge_block)
            loop_cond_end = self.builder.block

            # loop_body: compare byte i of each string
            #            mismatch -> jump straight to merge as "not equal"
            #            match    -> increment i, back to loop_cond
            self.builder.position_at_end(loop_body_block)
            l_byte_ptr = self.builder.gep(l_ptr, [i_phi], inbounds=True)
            r_byte_ptr = self.builder.gep(r_ptr, [i_phi], inbounds=True)
            l_byte = self.builder.load(l_byte_ptr)
            r_byte = self.builder.load(r_byte_ptr)
            byte_match = self.builder.icmp_signed("==", l_byte, r_byte)

            i_next = self.builder.add(i_phi, ir.Constant(ir.IntType(64), 1))
            self.builder.cbranch(byte_match, loop_cond_block, merge_block)
            loop_body_end = self.builder.block

            i_phi.add_incoming(i_next, loop_body_end)

            # merge: entry_block (lengths differed) -> false
            #        loop_cond_block (ran out of bytes clean) -> true
            #        loop_body_block (mismatch found) -> false
            self.builder.position_at_end(merge_block)
            result_phi = self.builder.phi(ir.IntType(1), name="streq_result")
            result_phi.add_incoming(ir.Constant(ir.IntType(1), 0), entry_block)
            result_phi.add_incoming(ir.Constant(ir.IntType(1), 1), loop_cond_end)
            result_phi.add_incoming(ir.Constant(ir.IntType(1), 0), loop_body_end)

            if op == TokenType.NOT_EQUAL:
                result = cast(ir.Value, self.builder.not_(result_phi))
            else:
                result = result_phi

            return result, self.type_map["bool"]
        else:
            self.__error(
                f"Mismatched or unsupported operand types in binary expression: "
                f"{ltype} vs {rtype}"
            )
            return None

        assert val is not None and typ is not None
        return val, typ

    def __visit_assign_expr(
        self, node: AssignmentExpression
    ) -> tuple[ir.Value, ir.Type] | None:
        name = cast(IdentifierLiteral, node.left).value
        env_val = self.env.lookup(name)
        if env_val is None:
            self.__error(f"Cannot assign to '{name}': it is undefined")
            return None

        assert node.right is not None
        resolved = self.__resolve_val(node.right)
        if resolved is None:
            self.__error(
                f"Cannot assign to '{name}': right-hand side failed to compile"
            )
            return None

        val, _ = resolved
        ptr, t = env_val
        self.builder.store(val, ptr)

        return val, t

    def __visit_call_expr(
        self, node: CallExpression
    ) -> tuple[ir.Value, ir.Type] | None:
        callee_name = cast(IdentifierLiteral, node.callee).value
        resolved_args: list[tuple[ir.Value, ir.Type] | None] = [
            self.__resolve_val(a) for a in node.args
        ]
        for a in resolved_args:
            if a is None:
                self.__error(
                    f"Cannot compile call to '{callee_name}': an argument failed to compile"
                )
                return None
        args: list[tuple[ir.Value, ir.Type]] = cast(
            list[tuple[ir.Value, ir.Type]], resolved_args
        )

        if callee_name == "print":
            return self.__call_print(args)
        elif callee_name == "type":
            return self.__call_type(args)

        res = self.env.lookup(callee_name)
        if res is None:
            self.__error(f"Cannot call undefined function '{callee_name}'")
            return None

        fn, _ = res
        val = self.builder.call(fn, [v for v, _ in args])
        return val, val.type

    # endregion

    # region Helpers
    def __hoist_fn_sign(self, node: FunctionDeclarationStatement) -> None:
        header = node.header
        assert header.ret_type is not None

        name = cast(IdentifierLiteral, header.name).value

        if self.env.lookup_current(name) is not None:
            self.__error(f"Cannot redeclare function '{name}'")
            return

        param_types = [self.type_map[p.value_type] for p in header.params]
        ret_type = self.type_map[header.ret_type]
        fn_type = ir.FunctionType(ret_type, param_types)
        fn = ir.Function(self.module, fn_type, name)
        self.env.define(name, fn, fn_type)

    def __resolve_val(
        self, node: Expression, val_type: str | None = None
    ) -> tuple[ir.Value, ir.Type] | None:
        match node.type():
            case NodeType.IntegerLiteral:
                int_node: IntegerLiteral = cast(IntegerLiteral, node)
                key = val_type if val_type is not None else "int"
                value, typ = int_node.value, self.type_map[key]
                return ir.Constant(typ, value), typ

            case NodeType.FloatLiteral:
                float_node: FloatLiteral = cast(FloatLiteral, node)
                key = val_type if val_type is not None else "float"
                value, typ = float_node.value, self.type_map[key]
                return ir.Constant(typ, value), typ

            case NodeType.BooleanLiteral:
                bool_node: BooleanLiteral = cast(BooleanLiteral, node)
                key = val_type if val_type is not None else "bool"
                value = 1 if bool_node.value else 0
                typ = self.type_map[key]
                return ir.Constant(typ, value), typ

            case NodeType.StringLiteral:
                n = cast(StringLiteral, node).value
                return self.__conv_to_string(n)

            case NodeType.IdentifierLiteral:
                ident_node: IdentifierLiteral = cast(IdentifierLiteral, node)
                result = self.env.lookup(ident_node.value)
                if result is None:
                    self.__error(f"Undefined variable '{ident_node.value}'")
                    return None
                ptr, t = result
                val = self.builder.load(ptr)
                return val, t

            case NodeType.BinaryExpression:
                return self.__visit_bin_expr(cast(BinaryExpression, node))

            case NodeType.AssignmentExpression:
                return self.__visit_assign_expr(cast(AssignmentExpression, node))

            case NodeType.CallExpression:
                return self.__visit_call_expr(cast(CallExpression, node))

            case _:
                self.__error(f"Unhandled expression type in resolve_val: {node.type()}")
                return None

    def __error(self, msg: str) -> None:
        self.errors.append(msg)

    def __make_raw_cstr_global(self, text: str, tag: str) -> ir.GlobalVariable:
        encoded = text.encode("utf8")
        str_type = ir.ArrayType(ir.IntType(8), len(encoded))
        str_const = ir.Constant(str_type, bytearray(encoded))

        g = ir.GlobalVariable(self.module, str_type, name=tag)
        g.linkage = "internal"
        g.global_constant = True
        g.initializer = str_const  # type: ignore[assignment]
        return g

    def __conv_to_string(self, string: str) -> tuple[ir.Value, ir.Type]:
        encoded = string.encode("utf8")
        length = len(encoded)

        global_str = self.__make_raw_cstr_global(
            string, f"__str_{self.__next_string_id()}"
        )
        data_ptr = self.__gep_to_i8ptr(global_str)

        string_type = self.type_map["string"]
        struct_val = ir.Constant(string_type, ir.Undefined)
        struct_val = self.builder.insert_value(
            struct_val, ir.Constant(ir.IntType(64), length), 0
        )
        struct_val = self.builder.insert_value(struct_val, data_ptr, 1)

        return struct_val, string_type

    def __gep_to_i8ptr(self, global_val: ir.GlobalVariable) -> ir.Value:
        zero = ir.Constant(ir.IntType(32), 0)
        return self.builder.gep(global_val, [zero, zero], inbounds=True)

    def __call_print(
        self, args: list[tuple[ir.Value, ir.Type]]
    ) -> tuple[ir.Value, ir.Type]:
        for val, typ in args:
            if isinstance(typ, ir.IntType) and typ.width == 1:
                widened = self.builder.zext(val, ir.IntType(32))
                self.builder.call(self._lime_print["bool"], [widened])

            elif isinstance(typ, ir.IntType):
                self.builder.call(self._lime_print["int"], [val])

            elif isinstance(typ, ir.FloatType):
                promoted = self.builder.fpext(val, ir.DoubleType())
                self.builder.call(self._lime_print["float"], [promoted])

            elif isinstance(typ, ir.DoubleType):
                self.builder.call(self._lime_print["float"], [val])

            elif typ == self.type_map["string"]:
                length = self.builder.extract_value(val, 0)
                data = self.builder.extract_value(val, 1)
                self.builder.call(self._lime_print["str"], [length, data])

            else:
                self.__error(f"'print' does not support argument type {typ}")
                return ir.Constant(ir.IntType(32), 0), ir.IntType(32)

        return ir.Constant(ir.IntType(32), 0), ir.IntType(32)

    def __call_type(
        self, args: list[tuple[ir.Value, ir.Type]]
    ) -> tuple[ir.Value, ir.Type] | None:
        if len(args) != 1:
            self.__error(f"'type_name' expects exactly 1 argument, got {len(args)}")
            return None

        _, typ = args[0]
        name = self.__type_to_name(typ)
        return self.__conv_to_string(name)

    def __type_to_name(self, typ: ir.Type) -> str:
        if isinstance(typ, ir.IntType) and typ.width == 1:
            return "bool"
        elif isinstance(typ, ir.IntType):
            return "int"
        elif isinstance(typ, (ir.FloatType, ir.DoubleType)):
            return "float"
        elif typ == self.type_map["string"]:
            return "string"
        else:
            return "unknown"

    def __next_string_id(self) -> int:
        self._string_counter += 1
        return self._string_counter

    # endregion
