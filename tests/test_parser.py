from src.core.preprocessor import expand
from src.core.tokenizer import tokenize
from src.core.parser import parse, UnionNode, ConcatNode, StarNode, LetterNode

def test_letter_node():
    tree = parse(tokenize("a"))
    assert isinstance(tree, LetterNode)
    assert tree.value == "a"

def test_union_node():
    tree = parse(tokenize("a+b"))
    assert isinstance(tree, UnionNode)

def test_concat_node():
    tree = parse(tokenize("ab"))
    assert isinstance(tree, ConcatNode)

def test_star_node():
    tree = parse(tokenize("a*"))
    assert isinstance(tree, StarNode)

def test_complex_tree():
    expr = expand("(a+b)*")
    tree = parse(tokenize(expr))
    assert isinstance(tree, StarNode)