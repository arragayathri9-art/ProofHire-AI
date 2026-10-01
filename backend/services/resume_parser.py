import os
import fitz  # PyMuPDF
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
from schemas.schemas import GeminiResumeExtraction
from utils.retry import with_gemini_retry

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file using PyMuPDF."""
    text = ""
    try:
        with fitz.open(file_path) as pdf_doc:
            for page in pdf_doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text.strip()

@with_gemini_retry("Resume Intelligence")
def analyze_resume_with_gemini(resume_text: str, model_name: str = "gemini-3.5-flash") -> GeminiResumeExtraction:
    """Uses Gemini to parse the raw resume text into structured JSON."""
    if not resume_text:
        return GeminiResumeExtraction()
        
    prompt = f"""
    You are an expert AI Resume Analyzer for "ProofHire AI".
    Your task is to extract information from the following resume text and format it STRICTLY as JSON.
    Do NOT hallucinate or invent any information that is not present in the text.
    If a field is not available, leave it as null or an empty list [].
    
    Extract candidate name, email, phone, location, summary, education, experience, projects, skills, certifications, links, and professional claims.
    
    Resume Text:
    ---
    {resume_text}
    ---
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiResumeExtraction
            )
        )
        data = json.loads(response.text)
        return GeminiResumeExtraction(**data)
    except Exception as e:
        raise Exception(f"Gemini API Error: {e}")
