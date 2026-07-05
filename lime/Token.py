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

    # Arithmetic synbols
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    SLASH = "SLASH"
    POW = "POW"
    MODULO = "MODULO"

    # Symbols
    COLON = "COLON"
    SEMICOLON = "SEMICOLON"
    LEFT_PARENTHESIS = "LEFT_PARENTHESIS"
    RIGHT_PARENTHESIS = "RIGHT_PARENTHESIS"

    # Assignment tokens
    ASSIGNMENT = "ASSIGNMENT"

    # Keywords
    LET = "LET"


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
}

TYPE_KEYWORDS: dict[str, TokenType] = {"int": TokenType.TYPE, "float": TokenType.TYPE}


def lookup_keyword(kw: str) -> TokenType:
    kw_tt = KEYWORDS.get(kw)
    if kw_tt is not None:
        return kw_tt

    kw_tt = TYPE_KEYWORDS.get(kw)
    if kw_tt is not None:
        return kw_tt

    return TokenType.IDENTIFIER
