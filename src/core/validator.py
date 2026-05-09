from __future__ import annotations
from .preprocessor import PreprocessorError

def validate_expanded(expr: str) -> None:
    if not expr:
        return

    stack: list[int] = []

    i = 0
    while i < len(expr):
        ch = expr[i]

        if ch == "(":
            if i + 1 < len(expr) and expr[i + 1] == ")":
                raise PreprocessorError(f"Empty bracket group '()' at position {i}.")
            stack.append(i)
        elif ch == ")":
            if not stack:
                raise PreprocessorError(f"Unmatched ')' at position {i}.")
            open_pos = stack.pop()

            if expr[open_pos + 1] == "+":
                raise PreprocessorError(f"'+' immediately after '(' at position {open_pos + 1}.")
            if expr[i - 1] == "+":
                raise PreprocessorError(f"'+' immediately before ')' at position {i - 1}.")

        elif ch == "+":
            if i + 1 < len(expr) and expr[i + 1] == "+":
                raise PreprocessorError(f"Consecutive '+' operators at position {i}.")
            if i == 0:
                raise PreprocessorError("Expression cannot start with '+'.")
            if i == len(expr) - 1:
                raise PreprocessorError("Expression cannot end with '+'.")
        i += 1

    if stack:
        raise PreprocessorError(f"Unmatched '(' at position(s): {stack}.")