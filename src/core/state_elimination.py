from __future__ import annotations
from typing import Dict, List, Set, Tuple

def _needs_paren(r: str) -> bool:
    depth = 0
    for ch in r:
        if ch == "(": depth += 1
        elif ch == ")": depth -= 1
        elif ch == "+" and depth == 0: return True
    return False

def _concat(a: str, b: str) -> str:
    if a in ("", "Λ") and b in ("", "Λ"): return "Λ"
    if a in ("", "Λ"): return b
    if b in ("", "Λ"): return a
    pa = f"({a})" if _needs_paren(a) else a
    pb = f"({b})" if _needs_paren(b) else b
    return pa + pb

def _union(a: str, b: str) -> str:
    if a == b: return a
    if a in ("", "empty"): return b
    if b in ("", "empty"): return a
    return f"{a}+{b}"

def _star(a: str) -> str:
    if a in ("", "Λ", "empty"): return "Λ"
    if len(a) == 1 or (a.startswith("(") and a.endswith(")")): return f"{a}*"
    return f"({a})*"

def dfa_to_regex(states: List[str], alphabet: List[str],
                 transitions: Dict[Tuple[str, str], str],
                 start: str, accept_states: Set[str]) -> str:
    """State-elimination: DFA -> regular expression string."""
    SRC, DST = "__SRC__", "__DST__"
    gnfa: Dict[str, Dict[str, str]] = {}

    def get(s, d):
        return gnfa.get(s, {}).get(d, "empty")

    def put(s, d, lbl):
        gnfa.setdefault(s, {})[d] = lbl

    for (src, sym), dst in transitions.items():
        put(src, dst, _union(get(src, dst), sym))

    put(SRC, start, "Λ")
    for acc in accept_states:
        put(acc, DST, _union(get(acc, DST), "Λ"))

    elim = [s for s in states if s != start] + [start]
    for st in elim:
        loop = get(st, st)
        sl = _star(loop) if loop != "empty" else "Λ"
        preds = [q for q in list(gnfa) if get(q, st) != "empty" and q != st]
        succs_map = gnfa.get(st, {})
        succs = [q for q in succs_map if q != st and succs_map[q] != "empty"]
        for p in preds:
            for s in succs:
                old = get(p, s)
                part = _concat(_concat(get(p, st), sl), get(st, s))
                put(p, s, _union(old, part))
        gnfa.pop(st, None)
        for q in gnfa:
            gnfa[q].pop(st, None)

    res = get(SRC, DST)
    return "Φ" if res == "empty" else res
