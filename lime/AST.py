from abc import ABC, abstractmethod
from enum import Enum

from Token import TokenType


class NodeType(Enum):
    ProgramNode = "Program"

    # Statements
    ExpressionStatement = "ExpressionStatement"

    # Expressions
    BinaryExpression = "BinaryExpression"
    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"


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
