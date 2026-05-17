from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple
import graphviz

from .parser import (
    Node, LetterNode, EpsilonNode, EmptyNode,
    StarNode, ConcatNode, UnionNode,
)

EPSILON = "Λ"

_counter = 0


def _new_state() -> int:
    global _counter
    _counter += 1
    return _counter


def _reset_counter(start: int = 0) -> None:
    global _counter
    _counter = start


@dataclass
class NFAFragment:
    start: int
    accept: int
    transitions: Dict[Tuple[int, str], Set[int]] = field(default_factory=dict)

    def add(self, frm: int, sym: str, to: int) -> None:
        key = (frm, sym)
        self.transitions.setdefault(key, set()).add(to)

    def merge(self, other: "NFAFragment") -> None:
        for (frm, sym), tos in other.transitions.items():
            self.transitions.setdefault((frm, sym), set()).update(tos)


class NFA:

    def __init__(self, fragment: NFAFragment, alphabet: Set[str]):
        self.start: int = fragment.start
        self.accept: int = fragment.accept
        self.transitions: Dict[Tuple[int, str], Set[int]] = fragment.transitions
        self.alphabet: Set[str] = alphabet
        self.states: Set[int] = {self.start, self.accept}
        for (frm, _), tos in self.transitions.items():
            self.states.add(frm)
            self.states.update(tos)
            
    def epsilon_closure(self, states: FrozenSet[int]) -> FrozenSet[int]:
        visited: Set[int] = set(states)
        stack = list(states)
        while stack:
            s = stack.pop()
            for nxt in self.transitions.get((s, EPSILON), set()):
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append(nxt)
        return frozenset(visited)

    def move(self, states: FrozenSet[int], symbol: str) -> FrozenSet[int]:
        result: Set[int] = set()
        for s in states:
            result.update(self.transitions.get((s, symbol), set()))
        return frozenset(result)

    def transition_table(self) -> List[dict]:
        rows = []
        symbols = sorted(self.alphabet) + [EPSILON]
        for state in sorted(self.states):
            row = {
                "state": state,
                "is_start": state == self.start,
                "is_accept": state == self.accept
            }
            for sym in symbols:
                nexts = sorted(self.transitions.get((state, sym), set()))
                row[sym] = nexts
            rows.append(row)
        return rows

    def transition_table_compact(self) -> Tuple[List[int], List[str], Dict]:
        states = sorted(self.states)
        symbols = sorted(self.alphabet) + [EPSILON]
        table: Dict = {}
        for s in states:
            for sym in symbols:
                table[(s, sym)] = sorted(self.transitions.get((s, sym), set()))
        return states, symbols, table

    def render_graphviz(self, output_path: str = "/tmp/nfa") -> str:
        dot = graphviz.Digraph(
            name="NFA",
            graph_attr={
                "rankdir": "LR",
                "bgcolor": "#FFFFFF",
                "fontcolor": "#111111",
                "pad": "0.4",
                "nodesep": "0.55",
                "ranksep": "0.7",
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

        for s in sorted(self.states):
            is_start = (s == self.start)
            is_accept = (s == self.accept)

            if is_start and is_accept:
                display_lbl = f"±{s}"
            elif is_start:
                display_lbl = f"-{s}"
            elif is_accept:
                display_lbl = f"+{s}"
            else:
                display_lbl = str(s)

            if is_start and is_accept:
                dot.node(str(s), display_lbl, shape="circle",
                         fillcolor="#FFE000", penwidth="3")
            elif is_start:
                dot.node(str(s), display_lbl, shape="circle",
                         fillcolor="#FFE000", fontcolor="#111111", penwidth="3")
            elif is_accept:
                dot.node(str(s), display_lbl, shape="circle",
                         fillcolor="#00E5CC", fontcolor="#111111")
            else:
                dot.node(str(s), display_lbl, shape="circle",
                         fillcolor="#F5F0E8", fontcolor="#111111")

        edge_labels: Dict[Tuple[int, int], List[str]] = {}
        for (frm, sym), tos in self.transitions.items():
            for to in tos:
                edge_labels.setdefault((frm, to), []).append(sym)

        for (frm, to), syms in edge_labels.items():
            label = ", ".join(sorted(syms))
            dot.edge(str(frm), str(to), label=label)

        dot.render(output_path, format="png", cleanup=True)
        return output_path + ".png"

def _thompson(node: Node) -> Tuple[NFAFragment, Set[str]]:
    if isinstance(node, EpsilonNode):
        s, a = _new_state(), _new_state()
        frag = NFAFragment(s, a)
        frag.add(s, EPSILON, a)
        return frag, set()

    if isinstance(node, EmptyNode):
        s, a = _new_state(), _new_state()
        frag = NFAFragment(s, a)
        return frag, set()

    if isinstance(node, LetterNode):
        s, a = _new_state(), _new_state()
        frag = NFAFragment(s, a)
        frag.add(s, node.value, a)
        return frag, {node.value}

    if isinstance(node, StarNode):
        inner, alpha = _thompson(node.child)
        s, a = _new_state(), _new_state()
        frag = NFAFragment(s, a)
        frag.merge(inner)
        frag.add(s, EPSILON, inner.start)
        frag.add(inner.accept, EPSILON, inner.start)
        frag.add(inner.accept, EPSILON, a)
        frag.add(s, EPSILON, a)
        return frag, alpha

    if isinstance(node, ConcatNode):
        left, a1 = _thompson(node.left)
        right, a2 = _thompson(node.right)
        frag = NFAFragment(left.start, right.accept)
        frag.merge(left)
        frag.merge(right)
        frag.add(left.accept, EPSILON, right.start)
        return frag, a1 | a2

    if isinstance(node, UnionNode):
        left, a1 = _thompson(node.left)
        right, a2 = _thompson(node.right)
        s, a = _new_state(), _new_state()
        frag = NFAFragment(s, a)
        frag.merge(left)
        frag.merge(right)
        frag.add(s, EPSILON, left.start)
        frag.add(s, EPSILON, right.start)
        frag.add(left.accept, EPSILON, a)
        frag.add(right.accept, EPSILON, a)
        return frag, a1 | a2

    raise TypeError(f"Unknown AST node type: {type(node)}")


def build_nfa(ast_node: Node, reset: bool = True) -> NFA:
    if reset:
        _reset_counter(0)
    fragment, alphabet = _thompson(ast_node)
    return NFA(fragment, alphabet)