"""
Multi-Agent Onboarding Pipeline
Agent 1: Intake & Validation (Gemini)
Agent 2: Compliance Check (Claude)
Agent 3: Setup & Assignment (Claude)
"""

import anthropic
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai as google_genai

load_dotenv()

claude_client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
gemini_client = google_genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Country-specific onboarding requirements
COUNTRY_POLICIES = {
    "UK": {
        "required_docs": [
            "Passport or right to work document",
            "P45 or starter checklist",
            "Bank account details",
            "Emergency contact form",
            "NI number confirmation"
        ],
        "mandatory_training": [
            "UK GDPR Awareness",
            "Health & Safety Induction",
            "Anti-Bribery & Corruption",
            "Information Security Essentials"
        ],
        "notice_period": "1 month (probation)",
        "probation": "6 months"
    },
    "Spain": {
        "required_docs": [
            "DNI or NIE document",
            "Social Security number",
            "Bank account details",
            "Emergency contact form",
            "Modelo 145 tax form"
        ],
        "mandatory_training": [
            "RGPD Data Protection",
            "Prevención de Riesgos Laborales",
            "Anti-Corruption Policy",
            "Information Security"
        ],
        "notice_period": "15 days (probation)",
        "probation": "6 months"
    },
    "Germany": {
        "required_docs": [
            "Personal ID or passport",
            "Tax ID (Steuer-ID)",
            "Social security card",
            "Bank account details",
            "Emergency contact form"
        ],
        "mandatory_training": [
            "DSGVO Datenschutz",
            "Arbeitssicherheit",
            "Anti-Corruption & Compliance",
            "Information Security"
        ],
        "notice_period": "2 weeks (probation)",
        "probation": "6 months"
    },
    "Brazil": {
        "required_docs": [
            "CPF and RG documents",
            "CTPS (work card)",
            "Bank account details",
            "Emergency contact form",
            "PIS/PASEP number"
        ],
        "mandatory_training": [
            "LGPD Data Privacy",
            "CIPA Safety Training",
            "Anti-Corruption (Lei Anticorrupção)",
            "Information Security"
        ],
        "notice_period": "30 days (probation)",
        "probation": "90 days"
    }
}

REQUIRED_FIELDS = [
    "full_name", "email", "role", "department",
    "start_date", "country", "manager_name"
]


def run_intake_agent(new_hire_data):
    """Agent 1 — Intake & Validation (Claude fallback from Gemini)"""

    missing_fields = [
        f for f in REQUIRED_FIELDS
        if not new_hire_data.get(f)
    ]

    country = new_hire_data.get("country", "UK")
    country_policy = COUNTRY_POLICIES.get(
        country, COUNTRY_POLICIES["UK"]
    )

    prompt = f"""
You are an HR Onboarding Intake Agent for Konecta, a global company
operating across 26 countries.

Review the following new hire submission and provide a structured
validation report.

New hire data:
{json.dumps(new_hire_data, indent=2)}

Country detected: {country}
Missing required fields: {missing_fields if missing_fields else 'None'}

Respond ONLY in this exact JSON format:
{{
  "validation_status": "passed",
  "new_hire_summary": "one sentence summary of who this person is",
  "country_detected": "{country}",
  "missing_fields": {json.dumps(missing_fields)},
  "data_quality_score": "high",
  "flags": [],
  "recommendation": "brief recommendation for the approving manager",
  "validated_at": "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
}}
"""

    try:
        message = claude_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        result["country_policy"] = country_policy
        result["agent"] = "Claude Haiku (Gemini fallback)"
        return result
    except Exception as e:
        return {
            "validation_status": "failed",
            "error": str(e),
            "agent": "Claude Haiku (Gemini fallback)",
            "missing_fields": missing_fields,
            "country_policy": country_policy
        }

def run_compliance_agent(new_hire_data, intake_result):
    """Agent 2 — Compliance Check using Claude"""

    country = new_hire_data.get("country", "UK")
    country_policy = intake_result.get(
        "country_policy", COUNTRY_POLICIES["UK"]
    )

    prompt = f"""
You are an HR Compliance Agent for Konecta.

Review the onboarding case below and generate a detailed compliance
checklist for this new hire based on their country requirements.

New hire: {new_hire_data.get('full_name')}
Role: {new_hire_data.get('role')}
Department: {new_hire_data.get('department')}
Country: {country}
Start date: {new_hire_data.get('start_date')}

Country-specific requirements:
- Required documents: {json.dumps(country_policy.get('required_docs', []))}
- Mandatory training: {json.dumps(country_policy.get('mandatory_training', []))}
- Probation period: {country_policy.get('probation', '6 months')}

Respond ONLY in this exact JSON format:
{{
  "compliance_status": "ready" or "needs_attention",
  "document_checklist": [
    {{"item": "document name", "status": "required", "deadline": "by start date"}}
  ],
  "training_checklist": [
    {{"course": "course name", "deadline": "within 30 days", "mandatory": true}}
  ],
  "compliance_risks": ["list any compliance risks"],
  "gdpr_notes": "specific GDPR/data privacy note for this country",
  "recommendation": "brief recommendation for the approving manager",
  "checked_at": "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
}}
"""

    message = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw.strip())
    result["agent"] = "Claude Haiku"
    return result


def run_setup_agent(new_hire_data, intake_result, compliance_result):
    """Agent 3 — Setup & Assignment using Claude"""

    country_policy = intake_result.get(
        "country_policy", COUNTRY_POLICIES["UK"]
    )

    prompt = f"""
You are an HR Setup Agent for Konecta. Your job is to generate the
complete onboarding setup package for a new hire.

New hire details:
- Name: {new_hire_data.get('full_name')}
- Role: {new_hire_data.get('role')}
- Department: {new_hire_data.get('department')}
- Country: {new_hire_data.get('country')}
- Start date: {new_hire_data.get('start_date')}
- Manager: {new_hire_data.get('manager_name')}
- Email: {new_hire_data.get('email')}

Mandatory training to assign:
{json.dumps(country_policy.get('mandatory_training', []))}

Respond ONLY in this exact JSON format:
{{
  "setup_status": "complete",
  "it_access_request": {{
    "email_account": "{new_hire_data.get('email')}",
    "systems": ["list of systems to provision based on role"],
    "access_level": "standard/elevated",
    "requested_for": "{new_hire_data.get('start_date')}"
  }},
  "training_assignments": [
    {{"course": "course name", "assigned_by": "day",
      "platform": "LMS/CSOD", "mandatory": true}}
  ],
  "checkin_schedule": [
    {{"day": 30, "type": "30-day check-in",
      "with": "{new_hire_data.get('manager_name')}",
      "agenda": "brief agenda"}},
    {{"day": 60, "type": "60-day check-in",
      "with": "{new_hire_data.get('manager_name')}",
      "agenda": "brief agenda"}},
    {{"day": 90, "type": "90-day review",
      "with": "{new_hire_data.get('manager_name')} + HR",
      "agenda": "brief agenda"}}
  ],
  "welcome_message": "personalised welcome message to the new hire",
  "buddy_recommendation": "recommendation for buddy/mentor pairing",
  "setup_completed_at": "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
}}
"""

    message = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw.strip())
    result["agent"] = "Claude Haiku"
    return result


def log_onboarding_to_sheet(new_hire_data, results, sheet_id):
    """Log completed onboarding to Google Sheets"""
    try:
        from integrations.sheets import get_sheet
        sheet = get_sheet(sheet_id)

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            new_hire_data.get("full_name", ""),
            new_hire_data.get("role", ""),
            new_hire_data.get("department", ""),
            new_hire_data.get("country", ""),
            new_hire_data.get("start_date", ""),
            new_hire_data.get("manager_name", ""),
            results.get("intake", {}).get("validation_status", ""),
            results.get("compliance", {}).get("compliance_status", ""),
            results.get("setup", {}).get("setup_status", ""),
            "Complete"
        ]

        sheet.append_row(row)
        print(f"  ✓ Onboarding logged for {new_hire_data.get('full_name')}")
    except Exception as e:
        print(f"  ✗ Sheet logging failed: {e}")
