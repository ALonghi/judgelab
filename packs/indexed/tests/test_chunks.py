import pytest
from chunk_documents import chunk_documents
from models import Document


def doc(text, key="d", **kwargs):
    return Document("a", key, "Title", text, **kwargs)


def test_chunks_sizes_order_ids_and_final_short_chunk():
    chunks = list(chunk_documents([doc("one two three four five")], max_words=2))
    assert [(c.document_id, c.chunk_id, c.text) for c in chunks] == [
        ("d", "0", "one two"), ("d", "1", "three four"), ("d", "2", "five")]


def test_chunks_preserve_permissions_title_and_unicode():
    chunks = list(chunk_documents([doc(" Café!\t世界\nNEXT ", public=False,
                                      allowed_users=frozenset({"u"}))], max_words=2))
    assert [c.text for c in chunks] == ["Café! 世界", "NEXT"]
    assert all((c.tenant_id, c.title, c.public, c.allowed_users) ==
               ("a", "Title", False, frozenset({"u"})) for c in chunks)


def test_chunks_blank_input_and_ids_restart_per_document():
    assert list(chunk_documents([], max_words=2)) == []
    chunks = list(chunk_documents([doc("  ", "blank"), doc("a", "x"), doc("b", "y")], max_words=1))
    assert [(c.document_id, c.chunk_id) for c in chunks] == [("x", "0"), ("y", "0")]


@pytest.mark.parametrize("maximum", [0, -1])
def test_chunks_validate_before_consuming(maximum):
    def forbidden():
        raise AssertionError("Invalid input consumed documents")
        yield
    with pytest.raises(ValueError):
        list(chunk_documents(forbidden(), max_words=maximum))


def test_chunks_yield_before_reading_next_document():
    def source():
        yield doc("one two three")
        raise AssertionError("Prefetched next document")
    chunks = iter(chunk_documents(source(), max_words=2))
    assert next(chunks).text == "one two"
    assert next(chunks).text == "three"


def test_chunks_do_not_split_entire_body():
    class StreamingText(str):
        def split(self, *args, **kwargs):
            raise AssertionError("Whole-body split allocates all words")
    body = StreamingText("one two " * 10000)
    chunks = iter(chunk_documents([doc(body)], max_words=2))
    assert next(chunks).text == "one two"
