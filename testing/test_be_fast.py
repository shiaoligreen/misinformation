"""Tests for be_fast.py"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Client fixture
@pytest.fixture(scope="module")
def client():
    with patch("be_search.build_or_load_index"):
        from be_fast import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

def _empty():
    return {"main_results": [], "ai_results": []}

def _one_result():
    return {
        "main_results": [{
            "doc_id": "annot_0", "raw_text": "maybe this is true",
            "source": "annotated", "tags": "hedging",
            "misinformation_label": "1", "raw_tags": {},
        }],
        "ai_results": [],
    }


# /health
def test_health(client):
    assert client.get("/health").json() == {"status": "online"}


# /search — response shape
class TestSearchShape:

    def test_returns_200_with_main_and_ai_keys(self, client):
        with patch("be_search.search", return_value=_empty()):
            data = client.get("/search", params={"query": "test"}).json()
        assert "main_results" in data
        assert "ai_results" in data

    def test_result_item_has_expected_fields(self, client):
        with patch("be_search.search", return_value=_one_result()):
            item = client.get("/search", params={"query": "maybe"}).json()["main_results"][0]
        for field in ["doc_id", "raw_text", "source", "tags", "misinformation_label", "raw_tags"]:
            assert field in item


# /search — parameter forwarding
class TestSearchParams:

    @pytest.mark.parametrize("params, key, expected", [
        ({"query": "climate"},                        "query",                "climate"),
        ({"query": "", "source": "annotated"},        "source",               "annotated"),
        ({"query": "", "misinformation_filter": "1"}, "misinformation_filter","1"),
    ])
    def test_param_forwarded(self, client, params, key, expected):
        with patch("be_search.search", return_value=_empty()) as mock_fn:
            client.get("/search", params=params)
        assert str(expected) in str(mock_fn.call_args)

    def test_tags_list_forwarded(self, client):
        with patch("be_search.search", return_value=_empty()) as mock_fn:
            client.get("/search", params=[("query", ""), ("tags", "hedging"), ("tags", "all_caps")])
        tags = mock_fn.call_args.kwargs.get("tags", [])
        assert "hedging" in tags and "all_caps" in tags

    def test_show_ai_true_forwarded(self, client):
        with patch("be_search.search", return_value=_empty()) as mock_fn:
            client.get("/search", params={"query": "", "show_ai": True})
        assert "True" in str(mock_fn.call_args)


# /search — edge cases
def test_search_exception_returns_500(client):
    with patch("be_search.search", side_effect=RuntimeError("Index not loaded")):
        assert client.get("/search", params={"query": "test"}).status_code == 500

def test_no_params_returns_200(client):
    with patch("be_search.search", return_value=_empty()):
        assert client.get("/search").status_code == 200


# Lifespan
def test_build_or_load_index_called_on_startup():
    with patch("be_search.build_or_load_index") as mock_build:
        from be_fast import app
        with TestClient(app):
            pass
        mock_build.assert_called_once()
