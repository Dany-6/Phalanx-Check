"""
Template Engine & Scenario Library for Authorized Phishing Simulation
=====================================================================
FOR AUTHORIZED USE ONLY - This module manages Jinja2-based email templates
and provides a library of pre-built, realistic simulation scenarios.

All template generation happens LOCALLY — no external API calls are made.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from jinja2 import Environment, BaseLoader, TemplateSyntaxError, UndefinedError

from models import EmailTarget, CompanyInfo, ScenarioType


# ---------------------------------------------------------------------------
#  Built-in Scenario Templates (HTML)
# ---------------------------------------------------------------------------

SCENARIO_TEMPLATES: dict[str, dict[str, str]] = {
    ScenarioType.IT_PASSWORD_RESET: {
        "subject": "Action Required: Your Password Expires in 24 Hours",
        "body": """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, Helvetica, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto;">
  <div style="background: #0078D4; padding: 20px; text-align: center;">
    <h1 style="color: #fff; margin: 0; font-size: 20px;">{{ company_name }} — {{ it_department }}</h1>
  </div>
  <div style="padding: 30px 20px; background: #f9f9f9;">
    <p>Dear {{ first_name }},</p>
    <p>Our records indicate that your network password for <strong>{{ email }}</strong>
    is set to expire within the next <strong>24 hours</strong>.</p>
    <p>To avoid any interruption to your access, please update your password
    immediately by clicking the button below:</p>
    <div style="text-align: center; margin: 30px 0;">
      <a href="#simulation-link-disabled" style="background: #0078D4; color: #fff;
         padding: 14px 28px; text-decoration: none; border-radius: 5px;
         font-weight: bold; display: inline-block;">Reset Password Now</a>
    </div>
    <p style="font-size: 13px; color: #777;">If you did not request this change,
    please contact the {{ it_department }} at
    <a href="mailto:{{ support_email }}">{{ support_email }}</a>.</p>
    <p>Best regards,<br>{{ it_department }}<br>{{ company_name }}</p>
  </div>
  <div style="padding: 15px 20px; background: #eee; font-size: 11px; color: #999; text-align: center;">
    {{ watermark }}
  </div>
</body>
</html>""",
    },

    ScenarioType.HR_BONUS_ANNOUNCEMENT: {
        "subject": "Congratulations! Your Annual Bonus Has Been Approved",
        "body": """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto;">
  <div style="background: linear-gradient(135deg, #2E7D32, #43A047); padding: 20px; text-align: center;">
    <h1 style="color: #fff; margin: 0; font-size: 20px;">{{ company_name }} — Human Resources</h1>
  </div>
  <div style="padding: 30px 20px; background: #f9f9f9;">
    <p>Dear {{ first_name }} {{ last_name }},</p>
    <p>We are pleased to inform you that your <strong>annual performance bonus</strong>
    for fiscal year 2025 has been approved by management.</p>
    <p>As a <strong>{{ position }}</strong> in the <strong>{{ department }}</strong>
    department, your contribution has been outstanding.</p>
    <p>To review the details and confirm your payment preferences, please log in
    to the employee portal:</p>
    <div style="text-align: center; margin: 30px 0;">
      <a href="#simulation-link-disabled" style="background: #2E7D32; color: #fff;
         padding: 14px 28px; text-decoration: none; border-radius: 5px;
         font-weight: bold; display: inline-block;">View Bonus Details</a>
    </div>
    <p style="font-size: 13px; color: #777;">This is a confidential communication.
    Please do not forward this email.</p>
    <p>Warm regards,<br>Human Resources<br>{{ company_name }}</p>
  </div>
  <div style="padding: 15px 20px; background: #eee; font-size: 11px; color: #999; text-align: center;">
    {{ watermark }}
  </div>
</body>
</html>""",
    },

    ScenarioType.URGENT_INVOICE: {
        "subject": "URGENT: Invoice #INV-2026-4851 Requires Your Immediate Approval",
        "body": """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, Helvetica, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto;">
  <div style="background: #C62828; padding: 20px; text-align: center;">
    <h1 style="color: #fff; margin: 0; font-size: 20px;">{{ company_name }} — Accounts Payable</h1>
  </div>
  <div style="padding: 30px 20px; background: #f9f9f9;">
    <p>Dear {{ first_name }},</p>
    <p>An invoice from <strong>Consolidated Services Ltd.</strong> totaling
    <strong>$12,340.00</strong> has been flagged for your approval.</p>
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <tr style="background: #f0f0f0;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Invoice #</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">INV-2026-4851</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Amount</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">$12,340.00</td>
      </tr>
      <tr style="background: #f0f0f0;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Due Date</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Within 48 Hours</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Requested By</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Finance Department</td>
      </tr>
    </table>
    <p>Failure to approve this invoice within 48 hours may result in
    <strong>late payment penalties</strong>. Please review and approve immediately:</p>
    <div style="text-align: center; margin: 30px 0;">
      <a href="#simulation-link-disabled" style="background: #C62828; color: #fff;
         padding: 14px 28px; text-decoration: none; border-radius: 5px;
         font-weight: bold; display: inline-block;">Review Invoice</a>
    </div>
    <p style="font-size: 13px; color: #777;">If you believe this invoice was sent
    in error, contact Accounts Payable immediately.</p>
    <p>Regards,<br>Accounts Payable<br>{{ company_name }}</p>
  </div>
  <div style="padding: 15px 20px; background: #eee; font-size: 11px; color: #999; text-align: center;">
    {{ watermark }}
  </div>
</body>
</html>""",
    },
}


# ---------------------------------------------------------------------------
#  Data class for rendered output
# ---------------------------------------------------------------------------

@dataclass
class RenderedEmail:
    """Container for a fully rendered simulation email."""
    subject: str
    html_body: str
    scenario: str
    target: EmailTarget


# ---------------------------------------------------------------------------
#  Template Engine
# ---------------------------------------------------------------------------

class TemplateEngine:
    """
    Jinja2-based template engine for phishing simulation emails.

    All rendering happens locally in-process — no external calls.
    The watermark footer is ALWAYS injected and cannot be removed.
    """

    def __init__(self, company_info: CompanyInfo, watermark_text: str) -> None:
        self._env = Environment(
            loader=BaseLoader(),
            autoescape=True,
            keep_trailing_newline=True,
        )
        self._company = company_info
        self._watermark = watermark_text

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def render(
        self,
        target: EmailTarget,
        scenario: ScenarioType,
        custom_subject: Optional[str] = None,
        custom_body: Optional[str] = None,
    ) -> RenderedEmail:
        """
        Render an email for a given target and scenario.

        Parameters
        ----------
        target : EmailTarget
            Validated target information.
        scenario : ScenarioType
            Which pre-built scenario to use, or CUSTOM for user-supplied templates.
        custom_subject : str, optional
            Subject line for CUSTOM scenario.
        custom_body : str, optional
            HTML body for CUSTOM scenario (must contain {{ watermark }}).

        Returns
        -------
        RenderedEmail
            Fully rendered email ready for sending.

        Raises
        ------
        ValueError
            If scenario is CUSTOM but no subject/body provided.
        """
        if scenario == ScenarioType.CUSTOM:
            if not custom_subject or not custom_body:
                raise ValueError(
                    "Custom scenario requires both custom_subject and custom_body."
                )
            subject_template = custom_subject
            body_template = custom_body
        else:
            template_data = SCENARIO_TEMPLATES[scenario]
            subject_template = template_data["subject"]
            body_template = template_data["body"]

        context = self._build_context(target)

        rendered_subject = self._render_string(subject_template, context)
        rendered_body = self._render_string(body_template, context)

        # Safety: guarantee watermark is present even if template omits it
        if self._watermark not in rendered_body:
            rendered_body += self._fallback_watermark_html()

        return RenderedEmail(
            subject=rendered_subject,
            html_body=rendered_body,
            scenario=scenario.value,
            target=target,
        )

    def list_scenarios(self) -> list[str]:
        """Return names of all available built-in scenarios."""
        return [s.value for s in ScenarioType if s != ScenarioType.CUSTOM]

    # ------------------------------------------------------------------
    #  Internals
    # ------------------------------------------------------------------

    def _build_context(self, target: EmailTarget) -> dict:
        """Assemble the Jinja2 template context from target + company info."""
        return {
            "first_name": target.first_name,
            "last_name": target.last_name,
            "full_name": target.full_name,
            "email": target.email,
            "position": target.position,
            "department": target.department,
            "company_name": self._company.name,
            "company_domain": self._company.domain,
            "support_email": self._company.support_email,
            "it_department": self._company.it_department,
            "watermark": self._watermark,
        }

    def _render_string(self, template_str: str, context: dict) -> str:
        """Render a Jinja2 template string with the given context."""
        try:
            template = self._env.from_string(template_str)
            return template.render(**context)
        except (TemplateSyntaxError, UndefinedError) as exc:
            raise ValueError(f"Template rendering failed: {exc}") from exc

    def _fallback_watermark_html(self) -> str:
        """Generate a fallback watermark block if the template forgot it."""
        return (
            f'\n<div style="padding:15px 20px;background:#eee;font-size:11px;'
            f'color:#999;text-align:center;">{self._watermark}</div>'
        )
