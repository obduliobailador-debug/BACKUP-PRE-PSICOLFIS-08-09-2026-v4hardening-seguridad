"""All Pydantic request/response models used by the API."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


class CheckoutRequest(BaseModel):
    agent_id: str
    origin_url: str


class BudgetRequest(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = ""
    plan: str
    agente: Optional[str] = ""
    mensaje: Optional[str] = ""
    captcha_token: str
    captcha_answer: str
    # Honeypot: real users must leave this empty; bots tend to fill every field
    website: Optional[str] = ""


class ReviewCreate(BaseModel):
    author: str
    rating: int = Field(ge=1, le=5)
    text: str
    role: Optional[str] = ""  # "Fisioterapeuta", "Dueño de cafetería"...
    captcha_token: str
    captcha_answer: str
    website: Optional[str] = ""  # honeypot


class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    agent_id: str
    amount: float
    currency: str
    payment_status: str
    metadata: Dict[str, str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AccessGenerateRequest(BaseModel):
    customer_email: EmailStr
    customer_name: Optional[str] = ""
    agent_id: str
    level: str = "full"  # "demo" or "full"
    days_valid: Optional[int] = None


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class MarkReadRequest(BaseModel):
    read: bool = True


class ReviewModerationRequest(BaseModel):
    approved: bool


class AdminAccessLinkRequest(BaseModel):
    customer_email: EmailStr
    customer_name: Optional[str] = ""
    agent_id: str
    level: str = "full"  # "demo" or "full"
    days_valid: Optional[int] = None
    send_email: bool = True

    @field_validator("level")
    @classmethod
    def _validate_level(cls, v: str) -> str:
        v = (v or "full").lower().strip()
        if v not in ("demo", "full"):
            raise ValueError("level debe ser 'demo' o 'full'")
        return v


class SectorMetric(BaseModel):
    label: str
    value: str


class SectorUpsertRequest(BaseModel):
    slug: str
    name: str
    icon: Optional[str] = ""
    tagline: Optional[str] = ""
    headline: Optional[str] = ""
    description: Optional[str] = ""
    problem: Optional[str] = ""
    solution: Optional[str] = ""
    ideal_for: Optional[str] = ""
    demo_intro: Optional[str] = ""
    use_cases: List[str] = []
    metrics: List[SectorMetric] = []
    deployment_id: Optional[str] = ""
    hidden: bool = False


class SectorVisibilityRequest(BaseModel):
    hidden: bool
