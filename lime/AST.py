from abc import ABC, abstractmethod
from enum import Enum

from Token import TokenType


class NodeType(Enum):
    ProgramNode = "Program"

    # Statements
    ExpressionStatement = "ExpressionStatement"
    VariableDeclarationStatement = "VariableDeclarationStatement"
    FunctionDeclarationStatement = "FunctionDeclarationStatement"
    BlockStatement = "BlockStatement"
    ReturnStatement = "ReturnStatement"

    # Expressions
    BinaryExpression = "BinaryExpression"
    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"
    IdentifierLiteral = "IdentifierLiteral"


class Node(ABC):
    @abstractmethod
    def type(self) -> NodeType:
        pass

    @abstractmethod
    def json(self) -> dict:
        pass


class Statement(Node):
    pass


class Expression(Node):
    pass


class Program(Node):
    def __init__(self) -> None:
        self.statements: list[Statement] = []

    def type(self) -> NodeType:
        return NodeType.ProgramNode

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "statements": [
                {stmt.type().value: stmt.json()} for stmt in self.statements
            ],
        }


# region


class ExpressionStatement(Statement):
    def __init__(self, expr: Expression) -> None:
        self.expr = expr

    def type(self) -> NodeType:
        return NodeType.ExpressionStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "expr": self.expr.json(),
        }


class VariableDeclarationStatement(Statement):
    def __init__(
        self,
        name: Expression | None = None,
        value: Expression | None = None,
        value_type: str | None = None,
    ) -> None:
        self.name = name
        self.value = value
        self.value_type = value_type

    def type(self) -> NodeType:
        return NodeType.VariableDeclarationStatement

    def json(self) -> dict:
        assert self.name is not None and self.value is not None
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "value": self.value.json(),
            "value_type": self.value_type,
        }


class BlockStatement(Statement):
    def __init__(self, statements: list[Statement]) -> None:
        self.statements = statements

    def type(self) -> NodeType:
        return NodeType.BlockStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "statements": [stmt.json() for stmt in self.statements],
        }


class FunctionDeclarationStatement(Statement):
    def __init__(
        self,
        name=None,
        params: list[Expression] = [],
        ret_type: str | None = None,
        body: BlockStatement | None = None,
    ) -> None:
        self.params = params
        self.body = body
        self.ret_type = ret_type
        self.name = name

    def type(self) -> NodeType:
        return NodeType.FunctionDeclarationStatement

    def json(self) -> dict:
        assert (
            self.ret_type is not None
            and self.body is not None
            and self.name is not None
        )
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "params": [expr.json() for expr in self.params],
            "ret_type": self.ret_type,
            "body": self.body.json(),
        }


class ReturnStatement(Statement):
    def __init__(self, value: Expression | None = None) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.ReturnStatement

    def json(self) -> dict:
        if self.value is not None:
            return {"type": self.type().value, "return_value": self.value.json()}

        return {"type": self.type().value, "return_value": None}


class BinaryExpression(Expression):
    def __init__(
        self, left: Expression, op: TokenType, right: Expression | None = None
    ) -> None:
        self.left = left
        self.op = op
        self.right = right

    def type(self) -> NodeType:
        return NodeType.BinaryExpression

    def json(self) -> dict:
        if self.right is None:
            return {
                "type": self.type().value,
                "left": self.left.json(),
                "operator": self.op.value,
            }

        return {
            "type": self.type().value,
            "left": self.left.json(),
            "operator": self.op.value,
            "right": self.right.json(),
        }


class IntegerLiteral(Expression):
    def __init__(self, value: int) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.IntegerLiteral

    def json(self) -> dict:
        return {"type": self.type().value, "integer": self.value}


class FloatLiteral(Expression):
    def __init__(self, value: float) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.FloatLiteral

    def json(self) -> dict:
        return {"type": self.type().value, "float": self.value}


class IdentifierLiteral(Expression):
    def __init__(self, value: str) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.IdentifierLiteral

    def json(self) -> dict:
        return {"type": self.type().value, "identifier": self.value}
