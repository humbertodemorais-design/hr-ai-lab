"""
Google Sheets Dashboard Builder
Creates and updates a summary dashboard from ticket log data
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_workbook(sheet_id):
    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)


def update_dashboard(sheet_id):
    try:
        wb = get_workbook(sheet_id)

        # Get ticket log data
        log_sheet = wb.sheet1
        all_data = log_sheet.get_all_records()

        if not all_data:
            print("  ✗ No ticket data found in log sheet")
            return

        # Calculate metrics
        total = len(all_data)
        escalated = sum(1 for r in all_data if r.get("Escalate") == "YES")
        escalation_rate = round((escalated / total) * 100, 1) if total > 0 else 0

        # Department breakdown
        departments = {}
        for row in all_data:
            dept = row.get("Department", "Unknown")
            departments[dept] = departments.get(dept, 0) + 1

        # Priority breakdown
        priorities = {}
        for row in all_data:
            pri = row.get("Priority", "unknown").lower()
            priorities[pri] = priorities.get(pri, 0) + 1

        # Get or create dashboard sheet
        try:
            dash = wb.worksheet("Dashboard")
        except:
            dash = wb.add_worksheet("Dashboard", rows=50, cols=10)

        # Clear existing content
        dash.clear()

        # ── Header ──
        dash.update("A1", [["HR AI AUTOMATION LAB — LIVE DASHBOARD"]])
        dash.update("A2", [[f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]])

        # ── Summary Metrics ──
        dash.update("A4", [["SUMMARY METRICS"]])
        dash.update("A5", [["Metric", "Value"]])
        dash.update("A6", [
            ["Total tickets processed", total],
            ["Escalated tickets", escalated],
            ["Escalation rate", f"{escalation_rate}%"],
            ["Departments active", len(departments)],
        ])

        # ── Department Breakdown ──
        dash.update("A12", [["TICKETS BY DEPARTMENT"]])
        dash.update("A13", [["Department", "Count", "% of Total"]])

        dept_rows = []
        for dept, count in sorted(departments.items(),
                                   key=lambda x: x[1], reverse=True):
            pct = round((count / total) * 100, 1)
            dept_rows.append([dept.replace("_", " "), count, f"{pct}%"])
        dash.update("A14", dept_rows)

        # ── Priority Breakdown ──
        dash.update("D12", [["TICKETS BY PRIORITY"]])
        dash.update("D13", [["Priority", "Count", "% of Total"]])

        pri_rows = []
        priority_order = ["high", "medium", "low"]
        for pri in priority_order:
            count = priorities.get(pri, 0)
            pct = round((count / total) * 100, 1) if total > 0 else 0
            pri_rows.append([pri.upper(), count, f"{pct}%"])
        dash.update("D14", pri_rows)

        # ── Escalation Summary ──
        dash.update("A20", [["ESCALATION SUMMARY"]])
        dash.update("A21", [["Ticket ID", "Department",
                              "Priority", "Reason"]])

        escalation_rows = []
        for row in all_data:
            if row.get("Escalate") == "YES":
                escalation_rows.append([
                    row.get("Ticket ID", ""),
                    row.get("Department", "").replace("_", " "),
                    row.get("Priority", "").upper(),
                    row.get("Escalation Reason", "")[:80]
                ])

        if escalation_rows:
            dash.update("A22", escalation_rows)
        else:
            dash.update("A22", [["No escalations recorded"]])

        # ── Format headers bold ──
        header_ranges = ["A1", "A4", "A12", "A13",
                         "A20", "A21", "D12", "D13"]
        for cell in header_ranges:
            dash.format(cell, {"textFormat": {"bold": True}})

        # Format title
        dash.format("A1", {
            "textFormat": {"bold": True, "fontSize": 14},
        })

        print(f"  ✓ Dashboard updated — {total} tickets, "
              f"{escalated} escalations, "
              f"{len(departments)} departments")

    except Exception as e:
        print(f"  ✗ Dashboard update failed: {e}")
