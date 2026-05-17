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
        
    sig_star = f"({'+'.join(alphabet)})*" if len(alphabet) > 1 else f"{alphabet[0]}*" if alphabet else ""
    
    def ext(m):
        return [g for g in m.groups() if g is not None]
        
    def _sigma_minus_star(exclude):
        sub = [c for c in alphabet if c != exclude]
        if not sub: return ''
        if len(sub) == 1: return f'{sub[0]}*'
        return f'({"+".join(sub)})*'

    def even_odd_intersection(m):
        p1 = ext(m)[0]
        x = ext(m)[1]
        p2 = ext(m)[2]
        y = ext(m)[3]
        E = f"({x}{x}+{y}{y}+({x}{y}+{y}{x})({x}{x}+{y}{y})*({x}{y}+{y}{x}))*"
        if p1 == "even" and p2 == "even":
            return E
        elif p1 == "even" and p2 == "odd":
            return f"({y}+{x}({x}{x}+{y}{y})*({x}{y}+{y}{x})){E}"
        elif p1 == "odd" and p2 == "even":
            return f"({x}+{y}({x}{x}+{y}{y})*({x}{y}+{y}{x})){E}"
        elif p1 == "odd" and p2 == "odd":
            return f"({x}{x}+{y}{y})*({x}{y}+{y}{x}){E}"

    def exactly_n_surrounded(m):
        num_str = ext(m)[0]
        x = ext(m)[1]
        y = ext(m)[2]
        mapping = {"one":1, "two":2, "three":3, "four":4, "five":5, "six":6, "seven":7, "eight":8, "nine":9, "ten":10}
        n = mapping.get(num_str, None)
        if n is None: n = int(num_str)
        return f"({y})*" + "".join([f"{x}({y})*" for _ in range(n)])

    def quantifier_and_quantifier(m):
        q1 = ext(m)[0]
        x = ext(m)[1]
        q2 = ext(m)[2]
        y = ext(m)[3]
        p1 = f"({x})*" if "zero" in q1 else f"{x}({x})*"
        p2 = f"({y})*" if "zero" in q2 else f"{y}({y})*"
        return p1 + p2

    RULES = [
        (r'.*even length.*', lambda m: f"(({'+'.join(alphabet)})({'+'.join(alphabet)}))*"),
        (r'.*odd length.*', lambda m: f"({'+'.join(alphabet)})(({'+'.join(alphabet)})({'+'.join(alphabet)}))*"),
        (r'.*(even|odd) number of\s+{X}.*and.*(even|odd) number of\s+{X}.*', even_odd_intersection),
        (r'.*even number of {X}.*', lambda m: (lambda c, o: f'{o}({c}{o}{c}{o})*')(ext(m)[0], _sigma_minus_star(ext(m)[0]))),
        (r'.*odd number of {X}.*', lambda m: (lambda c, o: f'{o}{c}{o}({c}{o}{c}{o})*')(ext(m)[0], _sigma_minus_star(ext(m)[0]))),
        (r'.*alternating\s+{X}.*one or more.*', lambda m: f'{ext(m)[0]}({ext(m)[0]})*'),
        (r'.*either\s+{X}.*or\s+{X}.*empty.*', lambda m: f'{ext(m)[0]}+{ext(m)[1]}+Λ'),
        (r'.*start and end with\s+{X}.*only\s+{X}.*or\s+{X}.*', lambda m: f'{ext(m)[0]}({ext(m)[1]}+{ext(m)[2]})*{ext(m)[0]}'),
        (r'.*containing only\s+{X}.*and\s+{X}.*any order.*', lambda m: f'({ext(m)[0]}+{ext(m)[1]})*'),
        (r'.*exactly (one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+{X}.*surrounded by zero or more\s+{X}.*', exactly_n_surrounded),
        (r'.*exactly two consecutive\s+{X}.*', lambda m: f'{sig_star}{ext(m)[0]}{ext(m)[0]}{sig_star}'),
        (r'.*start with any number.*{X}.*end with.*single\s+{X}.*', lambda m: f'({ext(m)[0]})*{ext(m)[1]}'),
        (r'.*start.*with\s+{X}.*followed by zero or more\s+{X}.*', lambda m: f'{ext(m)[0]}({ext(m)[1]})*'),
        (r'.*(zero or more|one or more)\s+{X}.*and.*(zero or more|one or more)\s+{X}.*', quantifier_and_quantifier),
        (r'.*one or more\s+{X}.*', lambda m: f'{ext(m)[0]}({ext(m)[0]})*'),
        (r'.*zero or more\s+{X}.*', lambda m: f'({ext(m)[0]})*')
    ]

    for pat_template, func in RULES:
        pat = pat_template.replace('{X}', r'(?:\"([a-z0-9]+)\"|\'([a-z0-9]+)\'|\b([a-z0-9])\b)')
        m = re.match(pat, phrase)
        if m:
            res = func(m)
            return re.sub(r'\(([a-z0-9])\)', r'\1', res)
            
    if phrase in ["empty", "empty string", "epsilon", "Λ"]:
        return "Λ"
    if phrase in ["all strings", "everything", "any string"]:
        return sig_star
        
    raise EnglishParseError("Could not parse phrase. Try formats like 'starts with a', 'contains exactly 2 b', 'ends with ab', 'does not contain a'.")
