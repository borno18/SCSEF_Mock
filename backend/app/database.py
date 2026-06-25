import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.config import DATABASE_URL
from backend.app.models import Base, Ticket, Classification

logger = logging.getLogger("queuestorm")

# Set up async engine with pooled connections
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False
}
if DATABASE_URL.startswith("postgresql"):
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    DATABASE_URL,
    **engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def init_db():
    """Create database tables if they do not exist. Useful for a fresh container startup."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}", exc_info=True)

async def persist_classification(
    ticket_id: str,
    channel: str | None,
    locale: str | None,
    message: str,
    case_type: str,
    severity: str,
    department: str,
    agent_summary: str,
    human_review_required: bool,
    confidence: float,
    classifier_source: str,
    latency_ms: int
):
    """Asynchronously persist ticket and classification records to the database."""
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                ticket = Ticket(
                    ticket_id=ticket_id,
                    channel=channel,
                    locale=locale,
                    message=message
                )
                session.add(ticket)
                # Flush to populate ticket.id for foreign key reference
                await session.flush()

                classification = Classification(
                    ticket_fk=ticket.id,
                    case_type=case_type,
                    severity=severity,
                    department=department,
                    agent_summary=agent_summary,
                    human_review_required=human_review_required,
                    confidence=confidence,
                    classifier_source=classifier_source,
                    latency_ms=latency_ms
                )
                session.add(classification)
            logger.info(f"Successfully persisted classification audit log for ticket {ticket_id}")
        except Exception as e:
            logger.error(f"Error persisting classification for ticket {ticket_id}: {e}", exc_info=True)
