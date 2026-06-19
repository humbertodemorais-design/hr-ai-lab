"""
HR AI Automation Lab — Benchmarking Module
Tests Claude on accuracy, latency, and output quality
Designed for Gemini comparison when billing is available
"""

import time
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.knowledge_agent import ask_claude, load_policy

policy = load_policy("data/hr_policy.txt")

# ================================================
# TEST CASES — Three categories
# ================================================

TEST_CASES = [
    # --- Category 1: Straightforward ---
    {
        "id": 1,
        "category": "Straightforward",
        "question": "How many days of annual leave do I get per year?",
        "expected_answer_contains": "25",
        "expected_policy_area": "Annual Leave Policy"
    },
    {
        "id": 2,
        "category": "Straightforward",
        "question": "How many days can I work from home per week?",
        "expected_answer_contains": "3",
        "expected_policy_area": "Remote Work Policy"
    },
    {
        "id": 3,
        "category": "Straightforward",
        "question": "What is the L&D budget per employee per year?",
        "expected_answer_contains": "1,500",
        "expected_policy_area": "Learning and Development Policy"
    },

    # --- Category 2: Boundary (correct answer is NO or involves a limit) ---
    {
        "id": 4,
        "category": "Boundary",
        "question": "Can I carry over 10 days of unused annual leave?",
        "expected_answer_contains": "5",
        "expected_policy_area": "Annual Leave Policy"
    },
    {
        "id": 5,
        "category": "Boundary",
        "question": "Can I work from home every day of the week?",
        "expected_answer_contains": "3",
        "expected_policy_area": "Remote Work Policy"
    },
    {
        "id": 6,
        "category": "Boundary",
        "question": "Can I work remotely from another country for 3 months?",
        "expected_answer_contains": "4 weeks",
        "expected_policy_area": "Remote Work Policy"
    },

    # --- Category 3: Ambiguous (policy doesn't fully answer) ---
    {
        "id": 7,
        "category": "Ambiguous",
        "question": "Can I take unpaid leave to travel for 6 months?",
        "expected_answer_contains": None,
        "expected_policy_area": "Annual Leave Policy"
    },
    {
        "id": 8,
        "category": "Ambiguous",
        "question": "What happens to my bonus if I resign in February?",
        "expected_answer_contains": "March",
        "expected_policy_area": "Compensation and Bonus Policy"
    },
]

# ================================================
# BENCHMARK RUNNER
# ================================================

def is_valid_json_response(response):
    required_keys = ["answer", "confidence", "policy_area", "follow_up_suggestion"]
    return all(k in response for k in required_keys)

def check_answer_accuracy(response, expected_contains):
    if expected_contains is None:
        return "N/A"
    answer_lower = response.get("answer", "").lower()
    return expected_contains.lower() in answer_lower

def run_benchmark():
    print("\n" + "=" * 65)
    print("  HR AI BENCHMARK — CLAUDE EVALUATION")
    print("=" * 65)

    results = []

    for test in TEST_CASES:
        print(f"\nRunning test {test['id']} [{test['category']}]: "
              f"{test['question'][:55]}...")

        row = {
            "test_id": test["id"],
            "category": test["category"],
            "question": test["question"],
            "expected_policy_area": test["expected_policy_area"]
        }

        # --- Claude ---
        try:
            start = time.time()
            claude_resp = ask_claude(test["question"], policy)
            claude_time = round(time.time() - start, 2)

            row["claude_answer"] = claude_resp.get("answer", "")
            row["claude_confidence"] = claude_resp.get("confidence", "")
            row["claude_policy_area"] = claude_resp.get("policy_area", "")
            row["claude_latency_s"] = claude_time
            row["claude_valid_json"] = is_valid_json_response(claude_resp)
            row["claude_answer_accurate"] = check_answer_accuracy(
                claude_resp, test["expected_answer_contains"]
            )
            row["claude_correct_area"] = (
                test["expected_policy_area"].lower() in
                claude_resp.get("policy_area", "").lower()
            )

        except Exception as e:
            print(f"  Claude error: {e}")
            row["claude_error"] = str(e)

        results.append(row)
        time.sleep(1)

    # ================================================
    # PRINT RESULTS TABLE
    # ================================================
    print("\n\n" + "=" * 65)
    print("BENCHMARK RESULTS")
    print("=" * 65)

    print("\n{:<4} {:<16} {:<10} {:<10} {:<10} {:<8}".format(
        "ID", "Category", "Latency", "Valid JSON",
        "Accurate", "Area OK"
    ))
    print("-" * 62)

    for r in results:
        print("{:<4} {:<16} {:<10} {:<10} {:<10} {:<8}".format(
            r["test_id"],
            r["category"],
            f"{r.get('claude_latency_s', 'ERR')}s",
            "✓" if r.get("claude_valid_json") else "✗",
            str(r.get("claude_answer_accurate", "N/A")),
            "✓" if r.get("claude_correct_area") else "✗"
        ))

    # ================================================
    # SUMMARY STATS
    # ================================================
    valid_json = sum(1 for r in results if r.get("claude_valid_json"))
    correct_area = sum(1 for r in results if r.get("claude_correct_area"))
    accurate = sum(1 for r in results
                   if r.get("claude_answer_accurate") is True)
    avg_latency = round(
        sum(r.get("claude_latency_s", 0) for r in results) / len(results), 2
    )
    boundary_accurate = sum(
        1 for r in results
        if r["category"] == "Boundary"
        and r.get("claude_answer_accurate") is True
    )

    print("\n" + "=" * 65)
    print("SUMMARY")
    print("=" * 65)
    print(f"Total tests:       {len(results)}")
    print(f"Valid JSON:        {valid_json}/{len(results)}")
    print(f"Correct area:      {correct_area}/{len(results)}")
    print(f"Answer accuracy:   {accurate}/7 (excl. ambiguous)")
    print(f"Boundary accuracy: {boundary_accurate}/3 "
          f"(hallucination check)")
    print(f"Avg latency:       {avg_latency}s")

    # ================================================
    # SAVE TO CSV
    # ================================================
    try:
        import pandas as pd
        df = pd.DataFrame(results)
        os.makedirs("evaluation", exist_ok=True)
        df.to_csv("evaluation/benchmark_results.csv", index=False)
        print(f"\nFull results saved to: evaluation/benchmark_results.csv")
    except ImportError:
        print("\nNote: Install pandas to save CSV: pip3 install pandas")

    # ================================================
    # INTERESTING FINDINGS
    # ================================================
    print("\n" + "=" * 65)
    print("NOTABLE FINDINGS")
    print("=" * 65)

    for r in results:
        if r["category"] == "Boundary":
            accurate = r.get("claude_answer_accurate")
            conf = r.get("claude_confidence", "")
            print(f"\nBoundary test {r['test_id']}: {r['question']}")
            print(f"  Accurate: {accurate} | Confidence: {conf}")
            print(f"  Answer: {r.get('claude_answer', '')[:120]}")

    for r in results:
        if r["category"] == "Ambiguous":
            conf = r.get("claude_confidence", "")
            print(f"\nAmbiguous test {r['test_id']}: {r['question']}")
            print(f"  Confidence: {conf}")
            print(f"  Answer: {r.get('claude_answer', '')[:120]}")

    return results

if __name__ == "__main__":
    run_benchmark()
