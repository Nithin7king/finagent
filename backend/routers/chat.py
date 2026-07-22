"""
FinAgent — Chat Router
Agent chat endpoint with streaming-friendly responses.
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend import models, schemas
from backend.agent.planner_langgraph import LangGraphPlanner as AgentPlanner

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def chat(
    data: schemas.ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Send a message to the AI agent and receive a response.
    The agent uses multi-step reasoning, tool calls, and RAG to answer.
    """
    session_id = data.session_id or str(uuid.uuid4())
    agent = AgentPlanner(db=db, user_id=current_user.id, session_id=session_id)
    result = agent.respond(data.message)

    return schemas.ChatResponse(
        response=result["response"],
        sources=result.get("sources", []),
        tool_calls_made=result.get("tool_calls_made", []),
        session_id=result["session_id"],
    )


@router.get("/history")
def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get conversation history for a session."""
    from backend.agent.memory import AgentMemory
    memory = AgentMemory(db, current_user.id, session_id)
    history = memory.get_history()
    return {"session_id": session_id, "messages": history, "count": len(history)}


@router.get("/digest")
def get_weekly_digest(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generate a proactive weekly financial digest."""
    session_id = f"digest_{uuid.uuid4()}"
    agent = AgentPlanner(db=db, user_id=current_user.id, session_id=session_id)
    digest = agent.generate_weekly_digest()
    return {"digest": digest}
