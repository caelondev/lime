from typing import cast

from llvmlite import ir

from AST import Node, NodeType, Expression, Program
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
        }

        self.module: ir.Module = ir.Module("main")
        self.builder: ir.IRBuilder = ir.IRBuilder()
        self.env = Environment()

    def compile(self, node: Node) -> None:
        match node.type():
            case NodeType.ProgramNode:
                self.__visit_program(cast(Program, node))

            case NodeType.ExpressionStatement:
                self.__visit_expr_stmt(cast(ExpressionStatement, node))
            case NodeType.VariableDeclarationStatement:
                self.__visit_var_decl_stmt(cast(VariableDeclarationStatement, node))
            case NodeType.FunctionDeclarationStatement:
                self.__visit_fn_decl_stmt(cast(FunctionDeclarationStatement, node))
            case NodeType.BlockStatement:
                self.__visit_block_stmt(cast(BlockStatement, node))
            case NodeType.ReturnStatement:
                self.__visit_ret_stmt(cast(ReturnStatement, node))

            case NodeType.BinaryExpression:
                self.__visit_bin_expr(cast(BinaryExpression, node))

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
        val, t = self.__resolve_val(cast(Expression, node.value), node.value_type)
        if self.env.lookup(name) is None:
            ptr = self.builder.alloca(t)
            self.builder.store(val, ptr)
            self.env.define(name, ptr, t)
        else:  # Reassign
            res = self.env.lookup(name)
            assert res is not None
            ptr, _ = res
            self.builder.store(val, ptr)

    def __visit_block_stmt(self, node: BlockStatement) -> None:
        for stmt in node.statements:
            self.compile(stmt)

    def __visit_ret_stmt(self, node: ReturnStatement) -> None:
        val_expr: Expression = cast(Expression, node.value)
        val, _ = self.__resolve_val(val_expr)

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
    def __visit_bin_expr(self, node: BinaryExpression) -> tuple[ir.Value, ir.Type]:
        op = node.op
        left, ltype = self.__resolve_val(cast(Expression, node.left))
        right, rtype = self.__resolve_val(cast(Expression, node.right))

        val = None
        typ = None

        if isinstance(ltype, ir.IntType) and isinstance(rtype, ir.IntType):
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
                    raise NotImplementedError("int pow not yet implemented")
                case _:
                    raise ValueError(f"Unsupported int binary operator {op}")
        elif isinstance(ltype, ir.FloatType) and isinstance(rtype, ir.FloatType):
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
                    raise NotImplementedError("float pow not yet implemented")
                case _:
                    raise ValueError(f"Unsupported float binary operator {op}")
        else:
            raise TypeError(
                f"Mismatched or unsupported operand types in binary expr: "
                f"{ltype} vs {rtype}"
            )

        assert val is not None and typ is not None
        return val, typ

    # endregion

    # region Helpers
    def __resolve_val(
        self, node: Expression, val_type: str | None = None
    ) -> tuple[ir.Value, ir.Type]:
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

            case NodeType.IdentifierLiteral:
                ident_node: IdentifierLiteral = cast(IdentifierLiteral, node)
                result = self.env.lookup(ident_node.value)
                if result is None:
                    raise NameError(f"undefined variable: {ident_node.value!r}")
                ptr, t = result
                val = self.builder.load(ptr)
                return val, t

            case NodeType.BinaryExpression:
                return self.__visit_bin_expr(cast(BinaryExpression, node))

            case _:
                raise ValueError(f"Unhandled __resolve_val path {node.type()}")

    # endregion
