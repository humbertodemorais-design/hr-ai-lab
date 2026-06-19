# HR AI Automation Lab

A hands-on engineering project simulating enterprise HR AI automation
using Anthropic Claude and Google Gemini.

Built as a technical demonstration of agentic workflow design, 
prompt engineering, structured output validation, and LLM evaluation
frameworks applied to real HR use cases.

---

## What it does

### Module 1 — HR Knowledge Agent
Answers HR policy questions with structured, validated JSON responses.
Grounds all answers in actual policy documents via context injection.
Returns confidence scoring on every response for human-in-the-loop routing.

### Module 2 — Workflow Classifier & Router  
Classifies incoming HR support tickets and routes them to the correct
department (Payroll, L&D, HR Ops, Talent) with priority detection and
automatic escalation logic for sensitive cases — harassment, grievances,
missing salary payments, discrimination complaints.

### Module 3 — Benchmark Evaluation Framework
Structured evaluation across three test categories:
- Straightforward: basic policy retrieval
- Boundary: hallucination detection on constrained answers  
- Ambiguous: confidence behaviour when policy doesn't have a clear answer

Results: 8/8 JSON compliance · 8/8 policy area accuracy · 
3/3 hallucination boundary tests passed · 2.27s avg latency

---

## Architecture

Employee Input

→ Prompt Orchestrator

→ Model Router (Claude / Gemini)

→ HR Agent Layer (Knowledge Agent · Workflow Agent)

→ Output Validator (JSON schema · Confidence scoring)

→ Structured Response

---

## Tech stack

- Python 3.14
- Anthropic Claude API (claude-haiku-4-5-20251001)
- Google Gemini API (google-genai)
- pandas (evaluation and reporting)
- python-dotenv (secrets management)

---

## Setup

```bash
git clone https://github.com/[your-handle]/hr-ai-lab
cd hr-ai-lab
python3 -m venv venv
source venv/bin/activate
pip3 install anthropic google-genai python-dotenv pandas
```

Create a `.env` file:

ANTHROPIC_API_KEY=your_key_here

GEMINI_API_KEY=your_key_here

Run the demo:
```bash
python3 main.py
```

Run the benchmark:
```bash
python3 evaluation/benchmarks.py
```

---

## Key design decisions

**Why JSON output?**  
Structured outputs are consumable by downstream systems — ticketing 
platforms, dashboards, audit logs. Raw text creates integration friction
in enterprise environments.

**Why two models?**  
Multi-model architecture avoids vendor lock-in and enables cost 
optimisation — routing simpler queries to faster cheaper models while
reserving stronger reasoning for complex sensitive cases.

**Why three benchmark categories?**  
Straightforward tests validate basic retrieval. Boundary tests catch
hallucination on constrained answers. Ambiguous tests verify the model
signals uncertainty rather than fabricating policy.

---

## Production roadmap

- RAG pipeline — vector embeddings for policy chunk retrieval
- Vertex AI deployment — model versioning, IAM, audit logging
- Human-in-the-loop — confidence threshold routing to HR reviewers
- Google Secret Manager — API key vault and rotation
- Async processing — handle high-volume ticket classification at scale