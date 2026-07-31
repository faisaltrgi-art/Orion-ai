"""Conversation and chat endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db import get_db
from app.db.models import Conversation, Message, User
from app.agents import orchestrator

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class MessageCreate(BaseModel):
    content: str
    agent_type: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    agent_name: Optional[str]
    content: str
    created_at: str


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    agent_type: str
    status: str
    created_at: str
    messages: List[MessageResponse]


class AgentListResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    color: str


@router.get("/agents", response_model=List[AgentListResponse])
async def list_agents():
    """List all available AI agents."""
    agents = orchestrator.get_available_agents()
    return [AgentListResponse(**a) for a in agents]


@router.post("", response_model=ConversationResponse)
async def create_conversation(data: MessageCreate, current_user: dict = Depends(get_current_user)):
    """Create new conversation and get first response."""
    async with get_db() as db:
        user_id = int(current_user["sub"])

        # Check credits
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user or user.credits <= 0:
            raise HTTPException(status_code=403, detail="Insufficient credits")

        # Deduct credit
        user.credits -= 1

        # Create conversation
        conv = Conversation(
            user_id=user_id,
            title=data.content[:50] + "..." if len(data.content) > 50 else data.content,
            agent_type=data.agent_type or "orchestrator"
        )
        db.add(conv)
        await db.flush()

        # Save user message
        user_msg = Message(conversation_id=conv.id, role="user", content=data.content)
        db.add(user_msg)

        # Generate AI response
        if data.agent_type and data.agent_type != "orchestrator":
            response = await orchestrator.chat_with_agent(data.agent_type, data.content)
        else:
            response = await orchestrator.process(data.content)

        # Save AI message
        ai_msg = Message(
            conversation_id=conv.id,
            role="agent",
            agent_name=response.agent_name,
            content=response.content,
            metadata=response.metadata
        )
        db.add(ai_msg)

        await db.commit()

        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            agent_type=conv.agent_type,
            status=conv.status,
            created_at=conv.created_at.isoformat(),
            messages=[
                MessageResponse(id=user_msg.id, role="user", agent_name=None, content=user_msg.content, created_at=user_msg.created_at.isoformat()),
                MessageResponse(id=ai_msg.id, role="agent", agent_name=ai_msg.agent_name, content=ai_msg.content, created_at=ai_msg.created_at.isoformat())
            ]
        )


@router.get("", response_model=List[dict])
async def list_conversations(current_user: dict = Depends(get_current_user)):
    """List user conversations."""
    async with get_db() as db:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == int(current_user["sub"]))
            .order_by(desc(Conversation.created_at))
        )
        conversations = result.scalars().all()
        return [
            {
                "id": c.id,
                "title": c.title,
                "agent_type": c.agent_type,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
                "message_count": len(c.messages)
            }
            for c in conversations
        ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int, current_user: dict = Depends(get_current_user)):
    """Get conversation with messages."""
    async with get_db() as db:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == int(current_user["sub"]))
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            agent_type=conv.agent_type,
            status=conv.status,
            created_at=conv.created_at.isoformat(),
            messages=[
                MessageResponse(
                    id=m.id, role=m.role, agent_name=m.agent_name,
                    content=m.content, created_at=m.created_at.isoformat()
                )
                for m in conv.messages
            ]
        )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """Send message in existing conversation."""
    async with get_db() as db:
        user_id = int(current_user["sub"])

        # Verify conversation
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Check credits
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user or user.credits <= 0:
            raise HTTPException(status_code=403, detail="Insufficient credits")

        user.credits -= 1

        # Save user message
        user_msg = Message(conversation_id=conv.id, role="user", content=data.content)
        db.add(user_msg)

        # Generate response
        if conv.agent_type and conv.agent_type != "orchestrator":
            response = await orchestrator.chat_with_agent(conv.agent_type, data.content)
        else:
            response = await orchestrator.process(data.content)

        ai_msg = Message(
            conversation_id=conv.id,
            role="agent",
            agent_name=response.agent_name,
            content=response.content,
            metadata=response.metadata
        )
        db.add(ai_msg)
        await db.commit()

        return MessageResponse(
            id=ai_msg.id,
            role="agent",
            agent_name=ai_msg.agent_name,
            content=ai_msg.content,
            created_at=ai_msg.created_at.isoformat()
        )
