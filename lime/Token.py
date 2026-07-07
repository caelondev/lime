from enum import Enum
from typing import Any


class TokenType(Enum):
    # Special tokens
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"
    TYPE = "TYPE"

    # Data types
    IDENTIFIER = "IDENTIFIER"
    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING"

    # Arithmetic symbols
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    SLASH = "SLASH"
    POW = "POW"
    MODULO = "MODULO"

    # Conditional symbols
    LESS = "LESS"
    GREATER = "GREATER"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER_EQUAL = "GREATER"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"

    # Symbols
    COLON = "COLON"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    ARROW = "ARROW"
    LEFT_PARENTHESIS = "LEFT_PARENTHESIS"
    RIGHT_PARENTHESIS = "RIGHT_PARENTHESIS"
    LEFT_BRACE = "LEFT_BRACE"
    RIGHT_BRACE = "RIGHT_BRACE"

    # Assignment tokens
    ASSIGNMENT = "ASSIGNMENT"

    # Keywords
    LET = "LET"
    FN = "FN"
    IF = "IF"
    ELSE = "ELSE"
    RETURN = "RETURN"
    TRUE = "TRUE"
    FALSE = "FALSE"


class Token:
    def __init__(self, type: TokenType, literal: Any, ln_number: int, pos: int):
        self.type = type
        self.literal = literal
        self.ln_number = ln_number
        self.pos = pos

    def __str__(self):
        return f"Token[{self.type}] : '{self.literal}' : ln {self.ln_number} : pos {self.pos}"

    def __repr__(self):
        return str(self)


KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}

TYPE_KEYWORDS: list[str] = [
    "int",
    "float",
    "bool",
    "string",
    "void",  # I DONT CARE ANYMORE!!! I AM **NOT**
    # IMPLEMENTING RETURN TYPES, USE THIS ANYWHERE, U MANIAC
]


def lookup_keyword(kw: str) -> TokenType:
    kw_tt = KEYWORDS.get(kw)
    if kw_tt is not None:
        return kw_tt

    if kw in TYPE_KEYWORDS:
        return TokenType.TYPE

    return TokenType.IDENTIFIER
