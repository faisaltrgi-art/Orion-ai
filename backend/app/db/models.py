"""SQLAlchemy ORM models."""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, Date, Boolean, ForeignKey, Text, BigInteger, func, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    credits: Mapped[int] = mapped_column(Integer, default=3)
    last_reset: Mapped[date] = mapped_column(Date, default=date.today)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    plan_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reports: Mapped[List["Report"]] = relationship("Report", back_populates="user", lazy="selectin")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="user", lazy="selectin")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    agent_type: Mapped[str] = mapped_column(String(50), default="orchestrator")
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", lazy="selectin", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, agent, system
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_uuid: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    final_content: Mapped[str] = mapped_column(Text, nullable=False)
    agents_used: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="reports")


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    referred_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    bonus_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Quest(Base):
    __tablename__ = "quests"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    quest_type: Mapped[str] = mapped_column(String(50), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=5)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
