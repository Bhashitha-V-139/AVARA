"""
Run the evaluation questions against the live backend and report the results.

Usage (backend must be running on port 8000):
    python tests/run_eval.py
"""

import json
import sys
import time
from pathlib import Path

import httpx

API = "http://127.0.0.1:8000/ask"
QUESTIONS = Path(__file__).with_name("eval_questions.json")
PAUSE_SECONDS = 25  # keeps requests under the free-tier limit of 15 per minute


def check(item: dict, body: dict) -> list[str]:
    """Return a list of problems. An empty list means the question passed."""
    problems = []
    answer = body.get("answer", "").lower()
    cited_pages = {c["page_number"] for c in body.get("citations", [])}

    if body.get("grounded") != item["expect_grounded"]:
        problems.append(
            f"grounded={body.get('grounded')}, expected {item['expect_grounded']}"
        )

    if item["expected_pages"] and not (cited_pages & set(item["expected_pages"])):
        problems.append(
            f"cited pages {sorted(cited_pages) or 'none'}, expected one of {item['expected_pages']}"
        )

    for fact in item["key_facts"]:
        if fact.lower() not in answer:
            problems.append(f"missing key fact: '{fact}'")

    return problems


def main() -> int:
    items = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    session_id = None
    failures = 0
    results = []

    for item in items:
        # A new session for each question keeps results independent.
        payload = {"question": item["question"]}
        try:
            response = httpx.post(API, json=payload, timeout=120)
        except httpx.HTTPError as exc:
            print(f"{item['id']}: could not reach backend ({exc})")
            return 1

        if response.status_code != 200:
            problems = [f"HTTP {response.status_code}: {response.text[:150]}"]
            body = {}
        else:
            body = response.json()
            problems = check(item, body)

        if item.get("known_gap") and problems:
            status = "KNOWN GAP"
        elif problems:
            status = "FAIL"
            failures += 1
        else:
            status = "PASS"

        results.append((item["id"], status, item["question"], problems))
        print(f"{item['id']} {status:9} {item['question']}")
        for problem in problems:
            print(f"      - {problem}")

        time.sleep(PAUSE_SECONDS)

    passed = sum(1 for _, s, _, _ in results if s == "PASS")
    gaps = sum(1 for _, s, _, _ in results if s == "KNOWN GAP")
    print()
    print(f"Summary: {passed} passed, {failures} failed, {gaps} known gap(s), {len(results)} total")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())