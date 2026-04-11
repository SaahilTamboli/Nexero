"""Pydantic models for dashboard/domain API endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class LeadCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=100)
    name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=25)
    source: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default="cold", max_length=20)
    budget_range: Optional[str] = Field(default=None, max_length=100)
    preferred_units: List[str] = Field(default_factory=list)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=25)
    source: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=20)
    budget_range: Optional[str] = Field(default=None, max_length=100)
    preferred_units: Optional[List[str]] = None
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class FollowUpCreate(BaseModel):
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    type: str = Field(default="call", max_length=30)
    scheduled_at: datetime
    notes: Optional[str] = None


class FollowUpUpdate(BaseModel):
    status: Optional[str] = Field(default=None, max_length=20)
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class SessionCreate(BaseModel):
    session_start: str
    session_end: str
    customer_id: Optional[str] = None
    property_id: Optional[str] = None
