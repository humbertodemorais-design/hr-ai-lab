import anthropic
import os
import json
from dotenv import load_dotenv
from prompts.templates import HR_TICKET_CLASSIFIER
from integrations.sheets import log_to_sheet

load_dotenv()

claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

def classify_ticket(ticket_text):
    prompt = HR_TICKET_CLASSIFIER.format(ticket=ticket_text)

    message = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    result["original_ticket"] = ticket_text
    return result


def process_tickets(tickets):
    results = []
    for ticket in tickets:
        print(f"\nProcessing ticket {ticket['id']}...")
        result = classify_ticket(ticket["text"])

        correct = result["department"] == ticket["expected_department"]
        escalation_correct = result["escalate"] == ticket["expected_escalate"]

        result["test_id"] = ticket["id"]
        result["expected_department"] = ticket["expected_department"]
        result["department_correct"] = correct
        result["escalation_correct"] = escalation_correct

        # Log every ticket to Google Sheets
        ticket_id = log_to_sheet(result, SHEET_ID)
        result["ticket_id"] = ticket_id

        print(f"  → {result['department']} | "
              f"{result['priority']} priority | "
              f"{'🚨 ESCALATE' if result['escalate'] else '✓ Standard'}")

        results.append(result)
    return results
