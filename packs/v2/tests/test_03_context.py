import pytest
from practice.models import Chunk, Citation, Context
from practice.round03_context import build_context


def chunk(doc="d1", key="c1", text="one two", *, tenant="a", public=True, allowed=()):
    return Chunk(tenant, doc, key, text, frozenset(allowed), public)


def build(data, budget=20, cap=2):
    return build_context(data, tenant_id="a", user_id="alice", word_budget=budget, max_per_document=cap)


def test_context_empty_and_zero_budget():
    assert build([]) == Context("", (), 0)
    assert build([chunk()], budget=0) == Context("", (), 0)


def test_context_exact_budget_and_citation_mapping():
    data = [chunk(text="one two"), chunk(doc="d2", text="three four")]
    assert build(data, budget=4) == Context("[1] one two\n[2] three four",
        (Citation("[1]", "d1", "c1"), Citation("[2]", "d2", "c1")), 4)


def test_context_skip_large_chunk_then_try_smaller():
    data = [chunk(text="this is too large"), chunk(doc="d2", text="fits now")]
    assert build(data, budget=2) == Context("[1] fits now", (Citation("[1]", "d2", "c1"),), 2)


def test_context_normalizes_whitespace_and_skips_empty():
    data = [chunk(text=" \t"), chunk(key="c2", text="  one\n two \tthree ")]
    assert build(data).text == "[1] one two three"
    assert build(data).words_used == 3


def test_context_same_chunk_once_but_distinct_chunks_kept():
    a, b = chunk(), chunk(key="c2", text="three")
    result = build([a, a, b])
    assert result.text == "[1] one two\n[2] three"
    assert result.words_used == 3


def test_context_cap_per_document_not_per_chunk_id():
    data = [chunk(key="c1"), chunk(key="c2"), chunk(doc="d2", key="c1")]
    result = build(data, cap=1)
    assert [(c.document_id, c.chunk_id) for c in result.citations] == [("d1", "c1"), ("d2", "c1")]


def test_context_permissions_filter_before_counting():
    data = [chunk(text="secret", public=False), chunk(text="visible", allowed=("alice",), public=False),
            chunk(doc="d2", text="foreign", tenant="b"), chunk(doc="d2", text="local")]
    assert build(data, budget=2).text == "[1] visible\n[2] local"


def test_context_no_leak_of_denied_content_or_citation_ids():
    result = build([chunk(doc="secret-id", text="SECRET", public=False), chunk(doc="safe", text="ok")])
    assert result == Context("[1] ok", (Citation("[1]", "safe", "c1"),), 1)


def test_context_first_visible_nonempty_duplicate_wins_even_if_too_large():
    data = [chunk(text="this cannot fit"), chunk(text="fits"), chunk(doc="d2", text="yes")]
    assert build(data, budget=1).text == "[1] yes"


def test_context_empty_duplicate_does_not_hide_nonempty():
    assert build([chunk(text=" "), chunk(text="yes")]).text == "[1] yes"


def test_context_generator_preserves_rank_order_not_id_order():
    data = [chunk(doc="z", text="top"), chunk(doc="a", text="next")]
    assert build(iter(data)).text == "[1] top\n[2] next"


@pytest.mark.parametrize("budget,cap", [(-1, 2), (4, 0), (4, -1)])
def test_context_validates_before_consuming_input(budget, cap):
    def must_not_consume():
        raise AssertionError("input consumed before validation")
        yield
    with pytest.raises(ValueError):
        build(must_not_consume(), budget=budget, cap=cap)
