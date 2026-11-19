from fastapi import APIRouter, HTTPException

from app.schemas import AgentRequest, AgentResponse, ToolCallLog
from app.services.agent import run_agent
from app.services.llm import LLMError

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("", response_model=AgentResponse)
def agent_endpoint(body: AgentRequest) -> AgentResponse:
    """Run the AVARA agent. It may call read-only document tools to answer the request."""
    request = body.request.strip()
    if len(request) < 3:
        raise HTTPException(status_code=400, detail="The request is too short.")

    try:
        result = run_agent(request)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AgentResponse(
        request=request,
        answer=result["answer"],
        tool_calls=[ToolCallLog(**call) for call in result["tool_calls"]],
        limit_reached=result["limit_reached"],
    )