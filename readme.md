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

## License

No license has currently been specified for this repository.

If you intend to allow others to use, modify, and redistribute the project, consider adding an appropriate open-source license.

## Author

**nsfwsabir**

GitHub:\
[https://github.com/nsfwsabir](https://github.com/nsfwsabir)

## Project

**Resume Scorer**

An AI-powered tool for analyzing job descriptions, parsing resumes, matching candidates to job requirements, and ranking applicants.
