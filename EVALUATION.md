# Evaluation

This document reports how the resume scorer was tested, how it compares with a keyword baseline, and where it fails.

## Scope

The evaluation asks one question: **does the system put a candidate in the right shortlist tier — `high`, `medium`, or `low` — for a given job description?**

It measures the LLM extraction + scoring path. The evaluation harness passes resume text directly to `parse_resume()`, so PDF/DOCX file extraction (`read_pdf`, `read_docx`) is not exercised; an empty-resume case is simulated by passing an empty string. Latency, cost, and real hiring outcomes are out of scope.

## Test set

[`eval/test_set.json`](eval/test_set.json) contains **32 labeled resume/JD pairs**: 4 job descriptions × 8 resumes each.

| Job description | Minimum experience | Required skills | Items | high / medium / low |
|---|---|---|---|---|
| Junior Backend Developer (Python) | 1 year | Python, SQL, REST APIs, Git | 8 | 2 / 3 / 3 |
| Data Analyst | 2 years | SQL, Excel, Python with pandas, data visualization | 8 | 2 / 3 / 3 |
| Senior Frontend Engineer | 3 years | JavaScript, React, HTML, CSS | 8 | 2 / 3 / 3 |
| Machine Learning Engineer | 3 years | Python, PyTorch/TensorFlow, ML, MLOps | 8 | 2 / 3 / 3 |

Label distribution: **8 high, 12 medium, 12 low**.

### Labeling rubric

Each item carries the label a recruiter should assign before seeing the model output. The label answers "should this candidate be shortlisted?"

- **high** — yes. Meets the minimum experience and most required skills, with professional evidence and a relevant background.
- **medium** — worth a screen. Transferable background or a notable gap; within about one year of the experience minimum.
- **low** — no. Core requirements absent, more than one year short, unrelated domain, or no extractable content.

Incidental or coursework-only use of a skill does not count as professional evidence. The per-item `notes` field records the reason for the label.

### Deliberate stress cases

| Category | Items | What it tests |
|---|---|---|
| `strong_match` | 8 | Correctly ranking clearly qualified candidates |
| `missing_skills` | 6 | One or two required skills absent |
| `unrelated_domain` | 5 | Adjacent job titles with little transferable work |
| `transferable_stack` | 4 | Shared keywords but a different primary stack |
| `under_experienced` | 4 | Strong skills but below the years minimum |
| `weak_evidence` | 2 | Skills mentioned only as tutorials or incidental use |
| `empty_extraction` | 1 | Scanned resume with no extractable text |
| `keyword_stuffing` | 1 | Every skill listed, zero professional experience |
| `cross_language` | 1 | Non-English resume against an English job description |

### Format

Each item has `id`, `job_id`, `category`, `expected_tier`, `notes`, and `resume_text`. Each job has its raw `text` plus a `baseline` block with required/preferred skill aliases and the minimum years. The baseline block is written independently of the LLM, so the baseline never benefits from LLM extraction.

## Systems compared

### LLM pipeline (production)

The production pipeline: parse the job description, parse each resume, score each pair. Prompts and model (`openai/gpt-oss-120b` via Groq) are unchanged. The job description is parsed once per role and cached for the eight items, mirroring the single-JD production run. Each item therefore uses two LLM calls (resume parse, match score).

### Keyword baseline

A deterministic scorer that needs no API:

```text
required_coverage   = required skills found in resume / required skills
preferred_coverage  = preferred skills found in resume / preferred skills
experience_met      = explicit "N years" in resume >= job minimum
score               = 100 × (0.7 × required_coverage
                           + 0.2 × preferred_coverage
                           + 0.1 × experience_met)
```

Skill matching is alias-based and case/punctuation-insensitive (`postgres` counts for SQL, `power bi` for data visualization). The years check uses the largest explicit `N years` mention; it does not parse date ranges or other languages.

### Tier mapping

Both systems use the same cutoffs, applied to their 0–100 score:

| Score | Tier |
|---|---|
| 70–100 | high |
| 40–69 | medium |
| 0–39 | low |

## Metrics

| Metric | Definition |
|---|---|
| Tier accuracy | Fraction of items whose predicted tier equals the label |
| Macro F1 | Unweighted mean of per-tier F1; treats all three tiers equally |
| Spearman ρ | Rank correlation between expected tier (0/1/2) and the system's score |
| Mean band error | Mean distance in tiers between predicted and expected |
| Severe errors | Items off by two tiers |
| High false positives | Items labeled `low` but predicted `high`; the costly failure for screening |
| Errors | Items where the system crashed or returned invalid output |

## Protocol

- One run per system on 2026-11-18.
- Model: `openai/gpt-oss-120b` via Groq, provider default sampling settings (temperature is not set). The run is therefore **not bit-for-bit reproducible**.
- The LLM run used a 2-second pause between calls to stay under provider rate limits; the production tool sleeps 5 seconds. This affects runtime only.
- Failed items are recorded with their exception, excluded from accuracy/F1/ρ, and counted separately.
- Baseline results are deterministic.
- Commands:

```bash
python eval/run_eval.py --system baseline
python eval/run_eval.py --system both
```

- Raw output: [`eval/results.json`](eval/results.json).

<!-- RESULTS -->

## Results

Both systems completed all 32 items with no crashes, invalid JSON, or schema errors. The LLM run took **486.5 seconds** (about 8.1 minutes) including the deliberate 4 seconds of sleep per item; the baseline is instant.

### Headline comparison

| Metric | Keyword baseline | LLM pipeline | Change |
|---|---|---|---|
| Tier accuracy | 62.5% (20/32) | **75.0%** (24/32) | +12.5 pp |
| Macro F1 | 0.626 | **0.750** | +0.124 |
| Spearman ρ | 0.842 | **0.892** | +0.050 |
| Mean band error | 0.438 | **0.281** | −0.157 |
| Severe errors (two tiers off) | 2 | **1** | −1 |
| High false positives (`low` → `high`) | 2 | **1** | −1 |

### Per-tier results

| Tier | Baseline precision / recall / F1 | LLM precision / recall / F1 |
|---|---|---|
| low | 1.000 / 0.583 / 0.737 | 1.000 / 0.750 / 0.857 |
| medium | 0.625 / 0.417 / 0.500 | 0.778 / 0.583 / 0.667 |
| high | 0.471 / 1.000 / 0.640 | 0.571 / 1.000 / 0.727 |

Confusion matrices (rows = expected, columns = predicted):

| Baseline | low | medium | high |
|---|---|---|---|
| low | 7 | 3 | 2 |
| medium | 0 | 5 | 7 |
| high | 0 | 0 | 8 |

| LLM | low | medium | high |
|---|---|---|---|
| low | 9 | 2 | 1 |
| medium | 0 | 7 | 5 |
| high | 0 | 0 | 8 |

### Where the improvement comes from

The LLM is better on the cases the baseline cannot reason about:

| Category | Items | Baseline accuracy | LLM accuracy |
|---|---|---|---|
| `strong_match` | 8 | 1.00 | 1.00 |
| `unrelated_domain` | 5 | 0.80 | 1.00 |
| `transferable_stack` | 4 | 0.25 | 0.50 |
| `under_experienced` | 4 | 0.00 | 0.50 |
| `weak_evidence` | 2 | 0.00 | 0.50 |
| `missing_skills` | 6 | 0.83 | 0.67 |
| `keyword_stuffing` | 1 | 0.00 | 0.00 |
| `empty_extraction` | 1 | 1.00 | 1.00 |
| `cross_language` | 1 | 1.00 | 1.00 |

Both systems found all eight strong candidates (high recall = 1.000). The gain is in rejecting the weaker ones: the baseline labeled 17 of 32 candidates `high`, the LLM labeled 14. The LLM uses the `low` band for clearly unrelated or empty resumes (scores from 0.0 to 30.0), but partially relevant resumes cluster at the 40–45 boundary, which is where two `low` items were misclassified as `medium`.

The baseline is marginally better on `missing_skills` (5/6 vs 4/6) because a missing required skill directly reduces its coverage term, while the LLM sometimes treats 3 of 4 required skills as a strong match.

## Error analysis

Every error made by either system is an **over-prediction** — both never place a candidate below the expected tier. The LLM's eight mismatches:

| Item | Label → prediction | Score | What happened |
|---|---|---|---|
| `backend-04` | medium → high | 80.0 | Java engineer with Python only as automation scripting. The parser counted Python, SQL, REST, and Git as matching and the score ignored that Python is a secondary tool. The verdict also lists "relational databases" as missing even though SQL is present. |
| `backend-05` | medium → high | 77.0 | New grad with 0.5 years against a 1-year minimum. The system correctly returned `experience_requirement_met: false` and wrote "falls short on experience", then scored 77 (high band). |
| `backend-06` | low → medium | 40.0 | PHP developer with no Python. The verdict says "not a suitable fit" and lists Python and SQL as missing, but the score sits exactly on the medium boundary. |
| `data-03` | medium → high | 83.0 | Operations analyst with Excel and SQL but no Python. Python is in `missing_skills`; the score is still 83. |
| `data-04` | medium → high | 80.0 | 1.5 years against a 2-year minimum. `experience_requirement_met: false`, verdict says it does not meet the requirement, score 80. |
| `data-05` | medium → high | 85.0 | Financial analyst with SQL, Excel, and Power BI but no Python. Python is listed as missing; score 85. |
| `data-08` | low → high | 75.0 | Coursework-only skills list with zero professional experience. The parser extracted no years and the system flagged the experience requirement as not met, but still scored 75. This is the only severe error (two tiers). |
| `frontend-08` | low → medium | 45.0 | Java engineer who touched HTML/CSS on admin screens. No JavaScript or React; scored 45 for the two peripheral skills. |

### What the failures have in common

1. **Score and verdict disagree.** In five of the eight errors the model explicitly states the missing skill or unmet experience in the verdict, then returns a high-band score anyway. The prompt asks for a score, a boolean, and a verdict, but does not tell the model how they should constrain each other.
2. **The experience flag is not reflected in the score.** Both under-experience cases return `experience_requirement_met: false` and scores of 77 and 80. The boolean is treated as reporting metadata rather than as a scoring input.
3. **Professional evidence is not separated from coursework.** The keyword-stuffed new grad lists every required tool and receives 75 despite no job history. The parser's `total_experience_years` is null and the verdict admits the gap, but the skill list dominates.
4. **Partial-overlap floor.** The `low` band is reachable: unrelated and empty resumes score 0.0–30.0. But clear rejects with some overlap (`backend-06`, `frontend-08`) land at 40.0–45.0, exactly on the medium boundary. The band boundary is poorly calibrated for partial matches, not unreachable.
5. **Depth is not modelled.** A primary Java developer who wrote Python scripts gets full Python credit (`backend-04`); a designer's HTML/CSS prototypes earn 3 of 4 required frontend skills (`frontend-05`, correctly medium but for the wrong reason). The model matches mentions, not evidence of ownership.

### What worked

- **Empty extraction is handled safely.** The empty resume scored 0.0 (`low`) without an exception.
- **No strong candidate was missed.** All eight `strong_match` items landed in `high` in both systems.
- **Cross-language input did not crash or confuse the pipeline.** The Portuguese resume was scored `low`, matching its label.
- **Extraction was complete on all 31 non-empty resumes**: a name, email flag, and non-empty skill list were returned for every one.
- **Unrelated domains were rejected.** All five `unrelated_domain` items were `low`, up from 4/5 for the baseline.

### Implication

The pipeline is **lenient, not conservative**. It is safer for surfacing candidates a recruiter might miss than for rejecting candidates automatically. Any deployment should use the score for ranking only, keep the `experience_requirement_met` flag visible, and require a human review before rejection. Fixing the score/verdict inconsistency and giving the experience flag an explicit weight are the two changes most likely to reduce the remaining errors.


## Threats to validity

- **Small, synthetic set.** 32 items is enough to expose failure modes, not to estimate production accuracy. The resumes are short and were written for this evaluation.
- **Labels are subjective.** The rubric reduces ambiguity, but "worth a screen" is a judgment. There is no second annotator and no inter-annotator agreement.
- **Test-set authorship bias.** The same author wrote the prompts, the labels, and the baseline aliases.
- **Single run.** LLM sampling is not fixed; a rerun can move an item across a tier boundary near 70 or 40.
- **File extraction is untested.** The harness bypasses PDF/DOCX readers. The scanned-resume case is a simulated empty string.
- **Baseline is intentionally simple.** It is a floor for comparison, not the strongest possible non-LLM system. A tuned TF-IDF or embedding baseline would be stronger.
- **No cost or latency comparison.** The LLM path makes 68 API calls for this set; the baseline makes none.

## Reproduce

```bash
python eval/run_eval.py --self-check       # validate metric/baseline code
python eval/run_eval.py --system baseline  # instant, no key
python eval/run_eval.py --system both      # needs GROQ_API_KEY
```

The harness writes `eval/results.json` with per-item records (scores, predicted tiers, parsed names, skills, years, verdicts, and errors), so the analysis below can be re-derived.
