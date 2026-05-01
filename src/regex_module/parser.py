from __future__ import annotations
from typing import List
from dataclasses import dataclass, field
from .tokenizer import Token
from .preprocessor import PreprocessorError

@dataclass
class LetterNode:
    value: str
    def __repr__(self): return f"Letter({self.value!r})"

@dataclass
class EpsilonNode:
    def __repr__(self): return "Epsilon"

@dataclass
class EmptyNode:
    def __repr__(self): return "Empty(Φ)"

@dataclass
class StarNode:
    child: object
    def __repr__(self): return f"Star({self.child!r})"

@dataclass
class ConcatNode:
    left: object
    right: object
    def __repr__(self): return f"Concat({self.left!r}, {self.right!r})"

@dataclass
class UnionNode:
    left: object
    right: object
    def __repr__(self): return f"Union({self.left!r}, {self.right!r})"

Node = LetterNode | EpsilonNode | EmptyNode | StarNode | ConcatNode | UnionNode


class _Parser:
    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Token | None:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _consume(self, kind: str) -> Token:
        tok = self._peek()
        if tok is None or tok.kind != kind:
            raise PreprocessorError(
                f"Expected {kind} but got {tok!r} at position {self._pos}."
            )
        self._pos += 1
        return tok

    def _at_end(self) -> bool:
        return self._pos >= len(self._tokens)

    def parse(self) -> Node:
        node = self._regex()
        if not self._at_end():
            raise PreprocessorError(
                f"Unexpected token {self._peek()!r} at position {self._pos}."
            )
        return node

    def _regex(self) -> Node:
        return self._union()

    def _union(self) -> Node:
        left = self._concat()
        while self._peek() and self._peek().kind == "UNION":
            self._pos += 1  
            right = self._concat()
            left = UnionNode(left, right)
        return left

    def _concat(self) -> Node:
        node = self._star()
        while (self._peek() and
               self._peek().kind not in ("UNION", "RPAREN")):
            right = self._star()
            node = ConcatNode(node, right)
        return node

    def _star(self) -> Node:
        node = self._atom()
        while self._peek() and self._peek().kind == "STAR":
            self._pos += 1  
            node = StarNode(node)
        return node

    def _atom(self) -> Node:
        tok = self._peek()
        if tok is None:
            raise PreprocessorError("Unexpected end of expression.")

        if tok.kind == "LETTER":
            self._pos += 1
            if tok.value == "Λ":
                return EpsilonNode()
            if tok.value in ("Φ", "∅"):
                return EmptyNode()
            return LetterNode(tok.value)

        if tok.kind == "LPAREN":
            self._pos += 1         
            node = self._regex()
            self._consume("RPAREN") 
            return node

        raise PreprocessorError(
            f"Unexpected token {tok!r} at position {self._pos}."
        )

def parse(tokens: List[Token]) -> Node:
    if not tokens:
        return EpsilonNode()
    return _Parser(tokens).parse()