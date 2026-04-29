"""
Authorized Phishing Simulation — Main Entry Point
==================================================
FOR AUTHORIZED USE ONLY - This tool is designed exclusively for corporate
security teams running authorized, ethical phishing simulations.

Unauthorized use of this tool is strictly prohibited and may violate
applicable laws and regulations.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from models import (
    CampaignConfig,
    EmailTarget,
    ScenarioType,
)
from templates import TemplateEngine
from validator import DomainValidator, ValidationError
from sender import SimulationSender


# ---------------------------------------------------------------------------
#  Logging setup
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """Configure structured logging for the simulation."""
    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/simulation.log", encoding="utf-8"),
        ],
    )


# ---------------------------------------------------------------------------
#  Configuration loader
# ---------------------------------------------------------------------------

def load_config(config_path: str = "config.yaml") -> CampaignConfig:
    """
    Load configuration from YAML file, with env-var overrides for secrets.

    Environment variables take precedence over config.yaml values:
      - SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS
    """
    load_dotenv()  # Load .env file if present

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Override SMTP settings from environment variables
    smtp = raw.get("smtp", {})
    smtp["host"] = os.getenv("SMTP_HOST", smtp.get("host", ""))
    smtp["port"] = int(os.getenv("SMTP_PORT", smtp.get("port", 587)))
    smtp["username"] = os.getenv("SMTP_USERNAME", smtp.get("username", ""))
    smtp["password"] = os.getenv("SMTP_PASSWORD", smtp.get("password", ""))
    smtp["use_tls"] = os.getenv("SMTP_USE_TLS", str(smtp.get("use_tls", True))).lower() in ("true", "1", "yes")
    raw["smtp"] = smtp

    return CampaignConfig(**raw)


# ---------------------------------------------------------------------------
#  Target loaders
# ---------------------------------------------------------------------------

def load_targets_from_csv(csv_path: str) -> list[EmailTarget]:
    """
    Load simulation targets from a CSV file.

    Expected CSV columns:
      email, first_name, last_name, position (optional), department (optional)

    Parameters
    ----------
    csv_path : str
        Path to the CSV file containing target information.

    Returns
    -------
    list[EmailTarget]
        Validated list of email targets.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If the CSV is empty or has missing required columns.
    """
    logger = logging.getLogger("phish_sim.main")
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"Targets CSV file not found: {csv_path}")

    targets: list[EmailTarget] = []
    errors: list[str] = []

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Validate required columns
        if reader.fieldnames is None:
            raise ValueError(f"CSV file '{csv_path}' is empty or has no header row.")

        required = {"email", "first_name", "last_name"}
        actual = {col.strip().lower() for col in reader.fieldnames}
        missing = required - actual
        if missing:
            raise ValueError(
                f"CSV is missing required columns: {missing}. "
                f"Found: {reader.fieldnames}"
            )

        for line_num, row in enumerate(reader, start=2):
            try:
                # Normalize keys to lowercase and strip whitespace
                clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if v}
                targets.append(EmailTarget(
                    email=clean_row["email"],
                    first_name=clean_row["first_name"],
                    last_name=clean_row["last_name"],
                    position=clean_row.get("position", "Employee"),
                    department=clean_row.get("department", "General"),
                ))
            except Exception as exc:
                errors.append(f"  Line {line_num}: {exc}")

    if errors:
        logger.warning("Some CSV rows had errors:")
        for err in errors:
            logger.warning(err)

    if not targets:
        raise ValueError(f"No valid targets found in '{csv_path}'.")

    logger.info("Loaded %d target(s) from '%s'", len(targets), csv_path)
    return targets


# Demo targets for testing (used when no CSV is provided)
DEMO_TARGETS = [
    EmailTarget(
        email="john.doe@yourcompany.com",
        first_name="John",
        last_name="Doe",
        position="Software Engineer",
        department="Engineering",
    ),
    EmailTarget(
        email="jane.smith@yourcompany.com",
        first_name="Jane",
        last_name="Smith",
        position="Marketing Manager",
        department="Marketing",
    ),
    EmailTarget(
        email="bob.wilson@yourcompany.com",
        first_name="Bob",
        last_name="Wilson",
        position="Finance Analyst",
        department="Finance",
    ),
    # This target should be BLOCKED by the domain validator:
    EmailTarget(
        email="external.user@gmail.com",
        first_name="External",
        last_name="User",
        position="Unknown",
        department="N/A",
    ),
]


# ---------------------------------------------------------------------------
#  Main simulation runner
# ---------------------------------------------------------------------------

def run_simulation(
    config: CampaignConfig,
    targets: list[EmailTarget],
    scenario: ScenarioType = ScenarioType.IT_PASSWORD_RESET,
) -> None:
    """
    Execute a full phishing simulation campaign.

    Steps:
    1. Initialize validator, template engine, and sender.
    2. Validate all targets against the domain whitelist.
    3. Render emails for valid targets.
    4. Send (or dry-run) emails with rate limiting.
    5. Print summary report.
    """
    logger = logging.getLogger("phish_sim.main")

    # --- Banner ---
    logger.info("=" * 70)
    logger.info("  AUTHORIZED PHISHING SIMULATION TOOL")
    logger.info("  Campaign: %s", config.simulation.campaign_name)
    logger.info("  Mode: %s", "DRY RUN" if config.simulation.dry_run else "LIVE")
    logger.info("  Scenario: %s", scenario.value)
    logger.info("=" * 70)

    # --- Initialize components ---
    validator = DomainValidator(config)
    engine = TemplateEngine(config.company, config.simulation.watermark_text)
    sender = SimulationSender(config, validator)

    # --- Step 1: Batch validate targets ---
    logger.info("Validating %d targets...", len(targets))
    valid_targets, validation_errors = validator.validate_batch(targets)

    if validation_errors:
        logger.warning(
            "%d target(s) REJECTED by domain whitelist:", len(validation_errors)
        )
        for err in validation_errors:
            logger.warning("  [X] %s - %s", err["email"], err["error"])

    if not valid_targets:
        logger.error("No valid targets remaining. Aborting simulation.")
        return

    logger.info("%d target(s) passed validation.", len(valid_targets))

    # --- Step 2: Render emails ---
    rendered_emails = []
    for target in valid_targets:
        try:
            rendered = engine.render(target, scenario)
            rendered_emails.append(rendered)
            logger.info("  [+] Rendered email for %s", target.email)
        except ValueError as exc:
            logger.error("  [X] Render failed for %s: %s", target.email, exc)

    if not rendered_emails:
        logger.error("No emails rendered. Aborting simulation.")
        return

    # --- Step 3: Send emails ---
    results = sender.send_batch(rendered_emails)

    # --- Step 4: Summary report ---
    logger.info("")
    logger.info("=" * 70)
    logger.info("  SIMULATION SUMMARY")
    logger.info("=" * 70)
    status_counts: dict[str, int] = {}
    for r in results:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1

    for status, count in sorted(status_counts.items()):
        logger.info("  %-12s: %d", status.upper(), count)

    logger.info("  %-12s: %d", "REJECTED", len(validation_errors))
    logger.info("  %-12s: %d", "TOTAL", len(targets))
    logger.info("=" * 70)
    logger.info(
        "  Log file: %s", config.simulation.log_file
    )
    logger.info("=" * 70)


# ---------------------------------------------------------------------------
#  CLI Entry Point
# ---------------------------------------------------------------------------

USAGE = """
USAGE:
  python main.py [config.yaml] [scenario] [targets.csv]

ARGUMENTS:
  config.yaml    Path to configuration file     (default: config.yaml)
  scenario       Simulation scenario to use      (default: it_password_reset)
  targets.csv    Path to CSV file with targets   (default: uses demo targets)

SCENARIOS:
  it_password_reset      - Fake IT password expiry notice
  hr_bonus_announcement  - Fake HR bonus notification
  urgent_invoice         - Fake urgent invoice approval

EXAMPLES:
  python main.py                                          # Dry-run with demo targets
  python main.py config.yaml it_password_reset targets.csv  # Full run with CSV
  python main.py config.yaml hr_bonus_announcement          # Demo with different scenario
"""


def main() -> None:
    """Main entry point for the phishing simulation tool."""
    setup_logging()
    logger = logging.getLogger("phish_sim.main")

    # Show help
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "help"):
        print(USAGE)
        sys.exit(0)

    logger.info("=" * 70)
    logger.info("  [!] AUTHORIZED USE ONLY [!]")
    logger.info("  This tool is for authorized security awareness training.")
    logger.info("  Unauthorized use is strictly prohibited.")
    logger.info("=" * 70)

    try:
        # Load configuration
        config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        logger.info("Loading configuration from: %s", config_path)
        config = load_config(config_path)

        # Select scenario
        scenario_arg = sys.argv[2] if len(sys.argv) > 2 else "it_password_reset"
        try:
            scenario = ScenarioType(scenario_arg)
        except ValueError:
            logger.error(
                "Unknown scenario '%s'. Available: %s",
                scenario_arg,
                [s.value for s in ScenarioType if s != ScenarioType.CUSTOM],
            )
            sys.exit(1)

        # Load targets: from CSV if provided, otherwise use demo targets
        csv_path = sys.argv[3] if len(sys.argv) > 3 else None
        if csv_path:
            logger.info("Loading targets from CSV: %s", csv_path)
            targets = load_targets_from_csv(csv_path)
        else:
            logger.info("No CSV provided -- using built-in demo targets.")
            targets = DEMO_TARGETS

        # Run simulation
        run_simulation(config, targets, scenario)

    except FileNotFoundError as exc:
        logger.error("Configuration error: %s", exc)
        sys.exit(1)
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected error during simulation: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
