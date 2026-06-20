"""
Google Sheets Integration
Logs HR ticket classifications to a live Google Sheet
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
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

def log_to_sheet(ticket_result, sheet_id):
    try:
        sheet = get_sheet(sheet_id)

        # Generate a simple ticket ID
        ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ticket_id,
            ticket_result.get("department", ""),
            ticket_result.get("priority", ""),
            "YES" if ticket_result.get("escalate") else "No",
            ticket_result.get("escalation_reason") or "",
            ticket_result.get("confidence", ""),
            ticket_result.get("suggested_response", "")[:200],
            ticket_result.get("original_ticket", "")[:200]
        ]

        sheet.append_row(row)
        print(f"  ✓ Logged to Google Sheets: {ticket_id}")
        return ticket_id

    except Exception as e:
        print(f"  ✗ Sheet logging failed: {e}")
        return None
