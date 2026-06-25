from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=True)
    locale = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

    classifications = relationship("Classification", back_populates="ticket", cascade="all, delete-orphan")


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_fk = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    case_type = Column(String, nullable=False)
    severity = Column(String, nullable=False, index=True)
    department = Column(String, nullable=False, index=True)
    agent_summary = Column(Text, nullable=False)
    human_review_required = Column(Boolean, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    classifier_source = Column(String, nullable=False)  # 'openai' or 'rules_fallback'
    latency_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="classifications")
