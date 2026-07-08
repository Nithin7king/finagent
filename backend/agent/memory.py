"""
FinAgent — Agent Memory
Session + cross-session memory stored in SQLite.
Maintains last 10 turns per session + a persistent financial profile.
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend import models


class AgentMemory:
    """
    Manages conversation memory for the AI agent.
    - Session memory: last N turns (short-term)
    - Persistent memory: user financial profile facts (long-term)
    """

    MAX_SESSION_TURNS = 10

    def __init__(self, db: Session, user_id: int, session_id: str):
        self.db = db
        self.user_id = user_id
        self.session_id = session_id

    def add_message(self, role: str, content: str):
        """
        Store a message in memory.
        role: "user" | "assistant" | "system"
        """
        mem = models.AgentMemory(
            user_id=self.user_id,
            session_id=self.session_id,
            role=role,
            content=content,
        )
        self.db.add(mem)
        self.db.commit()

        # Prune to MAX_SESSION_TURNS
        self._prune_session()

    def _prune_session(self):
        """Keep only the most recent MAX_SESSION_TURNS messages per session."""
        session_messages = (
            self.db.query(models.AgentMemory)
            .filter(
                models.AgentMemory.user_id == self.user_id,
                models.AgentMemory.session_id == self.session_id,
            )
            .order_by(models.AgentMemory.created_at.desc())
            .all()
        )
        if len(session_messages) > self.MAX_SESSION_TURNS * 2:  # *2 for user+assistant pairs
            old_messages = session_messages[self.MAX_SESSION_TURNS * 2:]
            for m in old_messages:
                self.db.delete(m)
            self.db.commit()

    def get_history(self, include_system: bool = False) -> List[Dict[str, str]]:
        """
        Get conversation history for this session.
        Returns list of {role, content} dicts suitable for LLM context.
        """
        query = (
            self.db.query(models.AgentMemory)
            .filter(
                models.AgentMemory.user_id == self.user_id,
                models.AgentMemory.session_id == self.session_id,
            )
            .order_by(models.AgentMemory.created_at.asc())
        )
        if not include_system:
            query = query.filter(models.AgentMemory.role != "system")

        messages = query.all()
        return [{"role": m.role, "content": m.content} for m in messages]

    def get_persistent_facts(self) -> List[str]:
        """
        Get persistent (cross-session) memory facts about the user.
        Returns list of fact strings.
        """
        facts = (
            self.db.query(models.AgentMemory)
            .filter(
                models.AgentMemory.user_id == self.user_id,
                models.AgentMemory.session_id == None,  # noqa: E711 - persistent = no session
                models.AgentMemory.role == "system",
            )
            .order_by(models.AgentMemory.created_at.desc())
            .limit(10)
            .all()
        )
        return [f.content for f in facts]

    def save_persistent_fact(self, fact: str):
        """
        Save a cross-session fact about the user (e.g., "User's monthly income is ₹85,000").
        """
        # Check for duplicates
        existing = (
            self.db.query(models.AgentMemory)
            .filter(
                models.AgentMemory.user_id == self.user_id,
                models.AgentMemory.session_id == None,  # noqa: E711
                models.AgentMemory.content == fact,
            )
            .first()
        )
        if not existing:
            mem = models.AgentMemory(
                user_id=self.user_id,
                session_id=None,
                role="system",
                content=fact,
            )
            self.db.add(mem)
            self.db.commit()

    def format_history_for_prompt(self) -> str:
        """Format conversation history as a string for inclusion in LLM prompt."""
        history = self.get_history()
        if not history:
            return ""
        lines = []
        for msg in history[-6:]:  # Last 3 turns (user + assistant each)
            prefix = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{prefix}: {msg['content'][:500]}")  # Truncate long messages
        return "\n".join(lines)
