from __future__ import annotations
import re
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from .dfa import DFA
from .nfa import NFA


def _accepts_epsilon(dfa: DFA) -> bool:
    return dfa.start in dfa.accept_states


def _is_empty_language(dfa: DFA) -> bool:
    return len(dfa.accept_states) == 0


def _is_sigma_star(dfa: DFA) -> bool:
    return all(s in dfa.accept_states for s in dfa.states)


def _has_self_loop(dfa: DFA, sym: str) -> List[str]:
    return [
        dfa.label(s) for s in dfa.states
        if dfa.transitions.get((s, sym)) == s
    ]


def _get_fixed_length_strings(samples: List[str]) -> Optional[int]:
    real = [s for s in samples if s != "ε"]
    if not real:
        return None
    lengths = {len(s) for s in real}
    if len(lengths) == 1:
        return lengths.pop()
    return None


def _detect_repetition(dfa: DFA, alphabet: List[str]) -> Optional[str]:
    if len(alphabet) != 1:
        return None
    a = alphabet[0]
    for s in dfa.states:
        nxt = dfa.transitions.get((s, a))
        if nxt is None and s not in dfa.accept_states:
            return None
    return a


def _detect_prefix(samples: List[str]) -> Optional[str]:
    real = [s for s in samples if s != "ε" and s]
    if not real:
        return None
    prefix = real[0]
    for s in real[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
        if not prefix:
            return None
    return prefix if len(prefix) >= 1 else None


def _detect_suffix(samples: List[str]) -> Optional[str]:
    real = [s for s in samples if s != "ε" and s]
    if not real:
        return None
    suffix = real[0]
    for s in real[1:]:
        while not s.endswith(suffix):
            suffix = suffix[1:]
        if not suffix:
            return None
    return suffix if len(suffix) >= 1 else None


def _count_dfa_paths(dfa: DFA, max_depth: int = 8) -> int:
    from collections import deque
    count = 0
    queue: deque = deque([(dfa.start, 0)])
    while queue:
        state, depth = queue.popleft()
        if state in dfa.accept_states:
            count += 1
        if depth >= max_depth:
            continue
        for sym in sorted(dfa.alphabet):
            nxt = dfa.transitions.get((state, sym))
            if nxt is not None:
                queue.append((nxt, depth + 1))
    return count


def _has_cycles(dfa: DFA) -> bool:
    visited: Set[FrozenSet[int]] = set()
    rec_stack: Set[FrozenSet[int]] = set()

    def dfs(s: FrozenSet[int]) -> bool:
        visited.add(s)
        rec_stack.add(s)
        for sym in dfa.alphabet:
            nxt = dfa.transitions.get((s, sym))
            if nxt is None:
                continue
            if nxt not in visited:
                if dfs(nxt):
                    return True
            elif nxt in rec_stack:
                return True
        rec_stack.discard(s)
        return False

    for s in dfa.states:
        if s not in visited:
            if dfs(s):
                return True
    return False


def _analyse_structure(dfa: DFA, samples: List[str]) -> dict:
    alphabet = sorted(dfa.alphabet)
    eps = _accepts_epsilon(dfa)
    empty = _is_empty_language(dfa)
    sigma_star = _is_sigma_star(dfa)
    cyclic = _has_cycles(dfa)
    fixed_len = _get_fixed_length_strings(samples)
    prefix = _detect_prefix(samples)
    suffix = _detect_suffix(samples)
    repetition = _detect_repetition(dfa, alphabet)

    return {
        "alphabet": alphabet,
        "accepts_epsilon": eps,
        "is_empty": empty,
        "is_sigma_star": sigma_star,
        "has_cycles": cyclic,
        "fixed_length": fixed_len,
        "common_prefix": prefix,
        "common_suffix": suffix,
        "repetition_char": repetition,
        "num_states": len(dfa.states),
        "num_accept": len(dfa.accept_states),
        "samples": samples,
    }


def describe_language(
    dfa: DFA,
    nfa: NFA,
    sample_strings: List[str],
    original_expr: str = "",
) -> str:
    info = _analyse_structure(dfa, sample_strings)
    parts: List[str] = []

    alpha_str = "{" + ", ".join(f"'{c}'" for c in info["alphabet"]) + "}"
    alpha_name = ", ".join(f"'{c}'" for c in info["alphabet"])

    if info["is_empty"]:
        return (
            "This language is the empty language (∅). "
            "No string over any alphabet is accepted."
        )

    if info["is_sigma_star"] and len(info["alphabet"]) > 0:
        return (
            f"This language is Σ* over the alphabet {alpha_str}. "
            f"It accepts every possible string formed from {alpha_name}, "
            "including the empty string."
        )

    if info["alphabet"]:
        parts.append(
            f"This language is defined over the alphabet {alpha_str}."
        )
    else:
        parts.append("This language is defined over the empty alphabet.")

    if info["accepts_epsilon"]:
        parts.append("The empty string (ε) is accepted.")
    else:
        parts.append("The empty string (ε) is not accepted.")

    if not info["has_cycles"]:
        parts.append(
            "The language is finite — only a limited set of strings is accepted."
        )
    else:
        parts.append(
            "The language is infinite — it contains arbitrarily long strings."
        )

    if info["repetition_char"] and info["has_cycles"]:
        c = info["repetition_char"]
        eps_note = "including ε" if info["accepts_epsilon"] else "excluding ε"
        parts.append(
            f"It accepts any number of repetitions of '{c}' ({eps_note}), "
            f"i.e., strings of the form '{c}*'."
        )

    elif info["fixed_length"] is not None and not info["has_cycles"]:
        fl = info["fixed_length"]
        if fl == 0:
            parts.append("All accepted strings have length zero (ε only).")
        else:
            parts.append(
                f"All accepted strings have exactly {fl} character(s)."
            )

    else:
        if info["common_prefix"] and len(info["common_prefix"]) >= 1:
            p = info["common_prefix"]
            parts.append(
                f"Every accepted string begins with the prefix '{p}'."
            )
        if info["common_suffix"] and len(info["common_suffix"]) >= 1:
            s = info["common_suffix"]
            parts.append(
                f"Every accepted string ends with the suffix '{s}'."
            )

    ns = info["num_states"]
    na = info["num_accept"]
    parts.append(
        f"The minimized DFA has {ns} state(s), "
        f"of which {na} is/are accepting."
    )

    real_samples = [s for s in sample_strings if s]
    if real_samples:
        sample_display = ", ".join(f"'{s}'" for s in real_samples[:5])
        parts.append(f"Example strings in the language: {sample_display}.")

    if original_expr:
        parts.append(
            f"The language was specified by the regular expression: {original_expr}."
        )

    return " ".join(parts)