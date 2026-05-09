from typing import List, Set, FrozenSet
from .dfa import DFA

def build_dfa_from_strings(strings: List[str]) -> DFA:
    """
    Builds a deterministic Trie (which is a DFA) from a list of strings.
    """
    alphabet: Set[str] = set()
    for s in strings:
        for c in s:
            alphabet.add(c)
    
                             
                      
    transitions = {}
    accept_states = set()
    
    state_counter = 0
    
                          
    trie = {0: {}}
    
    for s in strings:
        if s == "ε" or s == "":
            accept_states.add(0)
            continue
            
        current = 0
        for char in s:
            if char not in trie[current]:
                state_counter += 1
                trie[current][char] = state_counter
                trie[state_counter] = {}
            current = trie[current][char]
        accept_states.add(current)
        
                           
    dfa_transitions = {}
    for st, edges in trie.items():
        st_f = frozenset([st])
        for char, nxt in edges.items():
            dfa_transitions[(st_f, char)] = frozenset([nxt])
            
    dfa_accept = {frozenset([a]) for a in accept_states}
    state_labels = {frozenset([s]): f"q{s}" for s in trie.keys()}
    
    return DFA(
        start=frozenset([0]),
        accept_states=dfa_accept,
        transitions=dfa_transitions,
        alphabet=alphabet,
        state_labels=state_labels
    )
