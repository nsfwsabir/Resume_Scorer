#!/usr/bin/env python3
"""Compare the LLM resume scorer against a keyword baseline on a labeled set.

Usage:
    python eval/run_eval.py                 # baseline + LLM (needs GROQ_API_KEY)
    python eval/run_eval.py --system baseline
    python eval/run_eval.py --system llm --limit 4
    python eval/run_eval.py --self-check
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EVAL_DIR = Path(__file__).resolve().parent
TEST_SET_PATH = EVAL_DIR / "test_set.json"
RESULTS_PATH = EVAL_DIR / "results.json"

TIERS = ["low", "medium", "high"]
TIER_INDEX = {tier: i for i, tier in enumerate(TIERS)}


def tier_for_score(score):
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def normalize(text):
    return " " + re.sub(r"[^a-z0-9]+", " ", text.lower()).strip() + " "


def has_alias(text_norm, alias):
    return normalize(alias) in text_norm


def baseline_score(resume_text, job):
    """Naive lexical score: required coverage, preferred coverage, years regex."""
    text = normalize(resume_text)
    required = job["required"]
    preferred = job["preferred"]
    req_hits = sum(
        1 for aliases in required.values() if any(has_alias(text, a) for a in aliases)
    )
    pref_hits = sum(
        1 for aliases in preferred.values() if any(has_alias(text, a) for a in aliases)
    )
    req_cov = req_hits / len(required) if required else 1.0
    pref_cov = pref_hits / len(preferred) if preferred else 1.0

    years = max(
        (
            float(value)
            for value in re.findall(
                r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", resume_text.lower()
            )
        ),
        default=0.0,
    )
    min_years = job.get("min_experience")
    exp_met = min_years is None or years >= min_years

    score = round(100 * (0.7 * req_cov + 0.2 * pref_cov + 0.1 * exp_met), 1)
    return {
        "score": score,
        "required_coverage": round(req_cov, 3),
        "preferred_coverage": round(pref_cov, 3),
        "years_experience": years,
        "experience_met": exp_met,
    }


def _ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = average_rank
        i = j + 1
    return ranks


def spearman(reference, predicted):
    if len(reference) < 2:
        return None
    rx = _ranks(reference)
    ry = _ranks(predicted)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    numerator = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return round(numerator / (dx * dy), 3)


def evaluate(records):
    scored = [record for record in records if record.get("error") is None]
    y_true = [TIER_INDEX[record["expected_tier"]] for record in scored]
    y_pred = [TIER_INDEX[record["predicted_tier"]] for record in scored]

    confusion = {truth: {pred: 0 for pred in TIERS} for truth in TIERS}
    for truth, pred in zip(y_true, y_pred):
        confusion[TIERS[truth]][TIERS[pred]] += 1

    per_class = {}
    for index, tier in enumerate(TIERS):
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == index and p == index)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != index and p == index)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == index and p != index)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[tier] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": sum(1 for t in y_true if t == index),
        }

    accuracy = (
        sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(scored) if scored else None
    )
    band_errors = [abs(t - p) for t, p in zip(y_true, y_pred)]
    return {
        "n": len(scored),
        "errors": len(records) - len(scored),
        "accuracy": round(accuracy, 3) if accuracy is not None else None,
        "macro_f1": round(sum(v["f1"] for v in per_class.values()) / len(TIERS), 3),
        "spearman": spearman(y_true, [record["score"] for record in scored]),
        "mean_band_error": round(sum(band_errors) / len(band_errors), 3)
        if band_errors
        else None,
        "severe_errors": sum(1 for error in band_errors if error == 2),
        "high_false_positives": sum(
            1 for t, p in zip(y_true, y_pred) if t == 0 and p == 2
        ),
        "per_class": per_class,
        "confusion": confusion,
    }


def run_baseline(data):
    records = []
    for item in data["items"]:
        job = data["jobs"][item["job_id"]]["baseline"]
        result = baseline_score(item["resume_text"], job)
        records.append(
            {
                "id": item["id"],
                "job_id": item["job_id"],
                "category": item["category"],
                "expected_tier": item["expected_tier"],
                "predicted_tier": tier_for_score(result["score"]),
                **result,
                "error": None,
            }
        )
    return {"records": records, "metrics": evaluate(records)}


def with_retries(function, label, attempts=4):
    for attempt in range(1, attempts + 1):
        try:
            return function()
        except Exception as exc:
            if attempt == attempts:
                raise
            wait = 15 * attempt
            print(
                f"  [{label}] attempt {attempt} failed "
                f"({type(exc).__name__}: {exc}); retrying in {wait}s"
            )
            time.sleep(wait)


def run_llm(data, limit=None, sleep=2.0):
    from analyzer import final_score, parse_job_description, parse_resume

    items = data["items"][:limit]
    job_ids = list(dict.fromkeys(item["job_id"] for item in items))

    jobs = {}
    for job_id in job_ids:
        print(f"Parsing job description: {job_id}")
        jobs[job_id] = with_retries(
            lambda job_id=job_id: parse_job_description(
                data["jobs"][job_id]["text"]
            ),
            job_id,
        )
        time.sleep(sleep)

    records = []
    for number, item in enumerate(items, 1):
        print(f"[{number}/{len(items)}] {item['id']} ({item['category']})")
        record = {
            "id": item["id"],
            "job_id": item["job_id"],
            "category": item["category"],
            "expected_tier": item["expected_tier"],
            "score": None,
            "predicted_tier": None,
            "candidate_name": None,
            "matching_skills": [],
            "missing_skills": [],
            "experience_requirement_met": None,
            "verdict": None,
            "parsed_name": None,
            "parsed_email_present": None,
            "parsed_skill_count": None,
            "parsed_experience_years": None,
            "error": None,
        }
        start = time.monotonic()
        try:
            parsed = with_retries(
                lambda item=item: parse_resume(item["resume_text"]), item["id"]
            )
            record.update(
                {
                    "parsed_name": parsed.name,
                    "parsed_email_present": bool(parsed.email),
                    "parsed_skill_count": len(parsed.skills),
                    "parsed_experience_years": parsed.total_experience_years,
                }
            )
            time.sleep(sleep)
            result = with_retries(
                lambda parsed=parsed, item=item: final_score(
                    jobs[item["job_id"]], parsed
                ),
                item["id"],
            )
            record.update(
                {
                    "score": result.score,
                    "predicted_tier": tier_for_score(result.score),
                    "candidate_name": result.candidate_name,
                    "matching_skills": result.matching_skills,
                    "missing_skills": result.missing_skills,
                    "experience_requirement_met": result.experience_requirement_met,
                    "verdict": result.verdict,
                }
            )
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  FAILED: {record['error']}")
        record["seconds"] = round(time.monotonic() - start, 1)
        records.append(record)
        time.sleep(sleep)

    return {"records": records, "metrics": evaluate(records)}


def print_summary(name, metrics):
    print(
        f"{name}: n={metrics['n']} errors={metrics['errors']} "
        f"accuracy={metrics['accuracy']} macro_f1={metrics['macro_f1']} "
        f"spearman={metrics['spearman']} severe={metrics['severe_errors']} "
        f"high_false_positives={metrics['high_false_positives']}"
    )


def print_mismatches(name, records):
    misses = [
        record
        for record in records
        if record.get("error") is None
        and record["predicted_tier"] != record["expected_tier"]
    ]
    print(f"{name} mismatches ({len(misses)}):")
    for record in misses:
        print(
            f"  {record['id']}: expected={record['expected_tier']} "
            f"predicted={record['predicted_tier']} score={record['score']} "
            f"[{record['category']}]"
        )


def self_check(data):
    assert tier_for_score(70) == "high"
    assert tier_for_score(69.9) == "medium"
    assert tier_for_score(39.9) == "low"
    assert tier_for_score(0) == "low"

    job = data["jobs"]["backend_junior"]["baseline"]
    strong = baseline_score("Python SQL REST APIs Git 3 years", job)
    assert strong["score"] >= 80, strong
    empty = baseline_score("", job)
    assert empty["score"] == 0, empty
    assert empty["experience_met"] is False

    partial = baseline_score("postgresql 2 years", job)
    assert partial["required_coverage"] == 0.25, partial

    assert spearman([1, 2, 3], [10, 20, 30]) == 1.0
    assert spearman([1, 2, 3], [30, 20, 10]) == -1.0
    assert spearman([1, 2, 3], [10, 10, 10]) is None

    metrics = evaluate(
        [
            {"expected_tier": "high", "predicted_tier": "high", "score": 90, "error": None},
            {"expected_tier": "low", "predicted_tier": "low", "score": 10, "error": None},
            {"expected_tier": "medium", "predicted_tier": "high", "score": 75, "error": None},
            {"expected_tier": "low", "predicted_tier": "high", "score": 60, "error": None},
            {"expected_tier": "low", "predicted_tier": None, "score": None, "error": "boom"},
        ]
    )
    assert metrics["n"] == 4 and metrics["errors"] == 1, metrics
    assert metrics["accuracy"] == 0.5, metrics
    assert metrics["high_false_positives"] == 1, metrics
    assert metrics["severe_errors"] == 1, metrics
    print("self-check OK")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--system",
        choices=["both", "baseline", "llm"],
        default="both",
        help="Which system(s) to evaluate (default: both).",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Evaluate only the first N items."
    )
    parser.add_argument(
        "--sleep", type=float, default=2.0, help="Seconds between LLM calls."
    )
    parser.add_argument(
        "--self-check", action="store_true", help="Run assert-based checks and exit."
    )
    args = parser.parse_args()

    data = json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))
    if args.self_check:
        self_check(data)
        return

    run_baseline_system = args.system in ("both", "baseline")
    run_llm_system = args.system in ("both", "llm")

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "test_set": "eval/test_set.json",
        "n_items": len(data["items"]),
        "n_evaluated": min(args.limit, len(data["items"]))
        if args.limit
        else len(data["items"]),
    }

    if run_baseline_system:
        print("Running keyword baseline")
        results["baseline"] = run_baseline(data)
        print_summary("baseline", results["baseline"]["metrics"])
        print_mismatches("baseline", results["baseline"]["records"])

    if run_llm_system:
        print("\nRunning LLM pipeline")
        results["llm"] = run_llm(data, limit=args.limit, sleep=args.sleep)
        print_summary("llm", results["llm"]["metrics"])
        print_mismatches("llm", results["llm"]["records"])

    RESULTS_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nwrote {RESULTS_PATH}")


if __name__ == "__main__":
    main()
