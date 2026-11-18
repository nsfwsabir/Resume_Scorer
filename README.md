# Resume Scorer

An AI-powered resume screening and ranking tool built with Python. Given a job description and a folder of candidate resumes, Resume Scorer extracts structured information from both the job description and resumes, evaluates candidate-job fit, and ranks candidates based on their match score.

The project uses the Groq API with `openai/gpt-oss-120b` for semantic analysis and supports both PDF and DOCX resumes.

## Features

- 📝 **Multi-line Job Description Input**\
  Paste a complete job description directly into the terminal and type `END` when finished.

- 📄 **PDF Resume Parsing**\
  Extracts text from PDF resumes using `pypdf`.

- 📄 **DOCX Resume Parsing**\
  Extracts text from Word documents, including tables, using `python-docx`.

- 🤖 **AI-Powered Information Extraction**\
  Uses an LLM to extract structured information from job descriptions and resumes.

- 🎯 **Resume-to-Job Matching**\
  Compares candidate information against job requirements.

- 📊 **Match Score**\
  Generates an overall match score between 0 and 100.

- 🔎 **Skill Analysis**\
  Identifies matching and missing skills.

- 💼 **Experience Evaluation**\
  Determines whether the candidate meets the experience requirement.

- 🏆 **Candidate Ranking**\
  Sorts candidates by match score and displays the top 2 and bottom 2 candidates.

## How It Works

The application follows a simple pipeline:

```text
                 Job Description
                        │
                        ▼
              AI Job Description Parser
                        │
                        ▼
              Structured Job Requirements
                        │
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
   Resume 1                         Resume N
        │                               │
        ▼                               ▼
   PDF/DOCX Parser                PDF/DOCX Parser
        │                               │
        └───────────────┬───────────────┘
                        ▼
                 AI Resume Parser
                        │
                        ▼
              Structured Resume Data
                        │
                        ▼
                AI Match Analysis
                        │
                        ▼
                  Match Score
                        │
                        ▼
                 Candidate Ranking
```

### 1. Job Description Analysis

The user pastes a job description into the terminal.

The application extracts:

- Role
- Required skills
- Preferred skills
- Minimum experience
- Educational requirements
- Responsibilities

### 2. Resume Processing

The application scans the `resumes/` directory and processes:

- `.pdf`
- `.docx`

For each resume, it extracts:

- Candidate name
- Email
- Phone
- Total experience
- Skills
- Work experience
- Education
- Projects
- Certifications

### 3. Candidate Matching

Each structured resume is compared against the structured job description.

The model evaluates:

- Matching skills
- Missing important skills
- Experience requirement
- Overall job fit
- Final recommendation

### 4. Ranking

Candidates are sorted by their match score.

The application displays:

- Top 2 candidates
- Bottom 2 candidates

## Tech Stack

- **Python**
- **Groq API**
- **GPT-OSS 120B**
- **Pydantic** — structured data validation
- **pypdf** — PDF text extraction
- **python-docx** — DOCX text extraction
- **python-dotenv** — environment variable management

The repository currently targets Python 3.14+ and declares these dependencies in `pyproject.toml`.

## Project Structure

```text
Resume_Scorer/
│
├── analyzer.py
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── README.md
├── EVALUATION.md
│
├── eval/
│   ├── test_set.json
│   ├── run_eval.py
│   └── results.json
│
└── resumes/
    ├── candidate1.pdf
    ├── candidate2.pdf
    ├── candidate3.docx
    └── ...
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/nsfwsabir/Resume_Scorer.git
cd Resume_Scorer
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**macOS/Linux**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

If you are using `pip`:

```bash
pip install groq pydantic pypdf python-docx python-dotenv
```

Or, if you are using the project's `pyproject.toml` with a compatible environment:

```bash
pip install -e .
```

## Groq API Key

The application requires a Groq API key.

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Do **not** commit your `.env` file to GitHub.

Your `.gitignore` should contain:

```gitignore
.env
.venv/
__pycache__/
```

## Adding Resumes

Create a directory named `resumes` in the project root:

```text
Resume_Scorer/
│
├── analyzer.py
│
└── resumes/
    ├── John_Doe.pdf
    ├── Jane_Smith.pdf
    └── Alex_Brown.docx
```

The application automatically processes `.pdf` and `.docx` files in this directory.

## Usage

Run:

```bash
python analyzer.py
```

The application will prompt you to enter the job description:

```text
Paste the JOB Description.
Type END on a new line when finished.
```

You can paste multiple lines:

```text
We are looking for a Python Developer.

Requirements:
- 3+ years of Python experience
- Strong SQL knowledge
- Experience with REST APIs
- Django or Flask experience
- Good problem-solving skills

Responsibilities:
- Build backend applications
- Develop REST APIs
- Work with databases
- Collaborate with engineering teams
END
```

Once `END` is entered, the application processes the resumes.

Example output:

```text
Processing: John_Doe.pdf
Score: 87.0

Processing: Jane_Smith.pdf
Score: 74.0

Processing: Alex_Brown.docx
Score: 92.0


===== TOP 2 CANDIDATES =====

Alex Brown - 92.0%
Matching skills: ['Python', 'SQL', 'REST APIs', 'Django']
Missing skills: ['Docker']
Experience requirement met: True
Verdict: Strong match for the position.

John Doe - 87.0%
Matching skills: ['Python', 'SQL', 'REST APIs']
Missing skills: ['Django']
Experience requirement met: True
Verdict: Good match with some skill gaps.


===== BOTTOM 2 CANDIDATES =====

John Doe - 87.0%
...

Jane Smith - 74.0%
...
```

## Input / Output Contract

### Inputs

| Input | Where | Required | Rules |
|---|---|---|---|
| Job description | stdin | Yes | Multi-line text. A line that is exactly `END` (case-insensitive, surrounding whitespace ignored) ends input. Empty input is not rejected. |
| Resumes | `resumes/` in the working directory | Yes (may be empty) | Only `.pdf` and `.docx`; other extensions are skipped. Files are processed in directory order, not sorted. Subdirectories are not scanned. |
| Groq API key | `GROQ_API_KEY` in the environment or `.env` in the working directory | Yes | Checked lazily at the first LLM call. Missing key raises `ValueError` and aborts. |
| Model | hard-coded | — | `openai/gpt-oss-120b`. Not configurable by CLI or environment. |

The application takes no command-line arguments. Each resume is evaluated independently against the same parsed job description; candidates are never compared with each other beyond the final sort.

### Processing

- Job description text → one LLM extraction call → `JobDesc`.
- Each resume file → text extraction (`pypdf` or `python-docx`) → one LLM parsing call → `Resume`.
- Each `Resume` + `JobDesc` → one LLM scoring call → `MatchResult`.
- The tool sleeps 5 seconds after each resume parse and each score.

PDF extraction reads only the text layer; scanned/image-only PDFs produce empty or partial text and are not OCR'd. DOCX extraction reads paragraphs and tables only (not headers, footers, or text boxes).

### Outputs

The tool writes **only to stdout**. It does not create reports, JSON, or any other file, and it does not persist partial results.

Per-resume progress:

```text
 Processing: <filename>
Score: <float>
```

Final ranking:

```text
===== TOP 2 CANDIDATES =====

<name> - <score>%
Matching skills: <list>
Missing skills: <list>
Experience requirement met: <bool>
Verdict: <text>

===== BOTTOM 2 CANDIDATES =====

<name> - <score>%
...
```

Output semantics:

| Field | Meaning |
|---|---|
| `score` | LLM-generated match percentage, 0–100. Higher is better. Not calibrated and not a probability. |
| `TOP 2` | The two highest scores, always printed (fewer if fewer resumes). |
| `BOTTOM 2` | The two lowest scores, printed only when more than two resumes exist; otherwise the heading is printed with no entries. |
| `name` | Candidate name as parsed by the LLM; `None` if extraction failed or the resume is unreadable. |
| `Matching / missing skills` | LLM judgment, not computed from the keyword baseline. |
| `Experience requirement met` | LLM judgment against `minimum_experience` from the job description. |

### Failure behaviour

- There are no retries on API errors, rate limits, malformed JSON, or schema validation failures.
- Any unhandled error aborts the run with a traceback and a non-zero exit code.
- Resumes already processed are lost because results are held in memory only.
- A zero-resume folder is not an error: both ranking sections print empty and the process exits 0.

## Data Models

### Job Description

The job description is converted into structured data containing:

```text
role
required_skills
preferred_skills
minimum_experience
educational_requirements
responsibilities
```

### Resume

Each resume is converted into structured data containing:

```text
name
email
phone
total_experience_years
skills
experiences
education
projects
certifications
```

### Match Result

The final comparison produces:

```text
score
candidate_name
matching_skills
missing_skills
experience_requirement_met
verdict
```

## Scoring

The current implementation uses the LLM to evaluate the overall candidate-job match and return a score from **0 to 100**.

The score is intended as a screening aid rather than a definitive hiring decision.

A higher score indicates that the candidate's resume is more closely aligned with the requirements extracted from the job description.

## Evaluation

The system is evaluated on a fixed, labeled set rather than on the four sample resumes.

- **Test set:** [`eval/test_set.json`](eval/test_set.json) — 32 resume/JD pairs across 4 roles (8 each), labeled `high`, `medium`, or `low` for shortlisting. It includes edge cases: empty/scanned text, keyword stuffing, under-experienced candidates, transferable stacks, unrelated domains, and a non-English resume.
- **Baseline:** a deterministic keyword scorer using required/preferred skill coverage and a years regex, mapped to the same 0–100 scale and tier cutoffs.
- **Harness:** [`eval/run_eval.py`](eval/run_eval.py). It reports tier accuracy, macro F1, Spearman rank correlation, mean band error, severe errors (two tiers off), and high false positives (a `low` candidate predicted `high`).

Protocol, results, baseline comparison, and error analysis: **[EVALUATION.md](EVALUATION.md)**.

On the 32-item set, the LLM pipeline reaches **75.0% tier accuracy** versus **62.5%** for the keyword baseline (macro F1 0.750 vs 0.626; Spearman 0.892 vs 0.842). All errors by both systems are over-predictions, never under-predictions.

```bash
python eval/run_eval.py --system baseline   # no API key needed
python eval/run_eval.py                     # baseline + LLM, needs GROQ_API_KEY
python eval/run_eval.py --self-check        # assert-based checks of the metric code
```

## Important Considerations

### AI-generated scores are not objective hiring decisions

The score is generated using an LLM and should be treated as an assistive metric rather than an authoritative assessment.

Recruiters should review the original resume and job requirements before making hiring decisions.

### Resume extraction can vary

PDF text extraction depends on how the PDF was created. Scanned/image-only PDFs may not produce useful text without OCR.

### Semantic matching

The system uses an LLM to understand skills and experience rather than relying solely on exact keyword matching. This allows related concepts to be considered during candidate evaluation.

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/your-feature
```

3. Make your changes
4. Commit your changes

```bash
git commit -m "Add your feature"
```

5. Push the branch

```bash
git push origin feature/your-feature
```

6. Open a Pull Request

## Author

**nsfwsabir**

GitHub:\
[https://github.com/nsfwsabir](https://github.com/nsfwsabir)

## Project

**Resume Scorer**

An AI-powered tool for analyzing job descriptions, parsing resumes, matching candidates to job requirements, and ranking applicants.
