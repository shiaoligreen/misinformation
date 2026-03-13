# `be_fast.py` — FastAPI Backend Entry Point

## Overview

Initialises and runs the FastAPI application. Responsible for server lifecycle management and routing HTTP requests to the search logic in `be_search.py`.

This is the file passed to `uvicorn` at startup:

```bash
uvicorn be_fast:app --reload --port 8000
```

---

## Dependencies

| Import | Purpose |
|---|---|
| `fastapi` | ASGI web framework |
| `contextlib.asynccontextmanager` | Enables the lifespan context manager pattern |
| `be_search` | Internal module — search logic and index management |

---

## Startup & Shutdown — `lifespan`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
```

An async context manager registered with the FastAPI app that runs **once** at process start and once at shutdown.

- **On startup:** calls `be_search.build_or_load_index()` to either load an existing Whoosh index from disk or build one from scratch before any requests are accepted.
- **On shutdown:** logs a shutdown message.

This pattern ensures the index is fully ready before the server begins serving traffic, and avoids re-loading the corpus on every query.

---

## App Initialisation

```python
app = FastAPI(
    title="Search Backend",
    description="API for querying Whoosh index",
    lifespan=lifespan
)
```

Creates the FastAPI application instance with the lifespan hook attached. Auto-generated API docs are available at `http://localhost:8000/docs` while the server is running.

---

## Endpoints

### `GET /search`

```python
@app.get("/search")
async def get_search(
    query: str = " ",
    source: str = "all",
    show_ai: bool = False,
    tags: list[str] | None = Query(None),
    misinformation_filter: str = "all"
)
```

Primary search endpoint. Accepts query parameters from the frontend and delegates to `be_search.search()`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | `" "` | Keyword search string |
| `source` | `str` | `"all"` | Data source filter: `"all"`, `"annotated"`, or `"gemini"` |
| `show_ai` | `bool` | `False` | Whether to also return AI (Gemini) annotation results |
| `tags` | `list[str]` | `None` | Annotation tags to filter by (repeatable parameter) |
| `misinformation_filter` | `str` | `"all"` | Label filter: `"0"`, `"1"`, or `"all"` |

**Returns:** JSON object `{ "main_results": [...], "ai_results": [...] }`

---

### `GET /health`

```python
@app.get("/health")
def health_check():
    return {"status": "online"}
```

Lightweight health check endpoint. Returns `{ "status": "online" }` when the server is running.

Used by Docker to confirm the container is ready. If `/health` succeeds but `/search` fails, the issue is with the Whoosh index rather than the server itself.

---

## Interaction with Other Modules

```
be_fast.py
    └── be_search.build_or_load_index()   (called once at startup)
    └── be_search.search(...)             (called on every /search request)
```
