from fastapi.testclient import TestClient

from practice.exercise2_search_api import app

client = TestClient(app)


def test_search_is_tenant_scoped():
    response = client.get(
        "/search",
        params={"query": "acme"},
        headers={"X-Tenant-ID": "firm-a"},
    )
    assert response.status_code == 200
    assert response.json() == [
        {"document_id": "a-1", "title": "Acme Contract"},
    ]


def test_other_tenant_sees_only_its_own_document():
    response = client.get(
        "/search",
        params={"query": "acme"},
        headers={"X-Tenant-ID": "firm-b"},
    )
    assert response.status_code == 200
    assert response.json() == [
        {"document_id": "b-1", "title": "Acme Litigation"},
    ]


def test_query_validation():
    response = client.get(
        "/search",
        params={"query": " "},
        headers={"X-Tenant-ID": "firm-a"},
    )
    assert response.status_code == 422


def test_limit_validation():
    response = client.get(
        "/search",
        params={"query": "acme", "limit": 101},
        headers={"X-Tenant-ID": "firm-a"},
    )
    assert response.status_code == 422


def test_missing_tenant_header():
    response = client.get("/search", params={"query": "acme"})
    assert response.status_code == 422
