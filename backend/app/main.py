from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import agent, documents, qa, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts: creates folders and the database table.
    settings.ensure_directories()
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Virtual Assistant for Retrieval and Action",
    lifespan=lifespan,
)

# Allow the Vite dev server to call the API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(documents.router)
app.include_router(search.router)
app.include_router(qa.router)
app.include_router(agent.router)


@app.get("/health")
def health() -> dict:
    """Simple check that the server is running."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }