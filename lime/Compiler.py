from ast import FunctionType
from typing import cast

from llvmlite import ir

from AST import (
    AssignmentExpression,
    BooleanLiteral,
    CallExpression,
    IfStatement,
    Node,
    NodeType,
    Expression,
    Program,
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
        self.type_map: dict[str, ir.Type] = {
            "int": ir.IntType(32),
            "float": ir.FloatType(),
            "bool": ir.IntType(1),
        }

        self.module: ir.Module = ir.Module("main")
        self.builder: ir.IRBuilder = ir.IRBuilder()
        self.env = Environment()
        self.errors: list[str] = []

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

            case _:
                raise ValueError(f"Unhandled compile path {node.type()}")

    def __visit_program(self, node: Program) -> None:
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
        assert node.body is not None and node.ret_type is not None

        name: str = cast(IdentifierLiteral, node.name).value
        body: BlockStatement = node.body
        params: list[IdentifierLiteral] = node.params
        _param_names: list[str] = [p.value for p in params]
        _param_types: list[ir.Type] = []  # TODO: Implement params
        ret_type: ir.Type = self.type_map[node.ret_type]

        fn_type = ir.FunctionType(ret_type, params)
        fn = ir.Function(self.module, fn_type, name)
        self.env.define(name, fn, fn_type)

        prev_builder = self.builder
        prev_env = self.env

        block: ir.Block = fn.append_basic_block(f"{name}_entry")
        self.env = Environment(parent=self.env)
        self.builder = ir.IRBuilder(block)

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
        args = []
        # args_type = []

        match callee_name:
            case _:
                res = self.env.lookup(callee_name)
                if res is None:
                    self.__error(f"Cannot call undefined function '{callee_name}'")
                    return None

                fn, _ = res
                val = self.builder.call(fn, args)
                return val, val.type

    # endregion

    # region Helpers
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

    # endregion
