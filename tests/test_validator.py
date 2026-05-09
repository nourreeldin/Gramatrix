import pytest
from src.core.validator import validate_expanded
from src.core.preprocessor import PreprocessorError

def test_valid_expression():
    validate_expanded("a+b")

def test_empty_group_error():
    with pytest.raises(PreprocessorError):
        validate_expanded("()")

def test_unmatched_paren_open():
    with pytest.raises(PreprocessorError):
        validate_expanded("(a+b")

def test_unmatched_paren_close():
    with pytest.raises(PreprocessorError):
        validate_expanded("a+b)")

def test_consecutive_plus():
    with pytest.raises(PreprocessorError):
        validate_expanded("a++b")

def test_plus_at_start():
    with pytest.raises(PreprocessorError):
        validate_expanded("+ab")

def test_plus_at_end():
    with pytest.raises(PreprocessorError):
        validate_expanded("ab+")