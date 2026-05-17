from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple
import graphviz

from .nfa import NFA, EPSILON


@dataclass
class DFA:
    start: FrozenSet[int]
    accept_states: Set[FrozenSet[int]]
    transitions: Dict[Tuple[FrozenSet[int], str], FrozenSet[int]]
    alphabet: Set[str]
    state_labels: Dict[FrozenSet[int], str]

    @property
    def states(self) -> List[FrozenSet[int]]:
        all_s: Set[FrozenSet[int]] = {self.start}
        for (s, _), t in self.transitions.items():
            all_s.add(s)
            all_s.add(t)
        return sorted(all_s, key=lambda x: self.state_labels[x])

    def label(self, state: FrozenSet[int]) -> str:
        return self.state_labels[state]

    def accepts(self, string: str) -> bool:
        current = self.start
        for ch in string:
            current = self.transitions.get((current, ch))
            if current is None:
                return False
        return current in self.accept_states

    def step_trace(self, string: str) -> List[dict]:
        steps = []
        current = self.start
        for i, ch in enumerate(string):
            nxt = self.transitions.get((current, ch))
            steps.append({
                "step": i,
                "char": ch,
                "from_state": self.label(current),
                "to_state": self.label(nxt) if nxt is not None else None,
                "dead": nxt is None,
                "accepted": False,
            })
            if nxt is None:
                break
            current = nxt
        else:
            if steps:
                steps[-1]["accepted"] = (current in self.accept_states)
            else:
                steps.append({
                    "step": 0,
                    "char": "Λ",
                    "from_state": self.label(self.start),
                    "to_state": self.label(self.start),
                    "dead": False,
                    "accepted": self.start in self.accept_states,
                })
        return steps

    def transition_table(self) -> List[dict]:
        rows = []
        symbols = sorted(self.alphabet)
        for s in self.states:
            row: dict = {
                "state": self.label(s),
                "is_start": s == self.start,
                "is_accept": s in self.accept_states,
            }
            for sym in symbols:
                nxt = self.transitions.get((s, sym))
                row[sym] = self.label(nxt) if nxt is not None else ""
            rows.append(row)
        return rows

    def render_graphviz(self, output_path: str = "/tmp/dfa",
                        highlight_state: Optional[str] = None,
                        highlight_edge: Optional[Tuple[str, str, str]] = None) -> str:
        dot = graphviz.Digraph(
            name="DFA",
            graph_attr={
                "rankdir": "LR",
                "bgcolor": "#FFFFFF",
                "pad": "0.4",
                "nodesep": "0.6",
                "ranksep": "0.8",
            },
            node_attr={
                "style": "filled,bold",
                "fontname": "Segoe UI",
                "fontsize": "18",
                "fontcolor": "#111111",
                "color": "#111111",
                "penwidth": "3.5",
            },
            edge_attr={
                "fontname": "Consolas",
                "fontsize": "16",
                "fontcolor": "#111111",
                "color": "#111111",
                "penwidth": "2.5",
            },
        )

        for s in self.states:
            lbl = self.label(s)
            is_accept = s in self.accept_states
            is_start = s == self.start
            is_hi = (lbl == highlight_state)

            if is_start and is_accept:
                display_lbl = f"±{lbl}"
            elif is_start:
                display_lbl = f"-{lbl}"
            elif is_accept:
                display_lbl = f"+{lbl}"
            else:
                display_lbl = lbl

            if is_hi:
                fill = "#FF2020"
                fc = "#FFFFFF"
            elif is_start and is_accept:
                fill = "#FFE000"
                fc = "#111111"
            elif is_start:
                fill = "#FFE000"
                fc = "#111111"
            elif is_accept:
                fill = "#00E5CC"
                fc = "#111111"
            else:
                fill = "#F5F0E8"
                fc = "#111111"

            dot.node(lbl, display_lbl, shape="circle", fillcolor=fill, fontcolor=fc,
                     penwidth="4" if is_hi else "3")

        edge_map: Dict[Tuple[str, str], List[str]] = {}
        for (s, sym), t in self.transitions.items():
            key = (self.label(s), self.label(t))
            edge_map.setdefault(key, []).append(sym)

        for (frm, to), syms in edge_map.items():
            label = ", ".join(sorted(syms))
            is_hi_edge = (
                highlight_edge is not None
                and frm == highlight_edge[0]
                and to == highlight_edge[1]
            )
            if is_hi_edge:
                dot.edge(frm, to, label=label,
                         color="#FF2020", fontcolor="#FF2020", penwidth="4")
            else:
                dot.edge(frm, to, label=label)

        dot.render(output_path, format="png", cleanup=True)
        return output_path + ".png"


def build_dfa(nfa: NFA) -> DFA:
    alphabet = sorted(nfa.alphabet)

    start_closure = nfa.epsilon_closure(frozenset({nfa.start}))

    state_labels: Dict[FrozenSet[int], str] = {}
    label_counter = [0]

    def get_label(s: FrozenSet[int]) -> str:
        if s not in state_labels:
            state_labels[s] = f"{label_counter[0]}"
            label_counter[0] += 1
        return state_labels[s]

    get_label(start_closure)

    transitions: Dict[Tuple[FrozenSet[int], str], FrozenSet[int]] = {}
    accept_states: Set[FrozenSet[int]] = set()

    worklist = [start_closure]
    visited: Set[FrozenSet[int]] = {start_closure}

    while worklist:
        current = worklist.pop(0)
        if nfa.accept in current:
            accept_states.add(current)

        for sym in alphabet:
            moved = nfa.move(current, sym)
            closure = nfa.epsilon_closure(moved) if moved else frozenset()
            
            transitions[(current, sym)] = closure
            get_label(closure)
            if closure not in visited:
                visited.add(closure)
                worklist.append(closure)

    return DFA(
        start=start_closure,
        accept_states=accept_states,
        transitions=transitions,
        alphabet=set(alphabet),
        state_labels=state_labels,
    )