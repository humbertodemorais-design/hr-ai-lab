import anthropic
import os
import json
from dotenv import load_dotenv
from google import genai as google_genai
from prompts.templates import HR_POLICY_QA

load_dotenv()

claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
google_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def load_policy(filepath):
    with open(filepath, "r") as f:
        return f.read()

def ask_claude(question, context):
    prompt = HR_POLICY_QA.format(context=context, question=question)
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
    return json.loads(raw.strip())

def ask_gemini(question, context):
    prompt = HR_POLICY_QA.format(context=context, question=question)
    response = google_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
