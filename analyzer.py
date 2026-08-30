from pathlib import Path
from groq import Groq
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import os
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


job_data=json.loads(raw_json)
job=JobDesc(**job_data)

print(job.minimum_experience)
print(job.educational_requirements)

class MatchResult(BaseModel):
    score: float
    detials: dict

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

#def final_score(job,resume):



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
    for para in document.paragraph:
        if para.text.strip()
            text+=para.text + "\n"
    
    for table in document.tables:
        for row in document.rows:
            for cell in document.cell:
                if cell.text.strip():
                    text+=cell.text + "\n"
    return text

def read_resume(file_path):
    if file_path.suffix.lower() +=".pdf":
        read_pdf(file_path)
    elif file_path.suffix.lower() ==".docx":
        read_docx(file_path)
    else:
        return None 




