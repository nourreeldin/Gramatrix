from src.core.preprocessor import expand
from src.core.validator import validate_expanded
from src.core.tokenizer import tokenize
from src.core.parser import parse

def test_full_pipeline():
    expr = "a+b^2"

    expanded = expand(expr)
    validate_expanded(expanded)
    tokens = tokenize(expanded)
    tree = parse(tokens)

    assert tree is not None