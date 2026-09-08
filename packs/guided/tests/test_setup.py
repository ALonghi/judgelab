import sys
from models import Document, SearchHit
from text_tools import terms


def test_python_version():
    assert sys.version_info >= (3, 13), "Use Python >=3.13 for this practice pack."


def test_tokenizer_is_provided():
    assert terms("Termination, NOTICE! notice") == {"termination", "notice"}
    assert "notice" not in terms("notices")


def test_models_are_provided():
    document = Document("firm-a", "1", 1, "Title", "Body")
    assert document.title == "Title"
    assert document.public is False
    assert SearchHit("1", "Title", 3).score == 3
