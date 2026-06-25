import time
import logging
from typing import Literal
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.app import config
from backend.app.database import init_db, persist_classification
from backend.app.schemas import SortTicketRequest, SortTicketResponse
from backend.app.rules import check_phishing_signals, clean_agent_summary
from backend.app.classifier import classify_ticket

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("queuestorm")

# Setup Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="QueueStorm Triage API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS Middleware
origins = [origin.strip() for origin in config.FRONTEND_ORIGIN.split(",") if origin.strip()]
if "*" in origins or not origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False if origin is wildcard
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
async def startup_event():
    """Run table setup on startup."""
    await init_db()

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Immediate health check endpoint.
    Zero external calls to guarantee response well under 10s.
    """
    return {"status": "ok"}

def derive_department(case_type: str, message: str) -> str:
    """
    Derive the department name deterministically from the case type and message context.
    Matches rules:
      - wrong_transfer, contested refund_request -> dispute_resolution
      - payment_failed                            -> payments_ops
      - phishing_or_social_engineering            -> fraud_risk
      - refund_request (non-contested), other     -> customer_support
    """
    case_type_lower = case_type.lower()
    
    if case_type_lower in ("wrong_transfer", "contested refund_request"):
        return "dispute_resolution"
    elif case_type_lower == "payment_failed":
        return "payments_ops"
    elif case_type_lower == "phishing_or_social_engineering":
        return "fraud_risk"
    elif case_type_lower == "refund_request":
        # Check if the refund request is contested (disputed)
        msg_lower = message.lower()
        dispute_keywords = ["contest", "dispute", "complain", "legal", "police", "court", "wrong", "cheat", "force", "lawyer", "scam", "fraud"]
        if any(kw in msg_lower for kw in dispute_keywords):
            return "dispute_resolution"
        return "customer_support"
    else:
        return "customer_support"

@app.post("/sort-ticket", response_model=SortTicketResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/second")
async def sort_ticket(
    payload: SortTicketRequest,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Sort and triage support tickets using rules and LLM fallback paths.
    """
    start_time = time.perf_counter()
    
    ticket_id = payload.ticket_id
    channel = payload.channel
    locale = payload.locale
    message = payload.message.strip()

    # Pre-validate: check if message is empty or only whitespace
    if not message:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty or contain only whitespace."
        )

    # 1. Run message through rules-based pre-check for phishing signals
    rules_phishing_detected = check_phishing_signals(message)

    case_type = "other"
    severity = "low"
    agent_summary = "Rules-based fallback: classification could not be verified."
    confidence = 0.5
    classifier_source = "openai"

    if rules_phishing_detected:
        # Pre-check is a strong, OVERRIDING signal
        case_type = "phishing_or_social_engineering"
        severity = "critical"
        confidence = 1.0
        agent_summary = "Pre-check detected potential phishing or card credential safety risk."
        classifier_source = "rules_fallback"

    # 2. Call classify_ticket (OpenAI classification) unless we already had rule-based phishing override
    # Wait, the instruction says "Merge: if either step 1 or step 2 flags phishing/critical, the final result is phishing/critical"
    # To perform proper merge and get summary/confidence, we always try to run LLM unless it times out or errors.
    try:
        # Call LLM classification
        llm_result = await classify_ticket(message, locale)
        
        # Extract LLM values
        llm_case_type = llm_result["case_type"]
        llm_severity = llm_result["severity"]
        llm_agent_summary = llm_result["agent_summary"]
        llm_confidence = llm_result["confidence"]

        if rules_phishing_detected:
            # Overrides LLM's classification fields if rules pre-check detected phishing
            case_type = "phishing_or_social_engineering"
            severity = "critical"
            # Keep LLM summary if it is safe, else fallback
            agent_summary = llm_agent_summary
        else:
            case_type = llm_case_type
            severity = llm_severity
            agent_summary = llm_agent_summary
            confidence = llm_confidence
            classifier_source = "openai"

    except Exception as e:
        error_msg = f" (Error: {str(e)})"
        logger.warning(f"Failed to fetch or parse OpenAI classification{error_msg}. Falling back to rules-based classification.")
        classifier_source = "rules_fallback"
        # If LLM failed, we rely entirely on rules pre-check results
        if rules_phishing_detected:
            case_type = "phishing_or_social_engineering"
            severity = "critical"
            agent_summary = f"Rules-based fallback{error_msg}: critical security phishing pattern detected."
            confidence = 1.0
        else:
            case_type = "other"
            severity = "low"
            agent_summary = f"Rules-based fallback{error_msg}: ticket categorized due to classification server timeout or error."
            confidence = 0.5

    # 3. Merge flags: if either pre-check or LLM flags phishing/critical, elevate to critical phishing
    if rules_phishing_detected or case_type == "phishing_or_social_engineering" or severity == "critical":
        case_type = "phishing_or_social_engineering"
        severity = "critical"
        human_review_required = True
    else:
        human_review_required = False

    # 4. Derive department deterministically from final case_type
    department = derive_department(case_type, message)

    # 5. Post-validate summary against denylist to prevent leak of credentials
    agent_summary = clean_agent_summary(agent_summary, case_type)

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    # 6. Fire-and-forget audit logger write (added as a FastAPI background task)
    background_tasks.add_task(
        persist_classification,
        ticket_id=ticket_id,
        channel=channel,
        locale=locale,
        message=message,
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=agent_summary,
        human_review_required=human_review_required,
        confidence=confidence,
        classifier_source=classifier_source,
        latency_ms=latency_ms
    )

    # Structured logging of triage without raw message body
    logger.info(
        f"TriageResult: ticket_id={ticket_id} case_type={case_type} severity={severity} "
        f"department={department} human_review_required={human_review_required} "
        f"latency_ms={latency_ms} source={classifier_source}"
    )

    return SortTicketResponse(
        ticket_id=ticket_id,
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=agent_summary,
        human_review_required=human_review_required,
        confidence=confidence
    )
