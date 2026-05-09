import pytest
from src.core.preprocessor import expand, PreprocessorError

def test_basic_concat():
    assert expand("ab") == "ab"

def test_union():
    assert expand("a+b") == "a+b"

def test_kleene_star():
    assert expand("a*") == "a*"

def test_positive_closure():
    assert expand("a^+") == "aa*"

def test_power_two():
    assert expand("a^2") == "aa"

def test_group_repetition():
    assert expand("(ab)^2") == "abab"

def test_group_closure():
    assert expand("(a+b)^+") == "(a+b)(a+b)*"

def test_reverse_single():
    assert expand("a^R") == "a"

def test_reverse_group():
    assert expand("(ab)^R") == "ba"

def test_nested_star_collapse():
    assert expand("((a)*)*") == "a*"

def test_invalid_superscript():
    with pytest.raises(PreprocessorError):
        expand("^R")

def test_phi_isolated():
    assert expand("Φ") == "Φ"