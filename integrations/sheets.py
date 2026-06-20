"""
Google Sheets Integration
Logs HR ticket classifications to a live Google Sheet
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet(sheet_id):
    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1

def calculate_deadline(department, priority):
    from prompts.templates import HR_DEADLINE_RULES
    hours = HR_DEADLINE_RULES.get(department, {}).get(priority, 48)
    deadline = datetime.now() + timedelta(hours=hours)
    return deadline.strftime("%Y-%m-%d %H:%M"), hours

def log_to_sheet(ticket_result, sheet_id):
    try:
        sheet = get_sheet(sheet_id)
        ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        department = ticket_result.get("department", "HR_Ops")
        priority = ticket_result.get("priority", "medium")
        deadline, hours = calculate_deadline(department, priority)

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ticket_id,
            department,
            priority,
            "YES" if ticket_result.get("escalate") else "No",
            ticket_result.get("escalation_reason") or "",
            ticket_result.get("confidence", ""),
            ticket_result.get("suggested_response", "")[:200],
            ticket_result.get("original_ticket", "")[:200],
            deadline,
            f"{hours}h SLA"
        ]

        sheet.append_row(row)
        print(f"  ✓ Logged to Google Sheets: {ticket_id} "
              f"| Deadline: {deadline} ({hours}h SLA)")
        return ticket_id

    except Exception as e:
        print(f"  ✗ Sheet logging failed: {e}")
        return None