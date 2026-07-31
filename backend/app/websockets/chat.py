"""WebSocket chat endpoint for real-time agent communication."""
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.security import decode_token
from app.db import AsyncSessionLocal
from app.db.models import User, Conversation, Message
from app.agents import orchestrator

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected")

    async def send_message(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)


manager = ConnectionManager()


async def websocket_chat(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time chat."""
    # Authenticate
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    user_id = int(payload["sub"])
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message_type = data.get("type", "message")

            if message_type == "message":
                content = data.get("content", "").strip()
                agent_type = data.get("agent_type", "orchestrator")
                conversation_id = data.get("conversation_id")

                if not content:
                    continue

                # Check credits
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()

                    if not user or user.credits <= 0:
                        await manager.send_message(user_id, {
                            "type": "error",
                            "content": "رصيدك منتهي. قم بترقية خطتك."
                        })
                        continue

                    user.credits -= 1

                    # Get or create conversation
                    if conversation_id:
                        conv_result = await db.execute(
                            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
                        )
                        conv = conv_result.scalar_one_or_none()
                    else:
                        conv = Conversation(user_id=user_id, title=content[:50], agent_type=agent_type)
                        db.add(conv)
                        await db.flush()
                        conversation_id = conv.id

                    # Save user message
                    user_msg = Message(conversation_id=conv.id, role="user", content=content)
                    db.add(user_msg)
                    await db.commit()

                # Send typing indicator
                await manager.send_message(user_id, {
                    "type": "typing",
                    "agent_name": agent_type,
                    "conversation_id": conversation_id
                })

                # Generate AI response
                if agent_type and agent_type != "orchestrator":
                    response = await orchestrator.chat_with_agent(agent_type, content)
                else:
                    response = await orchestrator.process(content)

                # Save AI response
                async with AsyncSessionLocal() as db:
                    ai_msg = Message(
                        conversation_id=conversation_id,
                        role="agent",
                        agent_name=response.agent_name,
                        content=response.content,
                        metadata=response.metadata
                    )
                    db.add(ai_msg)
                    await db.commit()

                # Send response
                await manager.send_message(user_id, {
                    "type": "message",
                    "role": "agent",
                    "agent_name": response.agent_name,
                    "content": response.content,
                    "conversation_id": conversation_id,
                    "metadata": response.metadata
                })

                # Send updated credits
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    await manager.send_message(user_id, {
                        "type": "credits_update",
                        "credits": user.credits if user else 0
                    })

            elif message_type == "ping":
                await manager.send_message(user_id, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.exception(f"WebSocket error for user {user_id}")
        manager.disconnect(user_id)
