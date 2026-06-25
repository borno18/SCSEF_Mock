from typing import Optional, Literal
from pydantic import BaseModel, Field

# Request Model
class SortTicketRequest(BaseModel):
    ticket_id: str = Field(..., description="Unique ID for the ticket")
    channel: Optional[Literal['app', 'sms', 'call_center', 'merchant_portal']] = Field(
        None, description="Support channel"
    )
    locale: Optional[Literal['bn', 'en', 'mixed']] = Field(
        None, description="Locale language of the ticket message"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The customer message text (must not be empty or exceed 4000 characters)"
    )

# Response Model
class SortTicketResponse(BaseModel):
    ticket_id: str
    case_type: str
    severity: str
    department: str
    agent_summary: str
    human_review_required: bool
    confidence: float

# Structured Output Schema for OpenAI
class OpenAIClassification(BaseModel):
    case_type: Literal[
        'wrong_transfer',
        'payment_failed',
        'refund_request',
        'phishing_or_social_engineering',
        'other'
    ] = Field(..., description="The category classification of the support ticket")
    severity: Literal['low', 'medium', 'high', 'critical'] = Field(
        ..., description="The severity level of the issue"
    )
    agent_summary: str = Field(
        ..., description="One or two neutral sentences summarizing the ticket context without repeating credentials"
    )
    confidence: Optional[float] = Field(
        None, description="Confidence score from 0.0 to 1.0 (defaults to 0.5 if not returned)"
    )
