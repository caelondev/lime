from enum import Enum
from typing import Any


class TokenType(Enum):
    # Special tokens
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"

    # Data types
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
    SEMICOLON = "SEMICOLON"
    LEFT_PARENTHESIS = "LEFT_PARENTHESIS"
    RIGHT_PARENTHESIS = "RIGHT_PARENTHESIS"


class Token:
    def __init__(self, type: TokenType, literal: Any, ln_number: int, pos: int):
        self.type = type
        self.literal = literal
        self.ln_number = ln_number
        self.pos = pos

    def __str__(self):
        return f"Token[{self.type}] : {self.literal} : ln {self.ln_number} : pos {self.pos}"

    def __repr__(self):
        return str(self)
