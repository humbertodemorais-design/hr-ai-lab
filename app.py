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

from flask import Flask, render_template, request, jsonify
from agents.knowledge_agent import ask_claude, load_policy
from agents.workflow_agent import classify_ticket
import pandas as pd

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
        
        # Replace NaN with None so it serialises as JSON null
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
if __name__ == "__main__":
    app.run(debug=True, port=8080, host="127.0.0.1")
