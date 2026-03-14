"""Tests for be_search.py"""

import json
import csv
import os
import pytest
from unittest.mock import patch, MagicMock

from whoosh.index import create_in
from whoosh import index

import be_search
from be_search import clean, make_schema, build_or_load_index, search, ALL_TAGS


# Helpers
def _make_annotation(text="sample text", label="1", tags=None):
    record = {"Text": text, "misinformation_label": label}
    for t in ALL_TAGS:
        record[t] = (tags or {}).get(t, [])
    return record

def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["", "text", "label"])
        writer.writeheader()
        writer.writerows(rows)


# Fixtures
@pytest.fixture()
def tmp_index_dir(tmp_path):
    d = str(tmp_path / "whoosh_index")
    with patch.object(be_search, "INDEX_DIR", d):
        yield d

@pytest.fixture()
def fresh_ix(tmp_index_dir):
    os.makedirs(tmp_index_dir, exist_ok=True)
    ix = create_in(tmp_index_dir, make_schema())
    be_search.ix = ix
    yield ix
    be_search.ix = None

@pytest.fixture()
def populated_ix(fresh_ix):
    writer = fresh_ix.writer()
    docs = [
        dict(doc_id="annot_0", text="maybe this is true",   source="annotated",
             tags="hedging",   misinformation_label="1",
             raw_text="maybe this is true",
             raw_tags=json.dumps({t: [] for t in ALL_TAGS})),
        dict(doc_id="annot_1", text="SHOUT at the top",     source="annotated",
             tags="all_caps",  misinformation_label="0",
             raw_text="SHOUT at the top",
             raw_tags=json.dumps({t: [] for t in ALL_TAGS})),
        dict(doc_id="ai_0",    text="possibly a rumour",    source="gemini",
             tags="hedging",   misinformation_label="1",
             raw_text="possibly a rumour",
             raw_tags=json.dumps({t: [] for t in ALL_TAGS})),
        dict(doc_id="corpus_0", text="plain corpus document", source="corpus",
             tags="",          misinformation_label="0",
             raw_text="plain corpus document",
             raw_tags=json.dumps({t: [] for t in ALL_TAGS})),
    ]
    for d in docs:
        writer.add_document(**d)
    writer.commit()
    # Reopen after commit so the index object reflects the committed state
    reopened = index.open_dir(fresh_ix.storage.folder)
    be_search.ix = reopened
    return reopened


# clean()
class TestClean:

    @pytest.mark.parametrize("raw, expected", [
        ("Hello World",     "hello world"),
        ("  hello  ",       "hello"),
        ("hello   world",   "hello world"),
        ("hello\tworld\n",  "hello world"),
        ("",                ""),
    ])
    def test_clean(self, raw, expected):
        assert clean(raw) == expected


# make_schema()
class TestMakeSchema:

    def test_required_fields_and_uniqueness(self):
        schema = make_schema()
        for field in ["doc_id", "text", "source", "tags", "misinformation_label", "raw_text", "raw_tags"]:
            assert field in schema.names()
        assert schema["doc_id"].unique is True


# build_or_load_index()
class TestBuildOrLoadIndex:

    def test_builds_when_no_index_exists(self, tmp_index_dir):
        with patch("be_search.build_index") as mock_build:
            mock_build.return_value = object()
            build_or_load_index()
            mock_build.assert_called_once()

    def test_loads_existing_index(self, tmp_index_dir):
        os.makedirs(tmp_index_dir, exist_ok=True)
        create_in(tmp_index_dir, make_schema()).close()
        with patch("be_search.index.open_dir") as mock_open:
            # Use MagicMock so attribute access (e.g. .latest_generation()) doesn't raise
            mock_open.return_value = MagicMock()
            build_or_load_index()
            mock_open.assert_called_once_with(tmp_index_dir)


# Document ingestion — annotations, AI annotations, corpus
# (one test per source type, same logic)
class TestIngestion:

    def test_annotations_deduplication_and_tag_recording(self, fresh_ix, tmp_path):
        annotations = [
            _make_annotation("unique text", "1", tags={"hedging": [["maybe", 0, 5]]}),
            _make_annotation("unique text", "1"),
        ]
        ann_file = tmp_path / "annotations.json"
        ann_file.write_text(json.dumps(annotations), encoding="utf-8")

        with patch.object(be_search, "ANNOTATIONS_PATH", ann_file):
            writer = fresh_ix.writer()
            seen = set()
            count = be_search.add_annotations(writer, seen)
            writer.commit()

        assert count == 1

        # Reopen the index from disk after commit to avoid ReaderClosed errors
        reopened = index.open_dir(fresh_ix.storage.folder)
        with reopened.searcher() as s:
            results = list(s.search(be_search.Every()))
        assert "hedging" in results[0]["tags"]

    def test_ai_annotations_indexed_independently_of_main(self, fresh_ix, tmp_path):
        ai_docs = [{"ID": 1, "Text": "shared text", "misinformation_label": "1",
                    **{t: [] for t in ALL_TAGS}}]
        ai_file = tmp_path / "ai.json"
        ai_file.write_text(json.dumps(ai_docs), encoding="utf-8")

        with patch.object(be_search, "AI_PATH", ai_file):
            writer = fresh_ix.writer()
            seen_ai = set()  # independent of seen_main; shared text is not in here
            count = be_search.add_ai_annotations(writer, seen_ai)
            writer.commit()

        assert count == 1

    def test_ai_annotations_deduplication_within_ai_set(self, fresh_ix, tmp_path):
        ai_docs = [
            {"ID": 1, "Text": "shared text", "misinformation_label": "1",
             **{t: [] for t in ALL_TAGS}},
            {"ID": 2, "Text": "shared text", "misinformation_label": "1",
             **{t: [] for t in ALL_TAGS}},
        ]
        ai_file = tmp_path / "ai.json"
        ai_file.write_text(json.dumps(ai_docs), encoding="utf-8")

        with patch.object(be_search, "AI_PATH", ai_file):
            writer = fresh_ix.writer()
            count = be_search.add_ai_annotations(writer, set())
            writer.commit()

        assert count == 1

    def test_corpus_docs_empty_raw_tags_structure(self, fresh_ix, tmp_path):
        csv_path = tmp_path / "corpus.csv"
        _write_csv(csv_path, [{"": "0", "text": "some text", "label": "0"}])

        with patch.object(be_search, "CSV_PATH", csv_path):
            writer = fresh_ix.writer()
            count = be_search.add_corpus_docs(writer, set())
            writer.commit()

        assert count == 1

        # Reopen the index from disk after commit to avoid ReaderClosed errors
        reopened = index.open_dir(fresh_ix.storage.folder)
        with reopened.searcher() as s:
            raw_tags = json.loads(list(s.search(be_search.Every()))[0]["raw_tags"])
        assert set(raw_tags.keys()) == set(ALL_TAGS)
        assert all(v == [] for v in raw_tags.values())


# search()
class TestSearch:

    def test_raises_if_index_not_loaded(self):
        be_search.ix = None
        with pytest.raises(RuntimeError, match="Index not loaded"):
            search("anything")

    def test_result_has_required_keys(self, populated_ix):
        results = search("", source="all")
        required = {"doc_id", "raw_text", "source", "tags", "misinformation_label", "raw_tags"}
        for r in results["main_results"]:
            assert required.issubset(r.keys())

    def test_keyword_match(self, populated_ix):
        ids = [r["doc_id"] for r in search("maybe")["main_results"]]
        assert "annot_0" in ids

    def test_source_annotated_excludes_corpus(self, populated_ix):
        sources = {r["source"] for r in search("", source="annotated")["main_results"]}
        assert sources == {"annotated"}

    def test_show_ai_returns_ai_results(self, populated_ix):
        ai_ids = [r["doc_id"] for r in search("", show_ai=True)["ai_results"]]
        assert "ai_0" in ai_ids

    def test_show_ai_false_returns_empty_ai_list(self, populated_ix):
        assert search("", show_ai=False)["ai_results"] == []

    def test_tag_filter(self, populated_ix):
        ids = [r["doc_id"] for r in search("", source="annotated", tags=["hedging"])["main_results"]]
        assert "annot_0" in ids
        assert "annot_1" not in ids

    @pytest.mark.parametrize("label", ["0", "1"])
    def test_misinformation_label_filter(self, populated_ix, label):
        labels = {r["misinformation_label"] for r in search("", source="all", misinformation_filter=label)["main_results"]}
        assert labels == {label}

    def test_limit_respected(self, populated_ix):
        assert len(search("", source="all", limit=1)["main_results"]) <= 1
