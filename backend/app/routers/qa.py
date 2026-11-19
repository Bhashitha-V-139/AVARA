import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import (
    add_message,
    clear_session_messages,
    create_session,
    get_recent_messages,
    session_exists,
)
from app.schemas import AskRequest, AskResponse, ClearResponse
from app.services.llm import LLMError
from app.services.rag import HISTORY_MESSAGES, answer_question

router = APIRouter(prefix="/ask", tags=["questions"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    """Ask a question. Send the returned session_id with later questions to continue the conversation."""
    question = body.question.strip()
    if len(question) < 3:
        raise HTTPException(status_code=400, detail="The question is too short.")

    # Start a new session if the client didn't provide one.
    session_id = body.session_id or uuid.uuid4().hex
    if body.session_id and not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found. Start a new conversation.")
    if not body.session_id:
        create_session(session_id, _now())

    history = get_recent_messages(session_id, HISTORY_MESSAGES)

    try:
        result = answer_question(
            question,
            history=history,
            top_k=body.top_k,
            document_id=body.document_id,
        )
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Save the exchange so future follow-ups have context.
    add_message(session_id, "user", question, _now())
    add_message(
        session_id,
        "assistant",
        result["answer"],
        _now(),
        citations_json=json.dumps(result["citations"]),
    )

    return AskResponse(
        session_id=session_id,
        question=question,
        standalone_question=result["standalone_question"],
        answer=result["answer"],
        grounded=result["grounded"],
        citations=result["citations"],
        missing=result["missing"],
    )


@router.delete("/{session_id}", response_model=ClearResponse)
def clear_conversation(session_id: str) -> ClearResponse:
    """Clear a conversation's history. The session ID stays valid for a fresh start."""
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")
    clear_session_messages(session_id)
    return ClearResponse(session_id=session_id, message="Conversation cleared.")