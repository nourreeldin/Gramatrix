from __future__ import annotations
from typing import List

_LETTERS = set("abcdefghijklmnopqrstuvwxyz0123456789ΛΦ∅")
SUP_DIGIT_MAP: dict[str, str] = {
    "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4", "⁵": "^5",
    "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9",
}
SUP_REVERSE_LABEL = "ᴿ"
SUP_REVERSE_TOKEN = "^R"
SUP_POSITIVE_LABEL = "⁺"
SUP_KLEENE_LABEL = "*"

_SUP_DISPLAY: dict[str, str] = {v: k for k, v in SUP_DIGIT_MAP.items()}
_SUP_DISPLAY[SUP_REVERSE_TOKEN] = SUP_REVERSE_LABEL
_SUP_DISPLAY["^+"] = SUP_POSITIVE_LABEL


class PreprocessorError(ValueError):
    """Raised when the expression violates a syntactic rule."""


def to_display(expr: str) -> str:
    result: list[str] = []
    i = 0
    while i < len(expr):
        if expr[i] == "^" and i + 1 < len(expr):
            nxt = expr[i + 1]
            if nxt.upper() == "R":
                result.append(SUP_REVERSE_LABEL)
                i += 2
                continue
            if nxt == "+":
                result.append(SUP_POSITIVE_LABEL)
                i += 2
                continue
            if nxt.isdigit():
                result.append(_SUP_DISPLAY.get(f"^{nxt}", nxt))
                i += 2
                continue
        result.append(expr[i])
        i += 1
    return "".join(result)

def _raw_tokens(expr: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch == "(":
            depth = 0
            j = i
            while j < len(expr):
                if expr[j] == "(":
                    depth += 1
                elif expr[j] == ")":
                    depth -= 1
                    if depth == 0:
                        tokens.append(expr[i:j + 1])
                        i = j + 1
                        break
                j += 1
            else:
                tokens.append(ch)
                i += 1
            continue
        if ch == "^" and i + 1 < len(expr):
            nxt = expr[i + 1]
            if nxt.upper() == "R":
                tokens.append("^R")
                i += 2
                continue
            if nxt == "+":
                tokens.append("^+")
                i += 2
                continue
            if nxt.isdigit():
                tokens.append("^" + nxt)
                i += 2
                continue
        tokens.append(ch)
        i += 1
    return tokens


def _is_superscript(tok: str) -> bool:
    if tok == "*":
        return True
    if tok.startswith("^") and len(tok) > 1:
        rest = tok[1:]
        if rest.upper() == "R" or rest == "+" or rest.isdigit():
            return True
    return False

def _is_operand(tok: str) -> bool:
    return not _is_superscript(tok) and tok != "+"


def validate(expr: str, check_brackets: bool = True) -> None:
    if not expr:
        return

    tokens = _raw_tokens(expr)
    phi_present = any(t in ("Φ", "∅") for t in tokens)
    if phi_present:
        if len(tokens) != 1:
            raise PreprocessorError(
                "Φ/∅ must appear alone – no other symbols or superscripts allowed."
            )
        return
        
    for i, tok in enumerate(tokens):
        if _is_superscript(tok):
            if i == 0:
                raise PreprocessorError(
                    f"Superscript '{tok}' at position {i} has no preceding operand."
                )
            prev = tokens[i - 1]
            if _is_superscript(prev):
                raise PreprocessorError(
                    f"Consecutive superscripts are not allowed: "
                    f"'{prev}' followed by '{tok}'."
                )

    if check_brackets:
        stack: list[int] = []
        for idx, ch in enumerate(expr):
            if ch == "(":
                stack.append(idx)
            elif ch == ")":
                if not stack:
                    raise PreprocessorError(
                        f"Unmatched ')' at position {idx}."
                    )
                stack.pop()
        if stack:
            raise PreprocessorError(
                f"Unmatched '(' at position(s): {stack}."
            )

    for tok in tokens:
        if tok.startswith("(") and tok.endswith(")"):
            validate(tok[1:-1], check_brackets=check_brackets)

def tokenize(expr: str) -> List[str]:
    validate(expr)
    return _raw_tokens(expr)

def _has_plus(inner: str) -> bool:
    depth = 0
    for ch in inner:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "+" and depth == 0:
            return True
    return False


def _has_star(inner: str) -> bool:
    depth = 0
    for ch in inner:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "*" and depth == 0:
            return True
    return False


def _split_top_level(s: str, sep: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append(s[start:i])
            start = i + 1
    parts.append(s[start:])
    return parts


def _top_level_segments(s: str) -> list[str]:
    segments: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == "(":
            depth = 0
            j = i
            while j < len(s):
                if s[j] == "(":
                    depth += 1
                elif s[j] == ")":
                    depth -= 1
                    if depth == 0:
                        seg = s[i:j + 1]
                        if j + 1 < len(s) and s[j + 1] == "*":
                            seg += "*"
                            j += 1
                        segments.append(seg)
                        i = j + 1
                        break
                j += 1
            else:
                segments.append(s[i])
                i += 1
        elif s[i] == "+" and not (i > 0 and s[i-1] == "^"):
            segments.append(s[i])
            i += 1
        elif s[i] == "*":
            if segments:
                segments[-1] += "*"
            i += 1
        else:
            segments.append(s[i])
            i += 1
    return segments


def _structured_reverse(expanded: str) -> str:
    if _has_plus(expanded):
        parts = _split_top_level(expanded, "+")
        return "+".join(reversed(parts))

    segments = _top_level_segments(expanded)
    return "".join(reversed(segments))


def _matching_close(s: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _strip_outer_stars(s: str) -> tuple[str, int]:
    count = 0
    while s.endswith("*"):
        if len(s) >= 2 and s[-2] == ")":
            close = len(s) - 2
            depth = 0
            for i in range(close, -1, -1):
                if s[i] == ")":
                    depth += 1
                elif s[i] == "(":
                    depth -= 1
                    if depth == 0:
                        if i == 0:
                            s = s[i+1:close]
                            count += 1
                            break
                        else:
                            return s, count
            else:
                return s, count
        elif len(s) == 2 and s[0] != "(":
            s = s[0]
            count += 1
        else:
            break
    return s, count


def _collapse_stars(s: str) -> str:
    core, n = _strip_outer_stars(s)
    if n == 0:
        return s

    if len(core) == 1:
        return core + "*"
    return "(" + core + ")*"

def _wrap_if_needed(part: str, in_concat: bool) -> str:
    if in_concat and _has_plus(part):
        return "(" + part + ")"
    return part

def expand(expr: str, check_brackets: bool = True) -> str:
    validate(expr, check_brackets=check_brackets)
    if not expr:
        return ""
    return _expand_tokens(_raw_tokens(expr), check_brackets)


def _expand_tokens(tokens: List[str], check_brackets: bool = True) -> str:
    parts: list[tuple[str, bool, str]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok == "+":
            parts.append(("+", False, "+"))
            i += 1
            continue

        if _is_superscript(tok):
            if not parts:
                raise PreprocessorError("Superscript with no preceding operand.")
            prev_expanded, prev_is_group, prev_raw = parts.pop()
            result = _apply_superscript(prev_expanded, prev_is_group, prev_raw, tok)
            parts.append((result, False, ""))
            i += 1
            continue

        if tok.startswith("(") and tok.endswith(")"):
            inner = tok[1:-1]
            inner_exp = expand(inner, check_brackets=check_brackets)
            parts.append((inner_exp, True, tok))
        else:
            parts.append((tok, False, tok))

        i += 1

    non_union = [p for p in parts if p[0] != "+"]
    in_concat = len(non_union) > 1

    result_pieces: list[str] = []
    for expanded, is_group, raw_tok in parts:
        if expanded == "+":
            result_pieces.append("+")
            continue

        if is_group and _has_plus(expanded):
            result_pieces.append("(" + expanded + ")")
        elif is_group and _has_star(expanded):
            result_pieces.append("(" + expanded + ")")
        elif _has_plus(expanded) and in_concat:
            result_pieces.append("(" + expanded + ")")
        else:
            result_pieces.append(expanded)

    return "".join(result_pieces)


def _apply_superscript(expanded: str, is_group: bool, raw_tok: str, sup: str) -> str:
    inner_of_group: str | None = None
    if is_group:
        inner_of_group = raw_tok[1:-1] if (raw_tok.startswith("(") and raw_tok.endswith(")")) else None

    group_has_plus = (is_group and inner_of_group is not None and _has_plus(inner_of_group))

    expanded_has_plus = _has_plus(expanded)

    if sup == "*":
        result = _apply_star(expanded, is_group, group_has_plus, expanded_has_plus)
        return _collapse_stars(result)
    
    if sup == "^+":
        if is_group:
            if group_has_plus or expanded_has_plus:
                return f"({expanded})({expanded})*"
            else:
                inner_stripped = _maybe_strip_single_char(expanded)
                if inner_stripped is not None:
                    return f"{inner_stripped}{inner_stripped}*"
                return f"{expanded}({expanded})*"
        else:
            return f"{expanded}{expanded}*"

    if sup == "^R":
        if is_group:
            return _structured_reverse(expanded)
        else:
            return expanded[::-1]

    if sup.startswith("^") and sup[1:].isdigit():
        n = int(sup[1:])
        if n <= 0:
            raise PreprocessorError(f"Superscript must be a positive integer, got {n}.")
        if is_group:
            if group_has_plus or expanded_has_plus:
                return f"({expanded})" * n
            else:
                inner_stripped = _maybe_strip_single_char(expanded)
                if inner_stripped is not None:
                    return inner_stripped * n
                return expanded * n
        else:
            return expanded * n

    raise PreprocessorError(f"Unknown superscript token: '{sup}'.")


def _apply_star(expanded: str, is_group: bool, group_has_plus: bool,
                expanded_has_plus: bool) -> str:
    if is_group:
        inner_stripped = _maybe_strip_single_char(expanded)
        if inner_stripped is not None:
            return inner_stripped + "*"
        if group_has_plus or expanded_has_plus:
            return f"({expanded})*"
        return f"({expanded})*"
    else:
        return expanded + "*"


def _maybe_strip_single_char(expanded: str) -> str | None:
    if len(expanded) == 1 and expanded not in "()+*":
        return expanded
    return None