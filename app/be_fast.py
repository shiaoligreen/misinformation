# FastAPI


from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
import be_search

# One-time build of whoosh index at start up 
# before requests received
@asynccontextmanager
async def lifespan(app: FastAPI):
    # starts Whoosh index and buildin/loading process
    print("Backend: Loading Whoosh search index...")
    be_search.build_or_load_index()
    yield
    print("Backend: Shutting down...")

# App initialization
app = FastAPI(
    title="Search Backend",
    description="API for querying Whoosh index",
    lifespan=lifespan
)

# Search
@app.get("/search")
async def get_search(
    query: str = " ",
    source: str = "all",
    show_ai: bool = False,
    tags: list[str] | None = Query(None),
    misinformation_filter: str = "all"
):
    '''
    Receives search parameters from the frontend and returns
    results from the Whoosh index.
    '''
    # Pass all parameters from URL to search
    results = be_search.search(
        query=query,
        source=source,
        show_ai=show_ai,
        tags=tags,
        misinformation_filter=misinformation_filter
    )
    return results


# 4. Health Check, for signalling to Docker that code is
# running and server is ready for requests
# If /health works but /search doesn't, then problem with index, not server
@app.get("/health")
def health_check():
    return {"status": "online"}