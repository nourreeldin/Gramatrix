from __future__ import annotations
from typing import List, NamedTuple
from .validator import validate_expanded
from .preprocessor import PreprocessorError

class Token(NamedTuple):
    kind: str   
    value: str

def tokenize(expr: str) -> List[Token]:
    validate_expanded(expr)
    tokens: List[Token] = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch == "(":
            tokens.append(Token("LPAREN", ch))
        elif ch == ")":
            tokens.append(Token("RPAREN", ch))
        elif ch == "*":
            tokens.append(Token("STAR", ch))
        elif ch == "+":
            tokens.append(Token("UNION", ch))
        else:
            tokens.append(Token("LETTER", ch))
        i += 1
    return tokens

    