"""
Pydantic Models for Authorized Phishing Simulation
===================================================
FOR AUTHORIZED USE ONLY - This module defines strict data validation models
for email targets, simulation configuration, and campaign metadata.

All user-supplied data passes through these models before any processing occurs.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class ScenarioType(str, Enum):
    """Supported phishing simulation scenario types."""
    IT_PASSWORD_RESET = "it_password_reset"
    HR_BONUS_ANNOUNCEMENT = "hr_bonus_announcement"
    URGENT_INVOICE = "urgent_invoice"
    CUSTOM = "custom"


class EmailTarget(BaseModel):
    """
    Represents a single simulation target.
    All fields are validated before the target is accepted into the pipeline.
    """
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    position: str = Field(default="Employee", max_length=150)
    department: str = Field(default="General", max_length=150)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        """Remove leading/trailing whitespace from names."""
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize email to lowercase."""
        return value.lower().strip()

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def domain(self) -> str:
        """Extract the domain portion of the email address."""
        return self.email.split("@")[1]


class SMTPConfig(BaseModel):
    """SMTP server configuration with validation."""
    host: str = Field(..., min_length=1)
    port: int = Field(default=587, ge=1, le=65535)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    use_tls: bool = Field(default=True)
    sender_address: EmailStr
    sender_name: str = Field(default="IT Security Team")


class RateLimitConfig(BaseModel):
    """Rate limiting settings to prevent email flooding."""
    delay_seconds: int = Field(default=5, ge=1, le=300)
    max_emails_per_run: int = Field(default=50, ge=1, le=1000)


class CompanyInfo(BaseModel):
    """Company metadata injected into email templates."""
    name: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1)
    support_email: EmailStr
    it_department: str = Field(default="IT Department")


class SimulationConfig(BaseModel):
    """Top-level simulation configuration."""
    campaign_name: str = Field(..., min_length=1, max_length=200)
    watermark_text: str = Field(
        default="[SECURITY SIMULATION TEST - DO NOT PANIC]"
    )
    log_file: str = Field(default="logs/simulation_log.json")
    dry_run: bool = Field(default=True)


class CampaignConfig(BaseModel):
    """
    Complete campaign configuration combining all sub-configs.
    This is the root model loaded from config.yaml.
    """
    smtp: SMTPConfig
    authorized_domains: list[str] = Field(..., min_length=1)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    simulation: SimulationConfig
    company: CompanyInfo

    @field_validator("authorized_domains")
    @classmethod
    def normalize_domains(cls, domains: list[str]) -> list[str]:
        """Normalize all authorized domains to lowercase."""
        normalized = [d.lower().strip() for d in domains if d.strip()]
        if not normalized:
            raise ValueError("At least one authorized domain must be specified.")
        return normalized


class EmailLogEntry(BaseModel):
    """Structured log entry for each email send attempt."""
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
    campaign_name: str
    target_email: str
    target_name: str
    scenario: str
    status: str  # "success", "failed", "skipped", "dry_run"
    error_message: Optional[str] = None
    watermark_applied: bool = True
    domain_validated: bool = False
