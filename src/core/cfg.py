from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Set, Tuple

from .dfa import DFA


@dataclass
class CFG:
    start_symbol: str
    rules: Dict[str, List[str]] = field(default_factory=dict)
    alphabet: Set[str] = field(default_factory=set)

    def add_rule(self, nt: str, production: str) -> None:
        self.rules.setdefault(nt, []).append(production)

    def rules_text(self) -> str:
        lines = []
        for nt in self._sorted_nts():
            prods = self.rules[nt]
            rhs = " | ".join(prods)
            lines.append(f"{nt} → {rhs}")
        return "\n".join(lines)

    def rules_list(self) -> List[dict]:
        return [
            {"non_terminal": nt, "productions": self.rules[nt]}
            for nt in self._sorted_nts()
        ]

    def _sorted_nts(self) -> List[str]:
        nts = sorted(self.rules.keys())
        if self.start_symbol in nts:
            nts.remove(self.start_symbol)
            nts = [self.start_symbol] + nts
        return nts

    def summary(self) -> str:
        total = sum(len(v) for v in self.rules.values())
        return (
            f"Non-terminals: {len(self.rules)}  |  "
            f"Productions: {total}  |  "
            f"Alphabet: {{{', '.join(sorted(self.alphabet))}}}"
        )


def build_cfg(dfa: DFA) -> CFG:
    alphabet = sorted(dfa.alphabet)

    sorted_states = sorted(list(dfa.states), key=lambda s: dfa.label(s))
    state_to_letter = {}
    letters = [chr(i) for i in range(ord('A'), ord('Z')+1) if chr(i) != 'S']
    letter_idx = 0
    
    state_to_letter[dfa.start] = "S"
    for s in sorted_states:
        if s != dfa.start:
            if letter_idx < len(letters):
                state_to_letter[s] = letters[letter_idx]
                letter_idx += 1
            else:
                state_to_letter[s] = f"N_{dfa.label(s)}"

    def nt(state: FrozenSet[int]) -> str:
        return state_to_letter[state]

    cfg = CFG(
        start_symbol=nt(dfa.start),
        alphabet=set(alphabet),
    )

    for s in dfa.states:
        for sym in alphabet:
            nxt = dfa.transitions.get((s, sym))
            if nxt is not None:
                cfg.add_rule(nt(s), f"{sym}{nt(nxt)}")

        if s in dfa.accept_states:
            cfg.add_rule(nt(s), "Λ")

        if nt(s) not in cfg.rules:
            cfg.rules[nt(s)] = []

    return cfg