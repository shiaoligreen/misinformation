# `be_search.py` — Search Engine & Index Management

Core data layer. Handles corpus ingestion, Whoosh index construction, and query execution. Has no awareness of the HTTP or UI layers.

The index is built once at startup and held in a module-level variable (`ix`), so queries are served from memory without re-reading the corpus.

---

## Whoosh Schema

| Field | Stored | Purpose |
|---|---|---|
| `doc_id` | Yes | Unique ID — e.g. `annot_0`, `ai_42`, `corpus_1337` |
| `text` | No | Searchable content. `stoplist=None` preserves stop-words for hedging detection |
| `source` | Yes | `annotated`, `gemini`, or `corpus` |
| `tags` | Yes | Space-separated present annotation tags, used for filter queries |
| `misinformation_label` | Yes | `"0"` or `"1"` |
| `raw_text` | Yes | Original text returned to the frontend |
| `raw_tags` | Yes | JSON `{ tag: [[word, start, end], ...] }` map for word-level highlighting |

---

## Functions

**`build_or_load_index()`** — Called by `be_fast.py` at startup. Opens an existing index at `whoosh_index/` if present; otherwise calls `build_index()`.

**`build_index()`** — Creates the index and takes in all three sources in order: human annotations → AI annotations → corpus. Annotated examples are indexed first so duplicate texts retain their annotation spans.

**`add_annotations(writer, seen)`** / **`add_ai_annotations(writer, seen)`** / **`add_corpus_docs(writer, seen)`** — Each reads its respective file, skips empty or already-seen texts (checked via `clean()`), and writes documents to the index. Return the count of documents added.

**`clean(text)`** — Lowercases and collapses whitespace. Used for duplicate detection.

**`search(query, source, show_ai, tags, misinformation_filter, limit=50)`** — Public search function. Parses the query string into a Whoosh query object (or `Every()` if empty), then calls `fetch_results()`. If `show_ai=True`, runs a second parallel search against the `gemini` source.

**`fetch_results(searcher, text_query, source, tags, misinformation_filter, limit)`** — Compiles Boolean filter conditions and executes the search. All active conditions are combined with `And()` and passed as the `filter` argument to `searcher.search()`.

| Filter | Whoosh query |
|---|---|
| `source == "annotated"` | `Term("source", "annotated")` |
| `source == "gemini"` | `Term("source", "gemini")` |
| `source == "all"` | `Or([Term("source", "annotated"), Term("source", "corpus")])` |
| tag in `tags` | `Term("tags", tag)` — one per tag, all AND-ed |
| `misinformation_filter` in `["0","1"]` | `Term("misinformation_label", value)` |
