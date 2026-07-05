import re

from Lexer import Lexer
from Token import Token, TokenType
from typing import Callable
from enum import Enum, auto

from AST import Statement, Expression, Program
from AST import ExpressionStatement
from AST import BinaryExpression
from AST import IntegerLiteral, FloatLiteral


class PrecedenceType(Enum):
    P_LOWEST = 0
    P_LOGICAL_OR = auto()
    P_LOGICAL_AND = auto()
    P_EQUALITY = auto()
    P_COMPARISON = auto()
    P_ADDITIVE = auto()
    P_MULTIPLICATIVE = auto()
    P_POWER = auto()
    P_UNARY = auto()
    P_CALL = auto()


PRECEDENCES: dict[TokenType, PrecedenceType] = {
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
            TokenType.LEFT_PARENTHESIS: self.__parse_grouped_expr,
        }
        self.led_fns: dict[TokenType, Callable] = {
            TokenType.PLUS: self.__parse_binary_expr,
            TokenType.MINUS: self.__parse_binary_expr,
            TokenType.ASTERISK: self.__parse_binary_expr,
            TokenType.SLASH: self.__parse_binary_expr,
            TokenType.POW: self.__parse_pow_expr,
            TokenType.MODULO: self.__parse_binary_expr,
        }

        self.__next_token()  # fill peek_token
        self.__next_token()  # fill cur_token

    def parse_program(self) -> Program:
        program: Program = Program()

        while not self.__is_at_eof():
            stmt = self.__parse_stmt()
            if stmt is not None:
                program.statements.append(stmt)
            self.__next_token()

        return program

    # region Statement Parsers
    def __parse_stmt(self) -> Statement | None:
        return self.__parse_expr_stmt()

    def __parse_expr_stmt(self) -> ExpressionStatement | None:
        expr = self.__parse_expr(PrecedenceType.P_LOWEST)

        if self.__peek_token_is(TokenType.SEMICOLON):
            self.__next_token()

        if expr is not None:
            return ExpressionStatement(expr)

        return None

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

    def __parse_int_literal(self) -> Expression | None:
        cur = self.__cur()
        try:
            value = int(cur.literal)
        except ValueError:
            self.errors.append(f"Could not parse '{cur.literal}' as an integer.")
            return None
        return IntegerLiteral(value)

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

    def __peek_error(self, tt: TokenType):
        self.errors.append(
            f"Expected next token to be {tt} but got {self.peek_token} instead."
        )

    def __no_nud_parse_fn_error(self, tt: TokenType):
        self.errors.append(f"Unexpected token '{tt}'")

    def __is_at_eof(self) -> bool:
        return self.cur_token is None or self.cur_token.type == TokenType.EOF

    # endregion
