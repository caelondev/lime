from abc import ABC, abstractmethod
from enum import Enum

from Token import TokenType


class NodeType(Enum):
    ProgramNode = "Program"

    # Statements
    ExpressionStatement = "ExpressionStatement"
    VariableDeclarationStatement = "VariableDeclarationStatement"
    IfStatement = "IfStatement"
    FunctionDeclarationStatement = "FunctionDeclarationStatement"
    BlockStatement = "BlockStatement"
    ReturnStatement = "ReturnStatement"

    # Expressions
    AssignmentExpression = "AssignmentExpression"
    BinaryExpression = "BinaryExpression"
    CallExpression = "CallExpression"
    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"
    BooleanLiteral = "BooleanLiteral"
    IdentifierLiteral = "IdentifierLiteral"
    StringLiteral = "StringLiteral"

    # Helpers
    FunctionParameter = "FunctionParameter"


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


# region Helpers
class FunctionParameter(Expression):
    def __init__(self, name: str, value_type: str) -> None:
        self.name = name
        self.value_type = value_type

    def type(self) -> NodeType:
        return NodeType.FunctionParameter

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name,
            "value_type": self.value_type,
        }


# endregion

# region Statement


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


class IfStatement(Statement):
    def __init__(
        self,
        condition: Expression,
        consequence: BlockStatement,
        alternate: Statement | None,
    ) -> None:
        self.condition = condition
        self.consequence = consequence
        self.alternate = alternate

    def type(self) -> NodeType:
        return NodeType.IfStatement

    def json(self) -> dict:
        if self.alternate is None:
            return {
                "type": self.type().value,
                "condition": self.condition.json(),
                "consequence": self.consequence.json(),
            }
        return {
            "type": self.type().value,
            "condition": self.condition.json(),
            "consequence": self.consequence.json(),
            "alternate": self.alternate.json(),
        }


class FunctionDeclarationStatement(Statement):
    def __init__(
        self,
        name=None,
        params: list[FunctionParameter] = [],
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


# region Expression
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


class AssignmentExpression(Expression):
    def __init__(self, left: Expression, right: Expression | None = None) -> None:
        self.left = left
        self.right = right

    def type(self) -> NodeType:
        return NodeType.AssignmentExpression

    def json(self) -> dict:
        assert self.right is not None
        return {
            "type": self.type().value,
            "assignee": self.left.json(),
            "value": self.right.json(),
        }


class CallExpression(Expression):
    def __init__(self, callee: Expression, args: list[Expression]) -> None:
        self.callee = callee
        self.args = args if args else []

    def type(self) -> NodeType:
        return NodeType.CallExpression

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "callee": self.callee.json(),
            "args": [arg.json() for arg in self.args],
        }


class BooleanLiteral(Expression):
    def __init__(self, value: bool) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.BooleanLiteral

    def json(self) -> dict:
        return {"type": self.type().value, "boolean": self.value}


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


class StringLiteral(Expression):
    def __init__(self, value: str) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.StringLiteral

    def json(self) -> dict:
        return {"type": self.type().value, "string": self.value}


# endregion
