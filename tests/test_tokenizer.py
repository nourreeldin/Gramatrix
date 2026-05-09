from src.core.tokenizer import tokenize

def test_simple_tokens():
    tokens = tokenize("a+b")
    assert [t.kind for t in tokens] == ["LETTER", "UNION", "LETTER"]

def test_star_token():
    tokens = tokenize("a*")
    assert [t.kind for t in tokens] == ["LETTER", "STAR"]

def test_parentheses():
    tokens = tokenize("(a+b)")
    kinds = [t.kind for t in tokens]
    assert kinds == ["LPAREN", "LETTER", "UNION", "LETTER", "RPAREN"]

def test_complex_expression():
    tokens = tokenize("(ab)*+c")
    kinds = [t.kind for t in tokens]
    assert "UNION" in kinds
    assert "STAR" in kinds