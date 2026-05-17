from __future__ import annotations
from typing import Set, Dict, Tuple, List
from .nfa import NFA, NFAFragment, _reset_counter, _new_state

class CFGParseError(Exception):
    pass

def parse_cfg(cfg_text: str) -> NFA:
    """
    Parses a Context-Free Grammar into an NFA using a regular over-approximation.
    Expected format:
    S → a S a | b A | Λ
    A → a
    """
    lines = [line.strip() for line in cfg_text.split('\n') if line.strip()]
    if not lines:
        raise CFGParseError("CFG is empty.")

    rules: Dict[str, List[str]] = {}
    first_nt = None

    for line in lines:
        if '→' not in line:
            raise CFGParseError(f"Missing '→' in rule: {line}")
        
        left, right = line.split('→', 1)
        left = left.strip()
        if len(left) != 1 or not left.isupper():
            raise CFGParseError(f"Left side must be a single non-terminal (A-Z). Found: '{left}'")
        
        if first_nt is None:
            first_nt = left
            
        prods = [p.strip() for p in right.split('|')]
        rules.setdefault(left, []).extend(prods)

    # Parity-preserving heuristic for S -> u S u | Λ (like S -> aSa | Λ)
    for nt, prods in rules.items():
        is_candidate = True
        has_lambda = False
        symmetric = []
        for p in prods:
            p_clean = p.replace(' ', '')
            if p_clean in ("Λ", "e", "epsilon", "E"):
                has_lambda = True
            else:
                parts = p_clean.split(nt)
                if len(parts) == 2 and parts[0] == parts[1] and parts[0].islower() and len(parts[0]) > 0:
                    symmetric.append(parts[0])
                else:
                    is_candidate = False
                    break
        
        if is_candidate and has_lambda and symmetric:
            rewritten = []
            for p in prods:
                p_clean = p.replace(' ', '')
                if p_clean in ("Λ", "e", "epsilon", "E"):
                    rewritten.append(p)
                else:
                    parts = p_clean.split(nt)
                    rewritten.append(f"{parts[0]}{parts[0]}{nt}")
            rules[nt] = rewritten

    _reset_counter(0)
    
    nt_start: Dict[str, int] = {}
    nt_accept: Dict[str, int] = {}
    
    for nt in rules.keys():
        nt_start[nt] = _new_state()
        nt_accept[nt] = _new_state()

    alphabet: Set[str] = set()
    frag = NFAFragment(start=nt_start[first_nt], accept=nt_accept[first_nt])

    for nt, prods in rules.items():
        for prod_raw in prods:
            prod = prod_raw.replace(' ', '')
            if prod in ("Λ", "e", "epsilon", "E"):
                frag.add(nt_start[nt], "Λ", nt_accept[nt])
            else:
                curr = nt_start[nt]
                for i, sym in enumerate(prod):
                    is_last = (i == len(prod) - 1)
                    next_s = nt_accept[nt] if is_last else _new_state()
                    
                    if sym.isupper():
                        if sym not in nt_start:
                            nt_start[sym] = _new_state()
                            nt_accept[sym] = _new_state()
                        frag.add(curr, "Λ", nt_start[sym])
                        frag.add(nt_accept[sym], "Λ", next_s)
                    else:
                        if sym not in ('Λ', 'e', 'epsilon', 'E'):
                            alphabet.add(sym)
                            frag.add(curr, sym, next_s)
                        else:
                            frag.add(curr, "Λ", next_s)
                            
                    curr = next_s

    return NFA(frag, alphabet)
