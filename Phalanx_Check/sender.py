"""
SMTP Sender with Rate Limiting & Safety Watermarking
=====================================================
FOR AUTHORIZED USE ONLY - Handles the actual email delivery with
mandatory rate limiting, watermark enforcement, and comprehensive logging.
"""

from __future__ import annotations

import json
import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from models import CampaignConfig, EmailLogEntry, EmailTarget
from templates import RenderedEmail
from validator import DomainValidator, ValidationError

logger = logging.getLogger("phish_sim.sender")


class SimulationSender:
    """
    Email sender for phishing simulations with built-in safety controls.

    Safety features:
    - Rate limiting via time.sleep() between sends
    - Domain validation before every send
    - Watermark verification before every send
    - Comprehensive JSON logging of all attempts
    - Dry-run mode for testing without actual sends
    """

    def __init__(
        self, config: CampaignConfig, validator: DomainValidator
    ) -> None:
        self._config = config
        self._validator = validator
        self._smtp_cfg = config.smtp
        self._rate_delay = config.rate_limit.delay_seconds
        self._max_emails = config.rate_limit.max_emails_per_run
        self._dry_run = config.simulation.dry_run
        self._log_file = Path(config.simulation.log_file)
        self._sent_count = 0

        # Ensure log directory exists
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "SimulationSender initialized | dry_run=%s | rate_limit=%ds | max=%d",
            self._dry_run, self._rate_delay, self._max_emails,
        )

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def send_email(self, rendered: RenderedEmail) -> EmailLogEntry:
        """
        Send a single simulation email with all safety checks.

        Returns an EmailLogEntry regardless of success or failure.
        """
        target = rendered.target
        log_entry = EmailLogEntry(
            campaign_name=self._config.simulation.campaign_name,
            target_email=target.email,
            target_name=target.full_name,
            scenario=rendered.scenario,
            status="pending",
        )

        # --- Safety Gate 1: Domain validation ---
        try:
            self._validator.validate_target(target)
            log_entry.domain_validated = True
        except ValidationError as exc:
            log_entry.status = "failed"
            log_entry.error_message = str(exc)
            log_entry.domain_validated = False
            self._write_log(log_entry)
            return log_entry

        # --- Safety Gate 2: Watermark verification ---
        try:
            self._validator.validate_email_body(rendered.html_body)
            log_entry.watermark_applied = True
        except ValidationError as exc:
            log_entry.status = "failed"
            log_entry.error_message = str(exc)
            log_entry.watermark_applied = False
            self._write_log(log_entry)
            return log_entry

        # --- Safety Gate 3: Rate limit check ---
        if self._sent_count >= self._max_emails:
            log_entry.status = "skipped"
            log_entry.error_message = (
                f"Max emails per run ({self._max_emails}) reached."
            )
            self._write_log(log_entry)
            return log_entry

        # --- Dry-run mode ---
        if self._dry_run:
            log_entry.status = "dry_run"
            logger.info(
                "[DRY RUN] Would send to %s | Subject: %s",
                target.email, rendered.subject,
            )
            self._write_log(log_entry)
            self._sent_count += 1
            return log_entry

        # --- Actual send ---
        try:
            self._smtp_send(rendered)
            log_entry.status = "success"
            logger.info("Email sent to %s [OK]", target.email)
        except Exception as exc:
            log_entry.status = "failed"
            log_entry.error_message = f"SMTP error: {exc}"
            logger.error("SMTP send failed for %s: %s", target.email, exc)

        self._write_log(log_entry)
        self._sent_count += 1

        # --- Rate limiting delay ---
        if self._rate_delay > 0:
            logger.debug("Rate limiting: sleeping %ds...", self._rate_delay)
            time.sleep(self._rate_delay)

        return log_entry

    def send_batch(
        self, emails: list[RenderedEmail]
    ) -> list[EmailLogEntry]:
        """Send a batch of rendered emails with rate limiting."""
        results: list[EmailLogEntry] = []
        total = len(emails)

        logger.info("Starting batch send: %d emails", total)

        for idx, rendered in enumerate(emails, start=1):
            logger.info(
                "Processing %d/%d: %s", idx, total, rendered.target.email
            )
            entry = self.send_email(rendered)
            results.append(entry)

            if entry.status == "skipped":
                logger.warning("Batch halted: rate limit reached.")
                break

        # Summary
        statuses = {}
        for r in results:
            statuses[r.status] = statuses.get(r.status, 0) + 1
        logger.info("Batch complete: %s", statuses)

        return results

    @property
    def sent_count(self) -> int:
        return self._sent_count

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _smtp_send(self, rendered: RenderedEmail) -> None:
        """Construct MIME message and send via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["From"] = (
            f"{self._smtp_cfg.sender_name} <{self._smtp_cfg.sender_address}>"
        )
        msg["To"] = rendered.target.email
        msg["Subject"] = rendered.subject
        msg["X-Simulation"] = "Authorized-Phishing-Test"

        # Attach HTML body
        msg.attach(MIMEText(rendered.html_body, "html", "utf-8"))

        # Connect and send
        if self._smtp_cfg.use_tls:
            with smtplib.SMTP(
                self._smtp_cfg.host, self._smtp_cfg.port, timeout=30
            ) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(
                    self._smtp_cfg.username, self._smtp_cfg.password
                )
                server.send_message(msg)
        else:
            with smtplib.SMTP(
                self._smtp_cfg.host, self._smtp_cfg.port, timeout=30
            ) as server:
                server.ehlo()
                server.login(
                    self._smtp_cfg.username, self._smtp_cfg.password
                )
                server.send_message(msg)

    def _write_log(self, entry: EmailLogEntry) -> None:
        """Append a log entry to the JSON log file."""
        try:
            existing: list[dict] = []
            if self._log_file.exists() and self._log_file.stat().st_size > 0:
                with open(self._log_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            existing.append(entry.model_dump())

            with open(self._log_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

        except Exception as exc:
            logger.error("Failed to write log entry: %s", exc)
