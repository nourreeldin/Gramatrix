from src.regex_module.preprocessor import expand
from src.regex_module.validator import validate_expanded
from src.regex_module.tokenizer import tokenize
from src.regex_module.parser import parse

def test_full_pipeline():
    expr = "a+b^2"

    expanded = expand(expr)
    validate_expanded(expanded)
    tokens = tokenize(expanded)
    tree = parse(tokens)

    assert tree is not None