"""
Payroll Exception Detector
High-risk module — every exception requires human approval
before any action is taken
"""

import anthropic
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

claude_client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

EXCEPTION_TYPES = {
    "ZERO_HOURS": {
        "severity": "high",
        "description": "Employee paid but logged zero hours",
        "requires_approval": True
    },
    "BANK_CHANGE": {
        "severity": "high",
        "description": "Bank account changed this pay period",
        "requires_approval": True
    },
    "OVERPAYMENT": {
        "severity": "critical",
        "description": "Gross pay significantly exceeds expected amount",
        "requires_approval": True
    },
    "DUPLICATE": {
        "severity": "critical",
        "description": "Duplicate employee ID detected",
        "requires_approval": True
    },
    "DEDUCTION_ANOMALY": {
        "severity": "medium",
        "description": "Deductions outside normal range",
        "requires_approval": True
    },
    "NET_PAY_CHANGE": {
        "severity": "medium",
        "description": "Net pay changed significantly vs last period",
        "requires_approval": True
    }
}


def analyse_payroll(payroll_data):
    """
    Run Claude over the full payroll dataset
    Returns list of exceptions requiring human review
    """

    prompt = f"""
You are a Payroll Exception Detection Agent for Konecta.
Your role is to identify anomalies in payroll data that require
human review before processing.

CRITICAL: You must flag anything suspicious. It is far better to
flag a false positive than to miss a genuine payroll error or fraud.
Every exception you flag will be reviewed by a human before any
action is taken.

Analyse the following payroll records and identify ALL exceptions:

{json.dumps(payroll_data, indent=2)}

Check for these exception types:
1. ZERO_HOURS — employee has 0 hours worked but is being paid
2. BANK_CHANGE — bank_account_changed is True
3. OVERPAYMENT — gross_pay is significantly higher than
   (base_salary / 12) — flag if more than 20% over expected
4. DUPLICATE — same employee_id appears more than once
5. DEDUCTION_ANOMALY — deductions seem unusually high or low
   relative to gross pay (normal range 15-35% of gross)
6. NET_PAY_CHANGE — net_pay differs significantly from
   previous_net_pay (more than 15% change)

Respond ONLY in this exact JSON format:
{{
  "payroll_period": "June 2026",
  "total_records": {len(payroll_data)},
  "total_exceptions": 0,
  "total_gross_pay": 0,
  "exceptions": [
    {{
      "employee_id": "EMP001",
      "employee_name": "Full Name",
      "exception_type": "EXCEPTION_TYPE",
      "severity": "critical/high/medium",
      "description": "clear explanation of what was found",
      "expected_value": "what was expected",
      "actual_value": "what was found",
      "recommendation": "what the payroll team should check",
      "auto_hold": true
    }}
  ],
  "clean_records": [
    {{
      "employee_id": "EMP001",
      "employee_name": "Full Name",
      "net_pay": 0.00,
      "status": "approved_for_processing"
    }}
  ],
  "summary": "brief executive summary of findings"
}}
"""

    message = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw.strip())
    result["analysed_at"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    result["agent"] = "Claude Haiku"
    result["risk_tier"] = "HIGH — Payroll data requires human " \
                          "approval before processing"
    return result


def log_payroll_audit(payroll_period, exceptions,
                       approvals, sheet_id):
    """Log all payroll decisions to audit trail"""
    try:
        from integrations.sheets import get_sheet
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )
        client = gspread.authorize(creds)
        wb = client.open_by_key(sheet_id)

        try:
            sheet = wb.worksheet("Payroll Audit Log")
        except Exception:
            sheet = wb.add_worksheet(
                "Payroll Audit Log", rows=200, cols=10
            )
            sheet.append_row([
                "Timestamp", "Pay Period", "Employee ID",
                "Employee Name", "Exception Type", "Severity",
                "Description", "Decision", "Decided By",
                "Decision Time"
            ])
            sheet.format('A1:J1',
                         {'textFormat': {'bold': True}})

        for exc in exceptions:
            decision = approvals.get(
                exc["employee_id"] + "_" + exc["exception_type"],
                "pending"
            )
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                payroll_period,
                exc["employee_id"],
                exc["employee_name"],
                exc["exception_type"],
                exc["severity"],
                exc["description"],
                decision,
                "HR Manager (via Konecta AI Lab)",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])

        print(f"  ✓ Payroll audit log updated — "
              f"{len(exceptions)} exceptions logged")
    except Exception as e:
        print(f"  ✗ Audit log failed: {e}")
