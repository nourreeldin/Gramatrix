from __future__ import annotations
from typing import Dict, FrozenSet, List, Set, Tuple, Optional

from .dfa import DFA


def minimize_dfa(dfa: DFA) -> DFA:
    alphabet = sorted(dfa.alphabet)
    all_states = frozenset(dfa.states)

    if not all_states:
        return dfa

    accept = frozenset(dfa.accept_states)
    non_accept = all_states - accept

    reachable = _reachable_states(dfa)
    accept = accept & reachable
    non_accept = non_accept & reachable

    partitions: List[FrozenSet[FrozenSet[int]]] = []
    if accept:
        partitions.append(accept)
    if non_accept:
        partitions.append(non_accept)

    if not partitions:
        return dfa

    worklist = set(range(len(partitions)))

    def state_to_part(state: FrozenSet[int]) -> int:
        for i, p in enumerate(partitions):
            if state in p:
                return i
        return -1

    changed = True
    while changed:
        changed = False
        new_partitions: List[FrozenSet[FrozenSet[int]]] = []
        for group in partitions:
            if len(group) <= 1:
                new_partitions.append(group)
                continue

            split = _split_group(group, alphabet, dfa, partitions)
            if len(split) > 1:
                changed = True
                new_partitions.extend(split)
            else:
                new_partitions.append(group)
        partitions = new_partitions

    representatives: Dict[int, FrozenSet[int]] = {} 
    part_map: Dict[FrozenSet[int], int] = {}  

    for i, group in enumerate(partitions):
        for s in group:
            part_map[s] = i
        representatives[i] = min(group, key=lambda s: dfa.label(s))

    start_part = part_map.get(dfa.start)
    if start_part is None:
        return dfa

    new_transitions: Dict[Tuple[FrozenSet[int], str], FrozenSet[int]] = {}
    new_accept: Set[FrozenSet[int]] = set()
    new_state_labels: Dict[FrozenSet[int], str] = {}
    new_start: Optional[FrozenSet[int]] = None
    sorted_parts = sorted(
        range(len(partitions)),
        key=lambda i: dfa.label(representatives[i])
    )
    label_map: Dict[int, str] = {}
    label_idx = 0
    for pi in sorted_parts:
        label_map[pi] = f"{label_idx}"
        label_idx += 1

    for pi in range(len(partitions)):
        rep = representatives[pi]
        new_state = frozenset({pi})
        new_state_labels[new_state] = label_map[pi]

        if pi == start_part:
            new_start = new_state
        if rep in dfa.accept_states:
            new_accept.add(new_state)

        for sym in alphabet:
            nxt = dfa.transitions.get((rep, sym))
            if nxt is not None:
                nxt_part = part_map.get(nxt)
                if nxt_part is not None:
                    nxt_state = frozenset({nxt_part})
                    new_transitions[(new_state, sym)] = nxt_state

    if new_start is None:
        return dfa

    return DFA(
        start=new_start,
        accept_states=new_accept,
        transitions=new_transitions,
        alphabet=dfa.alphabet,
        state_labels=new_state_labels,
    )


def _reachable_states(dfa: DFA) -> FrozenSet[FrozenSet[int]]:
    visited: Set[FrozenSet[int]] = {dfa.start}
    queue = [dfa.start]
    while queue:
        s = queue.pop(0)
        for sym in dfa.alphabet:
            nxt = dfa.transitions.get((s, sym))
            if nxt is not None and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return frozenset(visited)


def _split_group(
    group: FrozenSet[FrozenSet[int]],
    alphabet: List[str],
    dfa: DFA,
    partitions: List[FrozenSet[FrozenSet[int]]],
) -> List[FrozenSet[FrozenSet[int]]]:
    def partition_of(s: FrozenSet[int]) -> int:
        for i, p in enumerate(partitions):
            if s in p:
                return i
        return -1  

    for sym in alphabet:
        sig_map: Dict[int, List[FrozenSet[int]]] = {}
        for state in group:
            nxt = dfa.transitions.get((state, sym))
            sig = partition_of(nxt) if nxt is not None else -1
            sig_map.setdefault(sig, []).append(state)

        if len(sig_map) > 1:
            return [frozenset(v) for v in sig_map.values()]

    return [group]