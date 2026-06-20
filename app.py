"""
HR AI Automation Lab — Web Interface
Flask app serving the HR AI demo in the browser
"""

from flask import Flask, render_template, request, jsonify
from agents.knowledge_agent import ask_claude, load_policy
from agents.workflow_agent import classify_ticket
import pandas as pd
import json
import os

app = Flask(__name__, template_folder="app/templates",
            static_folder="app/static")

policy = load_policy("data/hr_policy.txt")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/policy", methods=["POST"])
def policy_qa():
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400
    try:
        response = ask_claude(question, policy)
        return jsonify(response)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Model returned invalid JSON: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/classify", methods=["POST"])
def classify():
    data = request.get_json()
    ticket = data.get("ticket", "").strip()
    if not ticket:
        return jsonify({"error": "No ticket provided"}), 400
    try:
        result = classify_ticket(ticket)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/benchmark", methods=["GET"])
def benchmark():
    try:
        import math
        df = pd.read_csv("evaluation/benchmark_results.csv")
        df = df.where(pd.notnull(df), None)
        summary = {
            "total": len(df),
            "valid_json": int(df["claude_valid_json"].sum()),
            "correct_area": int(df["claude_correct_area"].sum()),
            "avg_latency": round(df["claude_latency_s"].mean(), 2),
            "boundary_passed": int(
                df[df["category"] == "Boundary"]["claude_answer_accurate"]
                .apply(lambda x: str(x).lower() == "true")
                .sum()
            ),
            "results": [
                {k: (None if isinstance(v, float) and math.isnan(v) else v)
                 for k, v in row.items()}
                for row in df.to_dict(orient="records")
            ]
        }
        return jsonify(summary)
    except FileNotFoundError:
        return jsonify({"error": "Run benchmarks.py first"}), 404

@app.route("/api/dashboard-data", methods=["GET"])
def dashboard_data():
    try:
        from integrations.sheets import get_sheet
        sheet = get_sheet(os.getenv("GOOGLE_SHEET_ID"))
        all_data = sheet.get_all_records()

        if not all_data:
            return jsonify({
                "total": 0,
                "escalated": 0,
                "escalation_rate": 0,
                "departments": {},
                "priorities": {},
                "recent_tickets": []
            })

        total = len(all_data)
        escalated = sum(1 for r in all_data if r.get("Escalate") == "YES")

        departments = {}
        for row in all_data:
            dept = row.get("Department", "Unknown").replace("_", " ")
            departments[dept] = departments.get(dept, 0) + 1

        priorities = {}
        for row in all_data:
            pri = row.get("Priority", "unknown").lower()
            priorities[pri] = priorities.get(pri, 0) + 1

        recent = list(reversed(all_data[-10:]))
        recent_tickets = [{
            "ticket_id": r.get("Ticket ID", ""),
            "department": r.get("Department", "").replace("_", " "),
            "priority": r.get("Priority", ""),
            "escalate": r.get("Escalate", "No"),
            "timestamp": r.get("Timestamp", ""),
            "ticket": r.get("Original Ticket", "")[:80]
        } for r in recent]

        return jsonify({
            "total": total,
            "escalated": escalated,
            "escalation_rate": round((escalated/total)*100, 1) if total > 0 else 0,
            "departments": departments,
            "priorities": priorities,
            "recent_tickets": recent_tickets
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8080, host="127.0.0.1")
