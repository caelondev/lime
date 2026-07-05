from typing import cast

from llvmlite import ir

from AST import Node, NodeType, Expression, Program
from AST import ExpressionStatement
from AST import BinaryExpression
from AST import IntegerLiteral, FloatLiteral
from Token import TokenType


class Compiler:
    def __init__(self) -> None:
        self.type_map: dict[str, ir.Type] = {
            "int": ir.IntType(32),
            "float": ir.FloatType(),
        }

        self.module: ir.Module = ir.Module("main")
        self.builder: ir.IRBuilder = ir.IRBuilder()

    def compile(self, node: Node) -> None:
        match node.type():
            case NodeType.ProgramNode:
                self.__visit_program(cast(Program, node))

            case NodeType.ExpressionStatement:
                self.__visit_expr_stmt(cast(ExpressionStatement, node))

            case NodeType.BinaryExpression:
                self.__visit_bin_expr(cast(BinaryExpression, node))

    def __visit_program(self, node: Program) -> None:
        main_fn: str = "main"
        param_types: list[ir.Type] = []
        return_type: ir.Type = self.type_map["int"]

        fn_type = ir.FunctionType(return_type, param_types)
        fn = ir.Function(self.module, fn_type, name=main_fn)

        block = fn.append_basic_block(f"{main_fn}_entry")
        self.builder = ir.IRBuilder(block)

        for stmt in node.statements:
            self.compile(stmt)

        ret_val: ir.Constant = ir.Constant(self.type_map["int"], 0)
        self.builder.ret(ret_val)

    # region Statements
    def __visit_expr_stmt(self, node: ExpressionStatement) -> None:
        self.compile(node.expr)

    # endregion

    # region Statements
    def __visit_bin_expr(self, node: BinaryExpression) -> tuple[ir.Value, ir.Type]:
        op = node.op
        left, ltype = self.__resolve_val(node.left)
        right, rtype = self.__resolve_val(cast(Expression, node.right))

        val = None
        typ = None

        if isinstance(rtype, ir.IntType) and isinstance(ltype, ir.IntType):
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
                    pass
        elif isinstance(rtype, ir.FloatType) and isinstance(ltype, ir.FloatType):
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
                    pass

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

            case NodeType.BinaryExpression:
                return self.__visit_bin_expr(cast(BinaryExpression, node))

            case _:
                raise ValueError(f"Unhandled __resolve_val path {node.type()}")

    # endregion
