from dataclasses import replace
from practice.models import Document
from practice.round01_warmup import latest_documents, category_counts


def doc(tenant="a", key="1", version=1, title="Title", categories=()):
    return Document(tenant, key, version, title, "body", frozenset(categories))


def test_latest_empty():
    assert latest_documents(iter(())) == []


def test_latest_keeps_highest_not_last_version():
    newer, older = doc(version=3), doc(version=1)
    assert latest_documents([newer, older]) == [newer]


def test_latest_equal_version_last_payload_wins():
    first = doc(title="first")
    last = replace(first, title="last")
    assert latest_documents([first, last]) == [last]


def test_latest_identity_includes_tenant():
    a, b = doc(tenant="a"), doc(tenant="b")
    assert latest_documents([b, a]) == [a, b]


def test_latest_sorts_identity_and_accepts_one_shot_iterable():
    a1, a2, b1 = doc(key="1"), doc(key="2"), doc(tenant="b")
    assert latest_documents(x for x in [b1, a2, a1]) == [a1, a2, b1]


def test_latest_does_not_mutate_input():
    data = [doc(version=2), doc(version=1)]
    before = list(data)
    latest_documents(data)
    assert data == before


def test_categories_empty():
    assert category_counts([]) == {}


def test_categories_multilabel_and_no_category():
    data = [doc(key="1", categories=("contract", "employment")),
            doc(key="2", categories=("contract",)), doc(key="3")]
    assert category_counts(iter(data)) == {"contract": 2, "employment": 1}


def test_categories_preserve_case_and_do_not_dedupe_input():
    one = doc(categories=("Memo", "memo"))
    assert category_counts([one, one]) == {"Memo": 2, "memo": 2}
