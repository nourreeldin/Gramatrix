from __future__ import annotations
import random
from collections import deque
from typing import FrozenSet, List, Optional, Set, Tuple

from .dfa import DFA

MAX_LEN = 30


def generate_strings(dfa: DFA, max_len: int = MAX_LEN, count: int = 5) -> List[str]:
    if not dfa.states:
        return []

    alphabet = sorted(dfa.alphabet)
    results: List[str] = []

    live_states: Set[FrozenSet[int]] = set(dfa.accept_states)
    changed = True
    while changed:
        changed = False
        for (frm, sym), to in dfa.transitions.items():
            if to in live_states and frm not in live_states:
                live_states.add(frm)
                changed = True

    if dfa.start not in live_states:
        return []

    queue: deque[Tuple[FrozenSet[int], str]] = deque()
    queue.append((dfa.start, ""))
    visited: Set[Tuple[FrozenSet[int], str]] = set()
    visited.add((dfa.start, ""))

    while queue and len(results) < count:
        state, path = queue.popleft()

        if state in dfa.accept_states:
            results.append(path if path else "ε")

        if len(path) >= max_len:
            continue

        for sym in alphabet:
            nxt = dfa.transitions.get((state, sym))
            if nxt is not None and nxt in live_states:
                new_path = path + sym
                key = (nxt, new_path)
                if key not in visited:
                    visited.add(key)
                    queue.append((nxt, new_path))

    return results


def generate_random_strings(
    dfa: DFA,
    max_len: int = MAX_LEN,
    count: int = 5,
    seed: Optional[int] = None,
) -> List[str]:
    if seed is not None:
        random.seed(seed)

    alphabet = sorted(dfa.alphabet)
    if not alphabet:
        return []

    live_states: Set[FrozenSet[int]] = set(dfa.accept_states)
    changed = True
    while changed:
        changed = False
        for (frm, sym), to in dfa.transitions.items():
            if to in live_states and frm not in live_states:
                live_states.add(frm)
                changed = True

    if dfa.start not in live_states:
        return []

    collected: List[str] = []
    seen: Set[str] = set()
    max_attempts = max(count * 8, 40)

    for _ in range(max_attempts):
        if len(collected) >= count:
            break

        state = dfa.start
        path: List[str] = []
        path_len = random.randint(0, max_len)

        for _ in range(path_len):
            shuffled = alphabet[:]
            random.shuffle(shuffled)
            moved = False
            for sym in shuffled:
                nxt = dfa.transitions.get((state, sym))
                if nxt is not None and nxt in live_states:
                    path.append(sym)
                    state = nxt
                    moved = True
                    break
            if not moved:
                break

        if state in dfa.accept_states:
            s = "".join(path) if path else "ε"
            if s not in seen:
                seen.add(s)
                collected.append(s)

    if len(collected) < count:
        bfs = generate_strings(dfa, max_len, count * 2)
        for s in bfs:
            if s not in seen and len(collected) < count:
                seen.add(s)
                collected.append(s)

    return collected[:count]