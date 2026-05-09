from __future__ import annotations
from typing import Set, Dict, Tuple, List
from .nfa import NFA, NFAFragment, _reset_counter, _new_state

class CFGParseError(Exception):
    pass

def parse_right_linear_cfg(cfg_text: str) -> NFA:
    """
    Parses a right-linear CFG into an NFA.
    Expected format:
    S → a S | b A | ε
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

    _reset_counter(0)
    
    nt_to_state: Dict[str, int] = {}
    for nt in rules.keys():
        nt_to_state[nt] = _new_state()

    accept_state = _new_state()
    alphabet: Set[str] = set()

    frag = NFAFragment(start=nt_to_state[first_nt], accept=accept_state)
    
                                                                                       
                                           
    for nt, prods in rules.items():
        src = nt_to_state[nt]
        for prod_raw in prods:
            prod = prod_raw.replace(' ', '')
            if prod == "ε":
                frag.add(src, "ε", accept_state)
            elif len(prod) == 1:
                                          
                if prod.isupper():
                    if prod not in nt_to_state:
                        nt_to_state[prod] = _new_state()
                    frag.add(src, "ε", nt_to_state[prod])
                else:
                    alphabet.add(prod)
                    frag.add(src, prod, accept_state)
            elif len(prod) == 2:
                    
                t, n = prod[0], prod[1]
                if t.isupper() or not n.isupper():
                    raise CFGParseError(f"Right-linear rules must be form 'aB'. Found: '{prod}'")
                alphabet.add(t)
                if n not in nt_to_state:
                    nt_to_state[n] = _new_state()
                frag.add(src, t, nt_to_state[n])
            else:
                raise CFGParseError(f"Rule '{prod}' is not strictly right-linear (e.g. 'aB', 'a', 'ε', 'B').")

    return NFA(frag, alphabet)
