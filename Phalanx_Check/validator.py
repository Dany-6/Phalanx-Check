"""
Domain Whitelisting & Safety Validator
======================================
FOR AUTHORIZED USE ONLY - This module is the GATEKEEPER.
No email can be sent without passing through this validator first.
"""

from __future__ import annotations

import logging
from typing import Optional

from models import EmailTarget, CampaignConfig

logger = logging.getLogger("phish_sim.validator")


class ValidationError(Exception):
    """Raised when a safety or domain validation check fails."""

    def __init__(self, message: str, target_email: Optional[str] = None):
        self.target_email = target_email
        super().__init__(message)


class DomainValidator:
    """
    Strict domain whitelisting validator — the primary safety mechanism.
    Must be called before every send attempt.
    """

    def __init__(self, config: CampaignConfig) -> None:
        self._authorized_domains: frozenset[str] = frozenset(
            d.lower() for d in config.authorized_domains
        )
        self._watermark: str = config.simulation.watermark_text
        logger.info(
            "DomainValidator initialized | Authorized domains: %s",
            sorted(self._authorized_domains),
        )

    def validate_target(self, target: EmailTarget) -> None:
        """Validate target domain is in the whitelist. Raises ValidationError."""
        domain = target.domain.lower()
        if domain not in self._authorized_domains:
            msg = (
                f"BLOCKED: '{target.email}' domain '{domain}' is NOT authorized. "
                f"Allowed: {sorted(self._authorized_domains)}"
            )
            logger.error(msg)
            raise ValidationError(msg, target_email=target.email)
        logger.debug("Domain validated: %s [OK]", target.email)

    def validate_email_body(self, html_body: str) -> None:
        """Verify watermark is present in the email body."""
        if self._watermark not in html_body:
            msg = f"BLOCKED: Watermark '{self._watermark}' missing from email body."
            logger.error(msg)
            raise ValidationError(msg)
        logger.debug("Watermark validation passed [OK]")

    def validate_batch(
        self, targets: list[EmailTarget]
    ) -> tuple[list[EmailTarget], list[dict]]:
        """Validate a batch. Returns (valid_targets, error_reports)."""
        valid: list[EmailTarget] = []
        errors: list[dict] = []
        for target in targets:
            try:
                self.validate_target(target)
                valid.append(target)
            except ValidationError as exc:
                errors.append({
                    "email": target.email,
                    "name": target.full_name,
                    "error": str(exc),
                })
        logger.info(
            "Batch validation: %d valid, %d rejected / %d total",
            len(valid), len(errors), len(targets),
        )
        return valid, errors

    @property
    def authorized_domains(self) -> frozenset[str]:
        return self._authorized_domains
