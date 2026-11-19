from datetime import datetime

from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    """Information about one uploaded document."""

    document_id: str
    filename: str
    size_bytes: int
    page_count: int
    status: str
    uploaded_at: datetime


class UploadResponse(BaseModel):
    """Returned after a successful upload."""

    message: str
    document: DocumentInfo


class PageText(BaseModel):
    """Text from one PDF page."""

    page_number: int
    text: str


class DocumentPages(BaseModel):
    """All extracted pages for one document."""

    document_id: str
    filename: str
    page_count: int
    pages: list[PageText]


class SearchResult(BaseModel):
    """One chunk returned by a search."""

    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    score: float
    text: str


class SearchResponse(BaseModel):
    """The results for one question."""

    question: str
    results: list[SearchResult]


class AskRequest(BaseModel):
    """A question sent to AVARA. Omit session_id to start a new conversation."""

    question: str = Field(..., min_length=3, max_length=1000)
    session_id: str | None = Field(None, pattern=r"^[0-9a-f]{32}$")
    top_k: int = Field(5, ge=1, le=10)
    document_id: str | None = Field(None, pattern=r"^[0-9a-f]{32}$")


class Citation(BaseModel):
    """One source used for an answer."""

    number: int
    document_id: str
    filename: str
    page_number: int
    score: float
    snippet: str


class AskResponse(BaseModel):
    """The answer, its session, whether it was grounded, and its sources."""

    session_id: str
    question: str
    standalone_question: str
    answer: str
    grounded: bool
    citations: list[Citation]
    missing: list[str] = []


class ClearResponse(BaseModel):
    """Returned after a conversation is cleared."""

    session_id: str
    message: str

class AgentRequest(BaseModel):
    """A request for the AVARA agent, which may call tools."""

    request: str = Field(..., min_length=3, max_length=1000)


class ToolCallLog(BaseModel):
    """One tool call made during an agent request."""

    name: str
    arguments: dict
    status: str | None = None
    result: dict | None = None


class AgentResponse(BaseModel):
    """The agent's answer and a record of the tools it used."""

    request: str
    answer: str
    tool_calls: list[ToolCallLog]
    limit_reached: bool