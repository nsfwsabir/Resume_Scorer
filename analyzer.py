from pathlib import Path
from groq import Groq
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import os
import time
from pypdf import PdfReader
from docx import Document


load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("API Key not found!")

client=Groq(api_key=my_api_key)
model="openai/gpt-oss-120b"

job_description= """At Amazon, our tech isn't just a tool, it's your playground. Our engineers work on scalable systems, cloud services, and customer-facing products that operate at global scale. This is an environment where you learn by building. Whether you're creating cloud-native solutions, optimizing machine learning models, or building products that drive experiences for millions of customers around the globe, your work reaches the world, fast. You'll take ownership early, collaborate across teams and disciplines, and grow your skills as you tackle new problems. There's no single path forward here, with a chance to explore different directions and shape your journey as you go. This is where ambition meets opportunity and, where the impact of what you build helps define what comes next, for customers and for you.

What's in it for you? An internship at Amazon means real responsibility from day one. You'll build, test, and learn alongside people who want to see you succeed, while making an impact that reaches far beyond campus.

Our Software Development Engineer (SDE) interns use modern technology to solve complex problems while seeing their work's impact first-hand. The challenges SDE interns solve at Amazon are meaningful and influence millions of customers, sellers, and products globally, in an environment where development cycles are measured in weeks, not years.

As an SDE intern, you'll own the entire lifecycle of your code — from design through deployment and ongoing operations. This ownership mindset, combined with our commitment to operational excellence, ensures we deliver the highest quality solutions for our customers.

Basic Qualifications

This program is for students graduating in 2027

• Must be 18 years of age or older.
• Experience with at least one general-purpose programming language such as Java, Python, C++, C#, Go, Rust, or TypeScript.
• Experience with data structure implementation, basic algorithm development, and/or object-oriented design principles.
• Currently enrolled in a Bachelor's degree or above in Computer Science, Computer Engineering, Data Science, Information Systems, or related STEM fields OR completed a Bachelor's or Graduate degree in specified fields.

Preferred Qualifications

• Experience from previous technical internship(s) or demonstrated project experience
• Experience with one or more of the following: AI tools for development productivity, Cloud platforms (preferably AWS), Database systems (SQL and NoSQL), Contributing to open-source projects, Version control systems, Debugging and troubleshooting complex systems
• Demonstrated ability to learn and adapt to new technologies quickly
• Basic understanding of software development lifecycle (SDLC)
• Strong problem-solving and analytical skills
• Excellent written and verbal communication skills



Key job responsibilities
• Collaborate and communicate effectively with experienced cross-disciplinary Amazonians to design, build, and operate innovative products and services that delight our customers, while participating in technical discussions to drive solutions forward.
• Design and develop scalable solutions using cloud-native architectures and microservices in a large distributed computing environment.
• Participate in code reviews and contribute to technical documentation.
• Build and maintain resilient distributed systems that are scalable, fault-tolerant, and cost-effective.
• Leverage and contribute to the development of GenAI and AI-powered tools to enhance development productivity while staying current with emerging technologies.
• Write clean, maintainable code following best practices and design patterns.
• Work in an agile environment practicing CI/CD principles while participating in operational responsibilities.
• Demonstrate operational excellence through monitoring, troubleshooting, and resolving production issues.


A day in the life
Your 22-24 weeks of internship includes:

• Dedicated SDE mentor matched to your interests
• Real project ownership — you'll write code that ships to production
• Learning opportunities — access to virtual trainings on project management, personal brand, communication skills, and more
• Taking ownership of your career — a successful internship could lead to a full-time offer after finishing your studies
Basic Qualifications

- Bachelor's degree or above in computer science, computer engineering, or related field
Preferred Qualifications

- Bachelor's degree or equivalent

"""


class JobDesc(BaseModel):
    role:str
    required_skills:list[str]
    preffered_skils:list[str]
    minimum_experience: float | None
    educational_requirements: list[str]
    responsibilities: list[str]


jobdesc_schema= JobDesc.model_json_schema()


system_prompt= f"""
    You are an expert HR Assisstant

    Your job is to analyze job description and extract structured information from them.

    Return ONLY valid JSON matching this schema: {jobdesc_schema}

    IMPORTANT:
    DO NOT return the scheme itself.
    DO NOT return fields like "properties", "title" or "type".
    Fill the schema with actual information extracted from the job description.

    If minimum experience is not mentioned, return null.
    If information for a list is missing, return an empty list.
    DO NOT invent information. 

    """

user_prompt= f"""
    Analyze the following job description.

    {job_description}
    """

message_system= {
    "role": "system",
    "content": system_prompt
    }
message_user={
    "role": "user",
    "content": user_prompt
    }
response_format={
    "type":"json_object"
    }

messages=[message_system, message_user]
response=client.chat.completions.create(model=model, messages=messages, response_format=response_format)
answer=response.choices[0].message.content


job_data=json.loads(answer)
job=JobDesc(**job_data)

class MatchResult(BaseModel):
    score: float
    details: dict

class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: list[str] = []

class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None

    total_experience_years: float | None = None
    skills:list[str]=[]
    experiences:list[Experience]=[]
    education:list[str]=[]
    projects:list[str]=[]
    certifications:list[str]=[]

resume_schema= Resume.model_json_schema()


def read_pdf(file_path):
    reader= PdfReader(file_path)
    text=""
    for page in reader.pages:
        page_text= page.extract_text()
        if page_text:
            text+=page_text + "\n"
    return text

def read_docx(file_path):
    document= Document(file_path)
    text=""
    for para in document.paragraphs:
        if para.text.strip():
            text+=para.text + "\n"
    
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    text+=cell.text + "\n"
    return text

def read_resume(file_path):
    if file_path.suffix.lower() ==".pdf":
        return read_pdf(file_path)
    elif file_path.suffix.lower() ==".docx":
        return read_docx(file_path)
    else:
        return None 

def parse_resume(resume_text):
    system_prompt=f"""
        You are an expert parser.

        Extract information from the resume based on its meaning,
        not only based on exact section headings.

        Different resumes may use different headings.

        For example:
        - Experience
        - Professional Experience
        - Work History
        - Employment 
        - Internships

        They may all content relevant experience.

        Skills may also appear in the skills section, work experience, 
        internships or projects.

        Return ONLY valid JSON mathching this schema: 

        {resume_schema}

        Important rules:

        1. DO NOT invent information.
        2. If a value is not available, return null.
        3. If a list has not information, return an empty list.
        4. Internships inside experience.
        5. Extract skills mentioned across the entire resume.    
    
        """

    user_prompt=f"""
        Parse the following resume:

        {resume_text}    
    
        """
    
    message_system= {
    "role": "system",
    "content": system_prompt
    }
    message_user={
    "role": "user",
    "content": user_prompt
    }
    response_format={
    "type":"json_object"
    }
    messages=[message_system, message_user]
    response=client.chat.completions.create(model=model, messages=messages, response_format=response_format)
    raw_output=response.choices[0].message.content
    data=json.loads(raw_output)
    resume= Resume(**data)
    return resume



def final_score(job,resume):
    match_schema= MatchResult.model_json_schema()
    prompt= f"""
        You are an HR Recruiter.

        Compare the candidate's resume with the job description.

        JOB DESCRIPTION:
        {job.model_dump_json(indent=2)}

        CANDIDATE'S RESUME:
        {resume.model_dump_json(indent=2)}

        Return JSON matching this schema:

        {match_schema}

        Give me:

        1. Candidate's Name.
        2. Matching skills.
        3. Missing important skills.
        4. Wether experience requirement is met.
        5. Overall match percentage ranging 0 to 100.
        6. A short final verdict.

        Keep the response concise and easy to read.
        """
    message={
    "role": "user",
    "content": prompt
    }
    response_format={
    "type":"json_object"
    }
    messages=[message]
    response=client.chat.completions.create(model=model, messages=messages, response_format=response_format)
    data=json.loads(response.choices[0].message.content)
    return MatchResult(**data)


resume_folder=Path("resumes")
all_results=[]

for file_path in resume_folder.iterdir():
    if file_path.suffix.lower() not in [".pdf", ".docx"]:
        continue
    print("\n Processing:", file_path.name)
    resume_text=read_resume(file_path)
    parsed_resume=parse_resume(resume_text)
    time.sleep(5)
    result=final_score(job,parsed_resume)
    time.sleep(5)
    print("Score:", result.score)
    all_results.append({
        "name": parsed_resume.name,
        "score": result.score,
        "details": result.details
    })
all_results.sort(
        key=lambda candidate: candidate["score"],
        reverse=True
    )
top_2=all_results[:2]
if len(all_results) <=2:
    bottom_2=[]
else:
    bottom_2=all_results[-2:]

print("Top 2 Candidates")
for candidate in top_2:
    print(
        candidate["name"],
        "-",
        candidate["score"],
        "%"
        )
    print(candidate["details"])

print("Bottom 2 Candidates")
for candidate in bottom_2:
    print(
        candidate["name"],
        "-",
        candidate["score"],
        "%"
        )
    print(candidate["details"])

