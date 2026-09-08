"""These should pass BEFORE you implement any exercise."""
import sys
from practice.text import terms
from practice.models import Document


def test_python_version():
    assert sys.version_info >= (3, 13)


def test_provided_tokenizer():
    assert terms("Non-compete, NDA! NDA") == {"non", "compete", "nda"}


def test_provided_models_import():
    doc = Document("t", "d", 1, "title", "text")
    assert doc.allowed_users == frozenset()
    assert doc.public is False
