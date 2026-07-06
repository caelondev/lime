from Lexer import Lexer
from Token import Token, TokenType
from typing import Callable, cast
from enum import Enum, auto

from AST import (
    AssignmentExpression,
    BlockStatement,
    BooleanLiteral,
    FunctionDeclarationStatement,
    IfStatement,
    ReturnStatement,
    Statement,
    Expression,
    Program,
)
from AST import ExpressionStatement, VariableDeclarationStatement
from AST import BinaryExpression
from AST import IntegerLiteral, FloatLiteral, IdentifierLiteral


class PrecedenceType(Enum):
    P_LOWEST = 0
    P_ASSIGNMENT = auto()
    P_LOGICAL_OR = auto()
    P_LOGICAL_AND = auto()
    P_EQUALITY = auto()
    P_COMPARISON = auto()
    P_ADDITIVE = auto()
    P_MULTIPLICATIVE = auto()
    P_POWER = auto()
    P_UNARY = auto()
    P_CALL = auto()


PRECEDENCES = {
    TokenType.ASSIGNMENT: PrecedenceType.P_ASSIGNMENT,
    TokenType.EQUAL: PrecedenceType.P_EQUALITY,
    TokenType.NOT_EQUAL: PrecedenceType.P_EQUALITY,
    TokenType.LESS: PrecedenceType.P_COMPARISON,
    TokenType.LESS_EQUAL: PrecedenceType.P_COMPARISON,
    TokenType.GREATER: PrecedenceType.P_COMPARISON,
    TokenType.GREATER_EQUAL: PrecedenceType.P_COMPARISON,
    TokenType.PLUS: PrecedenceType.P_ADDITIVE,
    TokenType.MINUS: PrecedenceType.P_ADDITIVE,
    TokenType.ASTERISK: PrecedenceType.P_MULTIPLICATIVE,
    TokenType.SLASH: PrecedenceType.P_MULTIPLICATIVE,
    TokenType.MODULO: PrecedenceType.P_MULTIPLICATIVE,
    TokenType.POW: PrecedenceType.P_POWER,
}


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer: Lexer = lexer
        self.errors: list[str] = []
        self.cur_token: Token | None = None
        self.peek_token: Token | None = None

        self.nud_fns: dict[TokenType, Callable] = {
            TokenType.INT: self.__parse_int_literal,
            TokenType.FLOAT: self.__parse_float_literal,
            TokenType.TRUE: self.__parse_bool_literal,
            TokenType.FALSE: self.__parse_bool_literal,
            TokenType.IDENTIFIER: self.__parse_identifier_literal,
            TokenType.LEFT_PARENTHESIS: self.__parse_grouped_expr,
        }
        self.led_fns: dict[TokenType, Callable] = {
            TokenType.PLUS: self.__parse_binary_expr,
            TokenType.MINUS: self.__parse_binary_expr,
            TokenType.ASTERISK: self.__parse_binary_expr,
            TokenType.SLASH: self.__parse_binary_expr,
            TokenType.POW: self.__parse_pow_expr,
            TokenType.MODULO: self.__parse_binary_expr,
            TokenType.ASSIGNMENT: self.__parse_assignment_expr,
            TokenType.LESS: self.__parse_binary_expr,
            TokenType.GREATER: self.__parse_binary_expr,
            TokenType.LESS_EQUAL: self.__parse_binary_expr,
            TokenType.GREATER_EQUAL: self.__parse_binary_expr,
            TokenType.EQUAL: self.__parse_binary_expr,
            TokenType.NOT_EQUAL: self.__parse_binary_expr,
        }

        self.__next_token()  # fill peek_token
        self.__next_token()  # fill cur_token

    def parse_program(self) -> Program:
        program: Program = Program()

        while not self.__is_at_eof():
            stmt = self.__parse_stmt()
            if stmt is not None:
                program.statements.append(stmt)
            else:
                self.__recover()
            self.__next_token()

        return program

    # region Statement Parsers
    def __parse_stmt(self) -> Statement | None:
        match self.__cur().type:
            case TokenType.LET:
                return self.__parse_var_decl_stmt()
            case TokenType.FN:
                return self.__parse_fn_decl_stmt()
            case TokenType.RETURN:
                return self.__parse_return_stmt()
            case TokenType.IF:
                return self.__parse_if_stmt()
            case _:
                return self.__parse_expr_stmt()

    def __parse_expr_stmt(self) -> ExpressionStatement | None:
        expr = self.__parse_expr(PrecedenceType.P_LOWEST)

        if self.__peek_token_is(TokenType.SEMICOLON):
            self.__next_token()

        if expr is not None:
            return ExpressionStatement(expr)

        return None

    def __parse_var_decl_stmt(self) -> VariableDeclarationStatement | None:
        stmt: VariableDeclarationStatement = VariableDeclarationStatement()

        if not self.__expect_peek(TokenType.IDENTIFIER):
            self.__recover()
            return None

        stmt.name = IdentifierLiteral(self.__cur().literal)

        if not self.__expect_peek(TokenType.COLON):
            self.__recover()
            return None

        if not self.__expect_peek(TokenType.TYPE):
            self.__recover()
            return None

        stmt.value_type = self.__cur().literal

        if not self.__expect_peek(TokenType.ASSIGNMENT):
            self.__recover()
            return None

        self.__next_token()  # eat ASSIGNMENT

        stmt.value = self.__parse_expr(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.SEMICOLON):
            self.__recover()
            return None

        return stmt

    def __parse_if_stmt(self) -> IfStatement | None:
        self.__next_token()
        condition = self.__parse_expr(PrecedenceType.P_LOWEST)
        if condition is None:
            self.__recover()
            return None

        if not self.__expect_peek(TokenType.LEFT_BRACE):
            self.__recover()
            return None

        consequence = self.__parse_block_stmt()
        if consequence is None:
            self.__recover()
            return None

        if not self.__peek_token_is(TokenType.ELSE):
            return IfStatement(condition, consequence, alternate=None)

        self.__next_token()  # eat RIGHT_BRACE

        # else if ...
        if self.__peek_token_is(TokenType.IF):
            self.__next_token()  # eat ELSE, cur is now IF
            alternate = self.__parse_if_stmt()
            if alternate is None:
                self.__recover()
                return None
            return IfStatement(condition, consequence, cast(Statement, alternate))

        # else { ... }
        if not self.__expect_peek(TokenType.LEFT_BRACE):
            self.__recover()
            return None

        alternate = self.__parse_block_stmt()
        if alternate is None:
            self.__recover()
            return None

        return IfStatement(condition, consequence, cast(Statement, alternate))

    def __parse_return_stmt(self) -> ReturnStatement | None:
        ret = ReturnStatement()
        if self.__peek_token_is(TokenType.SEMICOLON):
            self.__next_token()
            return ret

        self.__next_token()  # eat RETURN

        ret.value = self.__parse_expr(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.SEMICOLON):
            self.__recover()
            return None

        return ret

    def __parse_fn_decl_stmt(self) -> FunctionDeclarationStatement | None:
        fn_stmt = FunctionDeclarationStatement()
        if not self.__expect_peek(TokenType.IDENTIFIER):
            self.__recover()
            return None

        fn_stmt.name = IdentifierLiteral(self.__cur().literal)

        if not self.__expect_peek(TokenType.LEFT_PARENTHESIS):
            self.__recover()
            return None

        # TODO: Parse params

        if not self.__expect_peek(TokenType.RIGHT_PARENTHESIS):
            self.__recover()
            return None

        if not self.__expect_peek(TokenType.ARROW):
            self.__recover()
            return None

        if not self.__expect_peek(TokenType.TYPE):
            self.__recover()
            return None

        fn_stmt.ret_type = self.__cur().literal

        if not self.__expect_peek(TokenType.LEFT_BRACE):
            self.__recover()
            return None

        body = self.__parse_block_stmt()
        if body is None:
            self.__recover()
            return None

        fn_stmt.body = body

        return fn_stmt

    # endregion

    # region Statement Helpers
    def __parse_block_stmt(self) -> BlockStatement | None:
        stmts: list[Statement] = []

        self.__next_token()  # eat LEFT_BRACE

        while not self.__is_at_eof() and not self.__cur_token_is(TokenType.RIGHT_BRACE):
            stmt = self.__parse_stmt()
            if stmt is None:
                return None

            stmts.append(stmt)
            self.__next_token()

        if not self.__cur_token_is(TokenType.RIGHT_BRACE):
            self.errors.append("Expected closing '}' for block statement.")
            return None

        return BlockStatement(stmts)

    # endregion

    # region Expression Parsers
    def __parse_expr(self, precedence: PrecedenceType) -> Expression | None:
        cur = self.__cur()
        nud_fn = self.nud_fns.get(cur.type)
        if nud_fn is None:
            self.__no_nud_parse_fn_error(cur.type)
            return None

        left_expr = nud_fn()

        while (
            not self.__peek_token_is(TokenType.SEMICOLON)
            and self.peek_token is not None
            and precedence.value < self.__peek_precedence().value
        ):
            led_fn = self.led_fns.get(self.peek_token.type)
            if led_fn is None:
                return left_expr

            self.__next_token()

            left_expr = led_fn(left_expr)

        return left_expr

    def __parse_binary_expr(self, left: Expression) -> Expression:
        cur = self.__cur()
        bin_expr = BinaryExpression(left, cur.type)
        precedence = self.__current_precedence()
        self.__next_token()

        right = self.__parse_expr(precedence)
        if right is None:
            self.errors.append(
                f"Expected expression after '{cur.type}' but found none."
            )

        bin_expr.right = right

        return bin_expr

    def __parse_pow_expr(self, left: Expression) -> Expression:
        cur = self.__cur()
        bin_expr = BinaryExpression(left, cur.type)
        precedence = self.__current_precedence()
        self.__next_token()

        # subtract 1 so a further POW to the right binds tighter here,
        # recursing instead of returning control to __parse_expr's loop.
        right = self.__parse_expr(PrecedenceType(precedence.value - 1))
        if right is None:
            self.errors.append(
                f"Expected expression after '{cur.type}' but found none."
            )
        bin_expr.right = right

        return bin_expr

    def __parse_assignment_expr(self, left: Expression) -> Expression:
        cur = self.__cur()
        bin_expr = AssignmentExpression(left)
        precedence = self.__current_precedence()
        self.__next_token()

        # subtract 1 so a further ASSIGNMENT to the right binds tighter here,
        # recursing instead of returning control to __parse_expr's loop.
        right = self.__parse_expr(PrecedenceType(precedence.value - 1))
        if right is None:
            self.errors.append(
                f"Expected expression after '{cur.type}' but found none."
            )
        bin_expr.right = right

        return bin_expr

    def __parse_int_literal(self) -> Expression | None:
        cur = self.__cur()
        try:
            value = int(cur.literal)
        except ValueError:
            self.errors.append(f"Could not parse '{cur.literal}' as an integer.")
            return None
        return IntegerLiteral(value)

    def __parse_identifier_literal(self) -> Expression | None:
        return IdentifierLiteral(self.__cur().literal)

    def __parse_bool_literal(self) -> Expression | None:
        return BooleanLiteral(self.__cur_token_is(TokenType.TRUE))

    def __parse_float_literal(self) -> Expression | None:
        cur = self.__cur()
        try:
            value = float(cur.literal)
        except ValueError:
            self.errors.append(f"Could not parse '{cur.literal}' as a float.")
            return None
        return FloatLiteral(value)

    def __parse_grouped_expr(self) -> Expression | None:
        self.__next_token()

        expr = self.__parse_expr(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.RIGHT_PARENTHESIS):
            return None

        return expr

    # endregion

    # region Parser Helpers
    def __cur(self) -> Token:
        """Return cur_token, narrowed to non-None. Asserts once so call
        sites don't have to repeat `assert self.cur_token is not None`."""
        assert self.cur_token is not None, "cur_token accessed before parser init"
        return self.cur_token

    def __peek(self) -> Token:
        assert self.peek_token is not None, "peek_token accessed past EOF"
        return self.peek_token

    def __current_precedence(self) -> PrecedenceType:
        return PRECEDENCES.get(self.__cur().type, PrecedenceType.P_LOWEST)

    def __peek_precedence(self) -> PrecedenceType:
        return PRECEDENCES.get(self.__peek().type, PrecedenceType.P_LOWEST)

    def __next_token(self) -> None:
        self.cur_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def __peek_token_is(self, tt: TokenType) -> bool:
        return self.peek_token is not None and self.peek_token.type == tt

    def __cur_token_is(self, tt: TokenType) -> bool:
        return self.cur_token is not None and self.cur_token.type == tt

    def __expect_peek(self, tt: TokenType) -> bool:
        if self.__peek_token_is(tt):
            self.__next_token()
            return True

        self.__peek_error(tt)
        return False

    def __expect_cur(self, tt: TokenType) -> bool:
        if self.__cur_token_is(tt):
            self.__next_token()
            return True

        self.__cur_error(tt)
        return False

    def __peek_error(self, tt: TokenType):
        self.errors.append(
            f"Expected next token to be {tt} but got {self.peek_token} instead."
        )

    def __cur_error(self, tt: TokenType):
        self.errors.append(
            f"Expected current token to be {tt} but got {self.cur_token} instead."
        )

    def __no_nud_parse_fn_error(self, tt: TokenType):
        self.errors.append(f"Unexpected token '{tt}' at ${self.cur_token}")

    def __is_at_eof(self) -> bool:
        return self.cur_token is None or self.cur_token.type == TokenType.EOF

    def __recover(self) -> None:
        """skip tokens until a statement boundary (SEMICOLON) or EOF,
        so one bad statement doesn't cascade into a pile of bogus errors."""
        while not self.__cur_token_is(TokenType.SEMICOLON) and not self.__is_at_eof():
            self.__next_token()

    # endregion
