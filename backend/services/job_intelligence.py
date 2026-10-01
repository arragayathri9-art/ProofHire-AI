import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
from schemas.schemas import GeminiJobExtraction
from utils.retry import with_gemini_retry

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

@with_gemini_retry("Job Intelligence")
def analyze_job_with_gemini(job_title: str, company: str, job_description: str, model_name: str = "gemini-3.5-flash") -> GeminiJobExtraction:
    """Uses Gemini to parse the job description into structured JSON."""
    if not job_description:
        return GeminiJobExtraction(job_title=job_title)
        
    prompt = f"""
    You are an expert AI Job Description Analyzer for "ProofHire AI".
    Your task is to extract information from the following job description and format it STRICTLY as JSON.
    Do NOT hallucinate or invent any requirements that are not supported by the job description.
    
    Extract job title, required skills, preferred skills, minimum experience, education requirements, responsibilities, technical requirements, and other requirements.
    
    Job Title: {job_title}
    Company: {company}
    
    Job Description:
    ---
    {job_description}
    ---
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiJobExtraction
            )
        )
        data = json.loads(response.text)
        return GeminiJobExtraction(**data)
    except Exception as e:
        raise Exception(f"Gemini API Error (Job): {e}")
