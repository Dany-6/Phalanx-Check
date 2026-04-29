<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Status-Working-brightgreen?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/Type-CLI_Tool-blue?style=for-the-badge" alt="CLI">
</p>

# Phalanx Check

### Authorized Phishing Email Simulation Tool for Security Awareness Training

> **Disclaimer:** This tool is built strictly for **authorized, ethical phishing simulations** conducted by corporate security teams or for educational/academic purposes. Unauthorized use is strictly prohibited and may violate applicable laws.

---

## Table of Contents

- [About The Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Available Scenarios](#available-scenarios)
- [Sample Output](#sample-output)
- [Safety Mechanisms](#safety-mechanisms)
- [License](#license)

---

## About The Project

**Phalanx Check** is a Python-based CLI (Command Line Interface) tool that enables security teams to run controlled, internal phishing simulations. It helps organizations test and improve employee awareness against social engineering attacks.

The tool generates realistic but harmless phishing emails using customizable templates, sends them only to **whitelisted internal domains**, and logs every action for full auditability. Every email is watermarked with a visible safety disclaimer so recipients know it is a test.

### Why "Phalanx Check"?

A **phalanx** was an ancient Greek military formation — a wall of shields protecting against attack. This tool **checks** whether your organization's human phalanx (your employees) can recognize and resist phishing threats.

---

## Features

| Feature | Description |
|---------|-------------|
| **Template Engine** | Jinja2-based engine with variable injection (`{{first_name}}`, `{{company_name}}`, `{{position}}`, etc.) |
| **3 Built-in Scenarios** | IT Password Reset, HR Bonus Announcement, Urgent Invoice — realistic but harmless |
| **Domain Whitelisting** | Strict validation — only pre-approved internal domains are allowed. External emails are **blocked and logged** |
| **Safety Watermark** | Every email auto-appends: `[SECURITY SIMULATION TEST - DO NOT PANIC]` |
| **Rate Limiting** | Built-in `time.sleep()` delay between sends to prevent mail server flooding |
| **Dry-Run Mode** | Test the entire pipeline without sending any real emails |
| **CSV Target Import** | Load employee targets from a CSV file instead of hardcoding |
| **JSON Audit Logging** | Every attempt (success/failure/blocked) is logged to `simulation_log.json` |
| **Env-Based Secrets** | SMTP credentials stored in `.env` file — never hardcoded, never uploaded to Git |
| **Pydantic Validation** | All input data is strictly validated using Pydantic models before processing |

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.9+** | Core language |
| **Jinja2** | HTML email template rendering |
| **Pydantic** | Data validation and configuration models |
| **PyYAML** | Configuration file parsing |
| **python-dotenv** | Environment variable management |
| **smtplib** | SMTP email delivery (Python standard library) |
| **email.mime** | MIME message construction (Python standard library) |

---

## Project Structure

```
phalanx-check/
│
├── config.yaml            # Campaign settings, SMTP config, domain whitelist
├── .env.example           # Template for SMTP credentials (copy to .env)
├── .gitignore             # Ensures .env and logs are not uploaded to Git
├── requirements.txt       # Python dependencies
├── targets.csv            # Sample target list (CSV format)
├── README.md              # This file
│
├── models.py              # Pydantic models for data validation
├── templates.py           # Jinja2 template engine & scenario library
├── validator.py           # Domain whitelisting & safety gatekeeper
├── sender.py              # SMTP sender with rate limiting & audit logging
├── main.py                # CLI entry point — ties everything together
│
└── logs/                  # Auto-generated at runtime
    ├── simulation.log         # Human-readable execution log
    └── simulation_log.json    # Structured JSON audit trail
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        PHALANX CHECK                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   config.yaml ──► CampaignConfig (Pydantic) ──► DomainValidator  │
│   .env           (validates all settings)       (gatekeeper)     │
│                                                      │           │
│   targets.csv ──► EmailTarget (Pydantic) ────────────┤           │
│                   (validates each target)             │           │
│                                                      ▼           │
│                  TemplateEngine (Jinja2) ──► SimulationSender     │
│                  (renders HTML emails)       (SMTP + logging)    │
│                                                      │           │
│                                                      ▼           │
│                                              logs/               │
│                                              simulation_log.json │
└──────────────────────────────────────────────────────────────────┘
```

**Safety Pipeline (every email must pass all 3 gates):**

```
Target Email
    │
    ▼
[Gate 1] Domain Whitelist Check ── FAIL ──► BLOCKED & Logged
    │
   PASS
    │
    ▼
[Gate 2] Watermark Verification ── FAIL ──► BLOCKED & Logged
    │
   PASS
    │
    ▼
[Gate 3] Rate Limit Check ──────── FAIL ──► SKIPPED & Logged
    │
   PASS
    │
    ▼
Send Email (or Dry-Run) ──────────────────► Logged to JSON
```

---

## Prerequisites

- **Python 3.9 or higher** installed on your system
- **pip** (Python package manager)
- An **SMTP server** for sending emails (Gmail, company mail server, etc.)

Check your Python version:
```bash
python --version
```

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/phalanx-check.git
cd phalanx-check
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `jinja2` — template rendering
- `pydantic[email]` — data validation with email support
- `pyyaml` — YAML config parsing
- `python-dotenv` — .env file support

---

## Configuration

### Step 1: Set Up SMTP Credentials

Copy the example environment file and fill in your **real SMTP credentials**:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Edit `.env` with your SMTP details:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your_app_password_here
SMTP_USE_TLS=true
```

> **Important:** The `.env` file is listed in `.gitignore` and will **NOT** be uploaded to GitHub. Your credentials stay local.

> **Gmail Users:** You need to generate an [App Password](https://myaccount.google.com/apppasswords) — your regular Gmail password won't work with SMTP.

### Step 2: Edit Campaign Settings

Open `config.yaml` and update these fields:

```yaml
# Set your organization's authorized email domains
authorized_domains:
  - "yourcompany.com"       # Change to your real domain

# Set the sender identity
smtp:
  sender_address: "security-team@yourcompany.com"
  sender_name: "IT Security Team"

# Company info (appears in email templates)
company:
  name: "Your Company Name"
  domain: "yourcompany.com"
  support_email: "helpdesk@yourcompany.com"
  it_department: "IT Department"

# Keep dry_run: true until you're ready to send real emails
simulation:
  dry_run: true    # Change to false for live sending
```

### Step 3: Prepare Your Target List

Edit `targets.csv` with the employees you want to test:

```csv
email,first_name,last_name,position,department
alice.johnson@yourcompany.com,Alice,Johnson,Product Manager,Product
bob.smith@yourcompany.com,Bob,Smith,Developer,Engineering
carol.davis@yourcompany.com,Carol,Davis,HR Specialist,Human Resources
```

**Required columns:** `email`, `first_name`, `last_name`
**Optional columns:** `position`, `department`

---

## Usage

### Quick Start (Dry-Run with Demo Data)

```bash
python main.py
```

This runs with built-in demo targets and `dry_run: true` — **no emails are actually sent**. Great for verifying the setup works.

### Run with Your Own Targets

```bash
python main.py config.yaml it_password_reset targets.csv
```

### Command Format

```
python main.py [config_file] [scenario] [targets_csv]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `config_file` | Path to config YAML | `config.yaml` |
| `scenario` | Which email template to use | `it_password_reset` |
| `targets_csv` | Path to CSV with target list | Uses built-in demo targets |

### Show Help

```bash
python main.py --help
```

### Examples

```bash
# Test with demo targets (dry-run)
python main.py

# IT Password Reset scenario with your targets
python main.py config.yaml it_password_reset targets.csv

# HR Bonus scenario
python main.py config.yaml hr_bonus_announcement targets.csv

# Urgent Invoice scenario
python main.py config.yaml urgent_invoice targets.csv
```

---

## Available Scenarios

### 1. IT Password Reset (`it_password_reset`)
**Subject:** *"Action Required: Your Password Expires in 24 Hours"*

Simulates an IT department notification warning the employee their password is about to expire, with a fake "Reset Password" button.

### 2. HR Bonus Announcement (`hr_bonus_announcement`)
**Subject:** *"Congratulations! Your Annual Bonus Has Been Approved"*

Simulates an HR department email announcing a performance bonus, with a fake "View Bonus Details" button.

### 3. Urgent Invoice (`urgent_invoice`)
**Subject:** *"URGENT: Invoice #INV-2026-4851 Requires Your Immediate Approval"*

Simulates an Accounts Payable email requesting urgent invoice approval, with a fake "Review Invoice" button.

> **Note:** All buttons/links in the templates point to `#simulation-link-disabled` — they are intentionally non-functional.

---

## Sample Output

```
2026-04-29 19:12:01 | INFO     | ======================================================================
2026-04-29 19:12:01 | INFO     |   [!] AUTHORIZED USE ONLY [!]
2026-04-29 19:12:01 | INFO     |   This tool is for authorized security awareness training.
2026-04-29 19:12:01 | INFO     | ======================================================================
2026-04-29 19:12:01 | INFO     | Loading configuration from: config.yaml
2026-04-29 19:12:01 | INFO     | Loading targets from CSV: targets.csv
2026-04-29 19:12:01 | INFO     | Loaded 3 target(s) from 'targets.csv'
2026-04-29 19:12:01 | INFO     | ======================================================================
2026-04-29 19:12:01 | INFO     |   AUTHORIZED PHISHING SIMULATION TOOL
2026-04-29 19:12:01 | INFO     |   Campaign: Q1-2026-Security-Awareness
2026-04-29 19:12:01 | INFO     |   Mode: DRY RUN
2026-04-29 19:12:01 | INFO     |   Scenario: it_password_reset
2026-04-29 19:12:01 | INFO     | ======================================================================
2026-04-29 19:12:01 | INFO     | DomainValidator initialized | Authorized domains: ['yourcompany.com']
2026-04-29 19:12:01 | INFO     | Validating 3 targets...
2026-04-29 19:12:01 | INFO     | Batch validation: 3 valid, 0 rejected / 3 total
2026-04-29 19:12:01 | INFO     |   [+] Rendered email for john.doe@yourcompany.com
2026-04-29 19:12:01 | INFO     |   [+] Rendered email for jane.smith@yourcompany.com
2026-04-29 19:12:01 | INFO     |   [+] Rendered email for bob.wilson@yourcompany.com
2026-04-29 19:12:01 | INFO     | [DRY RUN] Would send to john.doe@yourcompany.com
2026-04-29 19:12:01 | INFO     | [DRY RUN] Would send to jane.smith@yourcompany.com
2026-04-29 19:12:01 | INFO     | [DRY RUN] Would send to bob.wilson@yourcompany.com
2026-04-29 19:12:01 | INFO     | ======================================================================
2026-04-29 19:12:01 | INFO     |   SIMULATION SUMMARY
2026-04-29 19:12:01 | INFO     | ======================================================================
2026-04-29 19:12:01 | INFO     |   DRY_RUN     : 3
2026-04-29 19:12:01 | INFO     |   REJECTED    : 0
2026-04-29 19:12:01 | INFO     |   TOTAL       : 3
2026-04-29 19:12:01 | INFO     | ======================================================================
```

### Sample JSON Log Entry (`logs/simulation_log.json`)

```json
{
  "timestamp": "2026-04-29T13:12:01.540146Z",
  "campaign_name": "Q1-2026-Security-Awareness",
  "target_email": "john.doe@yourcompany.com",
  "target_name": "John Doe",
  "scenario": "it_password_reset",
  "status": "dry_run",
  "error_message": null,
  "watermark_applied": true,
  "domain_validated": true
}
```

---

## Safety Mechanisms

This tool is designed with **safety-first architecture**. Multiple layers prevent misuse:

| # | Safety Layer | Description |
|---|-------------|-------------|
| 1 | **Domain Whitelisting** | Emails can ONLY be sent to pre-approved domains. Any external address (e.g., `@gmail.com`) is automatically **blocked** |
| 2 | **Mandatory Watermark** | Every email contains a visible footer: `[SECURITY SIMULATION TEST - DO NOT PANIC]`. Cannot be removed |
| 3 | **Rate Limiting** | Minimum 5-second delay between emails. Max 50 emails per run (configurable) |
| 4 | **Dry-Run Mode** | Enabled by default — tests the entire pipeline without sending real emails |
| 5 | **Disabled Links** | All clickable buttons point to `#simulation-link-disabled` — they don't go anywhere |
| 6 | **JSON Audit Trail** | Every single attempt is logged with timestamp, status, target, and scenario |
| 7 | **Pydantic Validation** | All input (emails, config, targets) is strictly validated before processing |
| 8 | **Secret Protection** | `.env` file is gitignored — SMTP credentials never reach GitHub |

---

## File Descriptions

| File | Lines | Description |
|------|-------|-------------|
| `main.py` | Entry point — loads config, reads CSV, orchestrates the simulation pipeline |
| `models.py` | Pydantic models: `EmailTarget`, `CampaignConfig`, `SMTPConfig`, `EmailLogEntry` |
| `templates.py` | Jinja2 `TemplateEngine` class + 3 built-in HTML email scenario templates |
| `validator.py` | `DomainValidator` class — the gatekeeper that blocks unauthorized domains |
| `sender.py` | `SimulationSender` class — handles SMTP delivery, rate limiting, and JSON logging |
| `config.yaml` | YAML configuration for SMTP, domains, rate limits, and company info |
| `targets.csv` | CSV file containing the list of simulation targets |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `FileNotFoundError: config.yaml` | Make sure you're running from the project directory |
| `BLOCKED: domain 'gmail.com' is NOT authorized` | This is **expected behavior** — the tool blocks external domains. Add your domain to `authorized_domains` in `config.yaml` |
| `SMTP authentication failed` | Check your `.env` credentials. Gmail users need an [App Password](https://myaccount.google.com/apppasswords) |
| `UnicodeEncodeError` on Windows | Already fixed — the tool uses ASCII-safe characters for console output |

---

## License

This project is for **educational and authorized use only**.

Distributed under the MIT License.

---

<p align="center">
  <b>Phalanx Check</b> — Test your organization's defenses before the real attackers do.
</p>
