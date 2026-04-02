"""
Async SQLAlchemy database layer.
- Engine with asyncpg + connection pooling
- Async session factory
- Declarative ORM models matching schema.sql exactly
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,          # verify connection health before use
    echo=settings.db_echo,
)

# ── Session factory ───────────────────────────────────────────────────────────

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,      # objects remain usable after commit
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields a database session.
    Rolls back on exception; always closes on exit.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Base model ────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── ENUM types ────────────────────────────────────────────────────────────────

class ChannelType(str, enum.Enum):
    web       = "web"
    gmail     = "gmail"
    whatsapp  = "whatsapp"


class TicketStatus(str, enum.Enum):
    open             = "open"
    in_progress      = "in_progress"
    waiting_customer = "waiting_customer"
    resolved         = "resolved"
    closed           = "closed"
    escalated        = "escalated"


class TicketPriority(str, enum.Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"


class MessageDirection(str, enum.Enum):
    inbound  = "inbound"
    outbound = "outbound"


class MessageStatus(str, enum.Enum):
    received   = "received"
    processing = "processing"
    replied    = "replied"
    failed     = "failed"


# ── ORM Models ────────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id:           Mapped[uuid.UUID]          = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str]                = mapped_column(Text, nullable=False)
    email:        Mapped[Optional[str]]      = mapped_column(Text, unique=True)
    phone:        Mapped[Optional[str]]      = mapped_column(Text, unique=True)
    company:      Mapped[Optional[str]]      = mapped_column(Text)
    plan:         Mapped[Optional[str]]      = mapped_column(Text)
    metadata_:    Mapped[dict]               = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at:   Mapped[datetime]           = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at:   Mapped[datetime]           = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    identifiers:  Mapped[list["CustomerIdentifier"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]]       = relationship(back_populates="customer", cascade="all, delete-orphan")
    messages:     Mapped[list["Message"]]             = relationship(back_populates="customer", cascade="all, delete-orphan")
    tickets:      Mapped[list["Ticket"]]              = relationship(back_populates="customer", cascade="all, delete-orphan")


class CustomerIdentifier(Base):
    __tablename__ = "customer_identifiers"
    __table_args__ = (UniqueConstraint("channel", "external_id"),)

    id:          Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    channel:     Mapped[str]        = mapped_column(Enum(ChannelType, name="channel_type"), nullable=False)
    external_id: Mapped[str]        = mapped_column(Text, nullable=False)
    metadata_:   Mapped[dict]       = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at:  Mapped[datetime]   = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="identifiers")


class Conversation(Base):
    __tablename__ = "conversations"

    id:              Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id:     Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    channel:         Mapped[str]             = mapped_column(Enum(ChannelType, name="channel_type"), nullable=False)
    subject:         Mapped[Optional[str]]   = mapped_column(Text)
    status:          Mapped[str]             = mapped_column(Enum(TicketStatus, name="ticket_status"), nullable=False, default=TicketStatus.open)
    context:         Mapped[dict]            = mapped_column(JSON, nullable=False, default=dict)
    started_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_message_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    closed_at:       Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    customer:  Mapped["Customer"]     = relationship(back_populates="conversations")
    messages:  Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    tickets:   Mapped[list["Ticket"]]  = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id:                  Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id:     Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    customer_id:         Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    direction:           Mapped[str]             = mapped_column(Enum(MessageDirection, name="message_direction"), nullable=False)
    channel:             Mapped[str]             = mapped_column(Enum(ChannelType, name="channel_type"), nullable=False)
    status:              Mapped[str]             = mapped_column(Enum(MessageStatus, name="message_status"), nullable=False, default=MessageStatus.received)
    content:             Mapped[str]             = mapped_column(Text, nullable=False)
    raw_payload:         Mapped[dict]            = mapped_column(JSON, nullable=False, default=dict)
    agent_response:      Mapped[Optional[str]]   = mapped_column(Text)
    processing_metadata: Mapped[dict]            = mapped_column(JSON, nullable=False, default=dict)
    error_details:       Mapped[Optional[dict]]  = mapped_column(JSON)
    received_at:         Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    replied_at:          Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at:          Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at:          Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    conversation: Mapped["Conversation"]        = relationship(back_populates="messages")
    customer:     Mapped["Customer"]            = relationship(back_populates="messages")
    metrics:      Mapped[list["AgentMetric"]]   = relationship(back_populates="message", cascade="all, delete-orphan")


class Ticket(Base):
    __tablename__ = "tickets"

    id:              Mapped[uuid.UUID]          = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID]          = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    customer_id:     Mapped[uuid.UUID]          = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    subject:         Mapped[str]                = mapped_column(Text, nullable=False)
    description:     Mapped[Optional[str]]      = mapped_column(Text)
    category:        Mapped[Optional[str]]      = mapped_column(Text)
    status:          Mapped[str]                = mapped_column(Enum(TicketStatus, name="ticket_status"), nullable=False, default=TicketStatus.open)
    priority:        Mapped[str]                = mapped_column(Enum(TicketPriority, name="ticket_priority"), nullable=False, default=TicketPriority.medium)
    assigned_to:     Mapped[Optional[str]]      = mapped_column(Text)
    resolution:      Mapped[Optional[str]]      = mapped_column(Text)
    tags:            Mapped[list[str]]          = mapped_column(ARRAY(Text), nullable=False, default=list)
    metadata_:       Mapped[dict]               = mapped_column("metadata", JSON, nullable=False, default=dict)
    escalated_at:    Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_at:       Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    due_at:          Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at:      Mapped[datetime]           = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at:      Mapped[datetime]           = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    conversation: Mapped["Conversation"]      = relationship(back_populates="tickets")
    customer:     Mapped["Customer"]          = relationship(back_populates="tickets")
    metrics:      Mapped[list["AgentMetric"]] = relationship(back_populates="ticket")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id:         Mapped[uuid.UUID]        = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title:      Mapped[str]              = mapped_column(Text, nullable=False)
    content:    Mapped[str]              = mapped_column(Text, nullable=False)
    category:   Mapped[Optional[str]]   = mapped_column(Text)
    tags:       Mapped[list[str]]       = mapped_column(ARRAY(Text), nullable=False, default=list)
    embedding:  Mapped[Optional[list]]  = mapped_column(Vector(1536))
    metadata_:  Mapped[dict]            = mapped_column("metadata", JSON, nullable=False, default=dict)
    is_active:  Mapped[bool]            = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ChannelConfig(Base):
    __tablename__ = "channel_configs"

    id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel:     Mapped[str]       = mapped_column(Enum(ChannelType, name="channel_type"), nullable=False, unique=True)
    is_active:   Mapped[bool]      = mapped_column(Boolean, nullable=False, default=True)
    config:      Mapped[dict]      = mapped_column(JSON, nullable=False, default=dict)
    rate_limit:  Mapped[int]       = mapped_column(Integer, nullable=False, default=100)
    created_at:  Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at:  Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class AgentMetric(Base):
    __tablename__ = "agent_metrics"

    id:                Mapped[uuid.UUID]        = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id:        Mapped[uuid.UUID]        = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    ticket_id:         Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="SET NULL"))
    model:             Mapped[str]              = mapped_column(Text, nullable=False)
    prompt_tokens:     Mapped[int]              = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int]              = mapped_column(Integer, nullable=False, default=0)
    total_tokens:      Mapped[int]              = mapped_column(Integer, nullable=False, default=0)
    latency_ms:        Mapped[int]              = mapped_column(Integer, nullable=False, default=0)
    tools_called:      Mapped[list[str]]        = mapped_column(ARRAY(Text), nullable=False, default=list)
    confidence_score:  Mapped[Optional[float]]  = mapped_column(Numeric(4, 3))
    was_escalated:     Mapped[bool]             = mapped_column(Boolean, nullable=False, default=False)
    escalation_reason: Mapped[Optional[str]]    = mapped_column(Text)
    metadata_:         Mapped[dict]             = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at:        Mapped[datetime]         = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    message: Mapped["Message"]         = relationship(back_populates="metrics")
    ticket:  Mapped[Optional["Ticket"]] = relationship(back_populates="metrics")
