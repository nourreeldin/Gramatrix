from __future__ import annotations
from typing import Dict, FrozenSet, List, Optional, Set, Tuple
from .dfa import DFA

def build_dfa_from_table(
    states: List[str],
    alphabet: List[str],
    transitions: Dict[Tuple[str, str], str],
    start: str,
    accept_states: Set[str],
) -> DFA:
    """Build a DFA object from a user-supplied transition table."""
    idx: Dict[str, FrozenSet[int]] = {n: frozenset({i}) for i, n in enumerate(states)}
    state_labels: Dict[FrozenSet[int], str] = {v: k for k, v in idx.items()}

    dead_needed = any((n, s) not in transitions for n in states for s in alphabet)
    dead_key: Optional[FrozenSet[int]] = None
    if dead_needed:
        dead_key = frozenset({len(states)})
        state_labels[dead_key] = "trap"

    new_t: Dict[Tuple[FrozenSet[int], str], FrozenSet[int]] = {}
    for name in states:
        src = idx[name]
        for sym in alphabet:
            dst_name = transitions.get((name, sym))
            if dst_name is not None and dst_name in idx:
                new_t[(src, sym)] = idx[dst_name]
            elif dead_key is not None:
                new_t[(src, sym)] = dead_key

    if dead_key is not None:
        for sym in alphabet:
            new_t[(dead_key, sym)] = dead_key

    return DFA(
        start=idx[start],
        accept_states={idx[s] for s in accept_states if s in idx},
        transitions=new_t,
        alphabet=set(alphabet),
        state_labels=state_labels,
    )
