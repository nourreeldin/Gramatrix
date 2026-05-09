import re
from typing import List, Optional

class EnglishParseError(Exception):
    pass

def _sigma_star(alphabet: List[str]) -> str:
    if not alphabet:
        return ""
    if len(alphabet) == 1:
        return f"{alphabet[0]}*"
    return f"({'+'.join(alphabet)})*"

def _sigma_minus(alphabet: List[str], exclude: str) -> str:
    sub = [c for c in alphabet if c != exclude]
    if not sub:
        return ""
    if len(sub) == 1:
        return sub[0]
    return f"({'+'.join(sub)})"

def _sigma_minus_star(alphabet: List[str], exclude: str) -> str:
    s = _sigma_minus(alphabet, exclude)
    if not s:
        return ""
    if len(s) == 1:
        return f"{s}*"
    return f"{s}*"

def parse_english_to_regex(phrase: str, alphabet: List[str]) -> str:
    phrase = phrase.lower().strip()
                      
    phrase = re.sub(r'\s+', ' ', phrase)
    
    if not alphabet:
        alphabet = ['a', 'b']
        
    sig_star = _sigma_star(alphabet)
    
                                      
    m = re.match(r'^starts with\s+([a-z0-9]+)\s+and ends with\s+([a-z0-9]+)$', phrase)
    if m:
        return f"{m.group(1)}{sig_star}{m.group(2)}"
        
                      
    m = re.match(r'^starts with\s+([a-z0-9]+)$', phrase)
    if m:
        return f"{m.group(1)}{sig_star}"
        
                    
    m = re.match(r'^ends with\s+([a-z0-9]+)$', phrase)
    if m:
        return f"{sig_star}{m.group(1)}"
        
                             
    m = re.match(r'^contains exactly (\d+) ([a-z0-9])(?:[\'s]*)?$', phrase)
    if m:
        n = int(m.group(1))
        char = m.group(2)
        if char not in alphabet:
            raise EnglishParseError(f"Character '{char}' not in alphabet.")
        other_star = _sigma_minus_star(alphabet, char)
        parts = [other_star]
        for _ in range(n):
            parts.append(char)
            parts.append(other_star)
        return "".join(parts)
        
                              
    m = re.match(r'^contains at least (\d+) ([a-z0-9])(?:[\'s]*)?$', phrase)
    if m:
        n = int(m.group(1))
        char = m.group(2)
        if char not in alphabet:
            raise EnglishParseError(f"Character '{char}' not in alphabet.")
        parts = [sig_star]
        for _ in range(n):
            parts.append(char)
            parts.append(sig_star)
        return "".join(parts)

                   
    m = re.match(r'^contains\s+([a-z0-9]+)$', phrase)
    if m:
        return f"{sig_star}{m.group(1)}{sig_star}"
        
                           
    m = re.match(r'^does not contain\s+([a-z0-9]+)$', phrase)
    if m:
        char = m.group(1)
        if len(char) == 1:
            if char not in alphabet:
                raise EnglishParseError(f"Character '{char}' not in alphabet.")
            return _sigma_minus_star(alphabet, char)
        else:
            raise EnglishParseError("Multi-character 'does not contain' is too complex for basic parser.")

                     
    if phrase in ["empty", "empty string", "epsilon", "ε"]:
        return "ε"
        
                    
    if phrase in ["all strings", "everything", "any string"]:
        return sig_star
        
    raise EnglishParseError("Could not parse phrase. Try formats like 'starts with a', 'contains exactly 2 b', 'ends with ab', 'does not contain a'.")
