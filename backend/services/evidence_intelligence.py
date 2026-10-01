import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
import re
from schemas.schemas import GeminiEvidenceAnalysis, GeminiVerificationAssessment
from utils.retry import with_gemini_retry

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

UNINSPECTED_NOTICE = "A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire."

PROHIBITED_PHRASES = [
    r"confirms?\s+the\s+existence",
    r"verified\s+deployment",
    r"verif(?:y|ies|ied)\s+(?:the\s+)?deployment",
    r"proves?\s+the\s+project",
    r"proves?\s+the\s+existence",
    r"proves?\s+(?:that\s+)?the\s+project",
    r"confirmed\s+deployment",
]

def sanitize_uninspected_text(text: str, has_retrieved_evidence: bool) -> str:
    """
    Enforces evidence integrity:
    If ProofHire only receives a URL but does NOT successfully retrieve and inspect the page/repository,
    do NOT say:
      - 'confirms the existence'
      - 'verified deployment'
      - 'proves the project'
    Instead say:
      - 'A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.'
    """
    if not text:
        return text
        
    if not has_retrieved_evidence:
        modified = text
        for pattern in PROHIBITED_PHRASES:
            modified = re.sub(pattern, UNINSPECTED_NOTICE, modified, flags=re.IGNORECASE)
        return modified
    return text

@with_gemini_retry("Evidence Agent")
def analyze_evidence_with_gemini(
    claim_text: str, 
    related_skills: list, 
    evidence_text: str, 
    job_context: str, 
    evidence_access_status: str = "submitted_only",
    model_name: str = "gemini-3.5-flash"
) -> GeminiEvidenceAnalysis:
    """Uses Gemini to analyze evidence against a claim with strict evidence-integrity rules."""
    
    prompt = f"""
    You are an expert AI Evidence Analyzer for "ProofHire AI".
    Analyze the supplied evidence for a candidate's professional claim.
    
    Claim: {claim_text}
    Related Skills: {', '.join(related_skills)}
    Target Job Context: {job_context}
    
    Evidence Provided:
    ---
    {evidence_text}
    ---
    
    EVIDENCE INTEGRITY AND ACCESS STATUS INSTRUCTIONS:
    1. ProofHire strictly distinguishes between:
       - Evidence submitted by the user
       - Evidence actually inspected/retrieved by the system (Evidence Access Status: {evidence_access_status})
    2. For URL evidence:
       If ProofHire only receives a URL but does NOT successfully retrieve and inspect the page/repository (i.e. access status is NOT 'retrieved'):
       - DO NOT say "confirms the existence"
       - DO NOT say "verified deployment"
       - DO NOT say "proves the project"
       - INSTEAD say: "A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire."
       - Only describe actual webpage/repository contents if ProofHire successfully retrieved those contents (access status is 'retrieved').
    3. For GitHub repository evidence:
       - GitHub repository existence does NOT prove that the candidate personally wrote every part of the repository.
       - ProofHire may say: "The repository contains evidence consistent with [skills] development."
       - Do NOT say: "The candidate definitely developed this."
       - Contributor information is factual public metadata; do NOT infer identity beyond available evidence.
       - Do NOT invent files, dependencies, or repository features not present in the provided evidence.
    
    Output strictly as JSON matching the schema. Do not output markdown code blocks.
    Answer:
    1. What information does this evidence contain?
    2. Which claimed skills does it support?
    3. Which claim does it relate to?
    4. Is the evidence relevant to the claim?
    5. What important information is still missing?
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiEvidenceAnalysis
            )
        )
        data = json.loads(response.text)
        
        is_retrieved = (evidence_access_status == "retrieved")
        data["information_contained"] = sanitize_uninspected_text(data.get("information_contained", ""), is_retrieved)
        data["relation_to_claim"] = sanitize_uninspected_text(data.get("relation_to_claim", ""), is_retrieved)
        
        return GeminiEvidenceAnalysis(**data)
    except Exception as e:
        raise Exception(f"Gemini API Error (Evidence Agent): {e}")

@with_gemini_retry("Verification Agent")
def verify_claim_with_gemini(
    claim_text: str, 
    evidence_texts: list, 
    resume_context: str, 
    has_retrieved_evidence: bool = False,
    model_name: str = "gemini-3.5-flash"
) -> GeminiVerificationAssessment:
    """Uses Gemini to verify a claim using all accumulated evidence."""
    
    # Rule: Claims with zero additional evidence remain Needs Verification
    if not evidence_texts:
        return GeminiVerificationAssessment(
            evidence_level="Needs Verification",
            evidence_used="Resume claim only (no additional evidence submitted)",
            what_supports="Stated in candidate resume.",
            what_is_missing="No additional supporting evidence has been provided yet.",
            next_step="Submit supporting evidence (code repository, deployment URL, or documentation) to begin verification."
        )
        
    evidence_str = "\n\n---\n\n".join(evidence_texts)
    
    prompt = f"""
    You are an expert AI Verification Agent for "ProofHire AI".
    Evaluate the strength of the provided evidence for the candidate's claim.
    
    Claim: {claim_text}
    Resume Context: {resume_context}
    
    Supplied Evidence:
    ---
    {evidence_str}
    ---
    
    EVIDENCE INTEGRITY & ACCESS RULES:
    1. ProofHire strictly distinguishes between:
       - Evidence submitted by the user
       - Evidence actually inspected/retrieved by the system
    2. For URL evidence:
       If ProofHire only receives a URL but does NOT successfully retrieve and inspect the page/repository:
       - DO NOT say "confirms the existence"
       - DO NOT say "verified deployment"
       - DO NOT say "proves the project"
       - INSTEAD say: "A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire."
       - Only describe actual webpage/repository contents if ProofHire successfully retrieved those contents.
    3. Allowed evidence levels (MUST be one of these five):
       - "Strong Evidence"
       - "Good Evidence"
       - "Moderate Evidence"
       - "Limited Evidence"
       - "Needs Verification"
    4. If the only additional evidence is an uninspected URL (submitted_only or retrieval_failed), it does NOT prove the project or confirm deployment. In such cases, the evidence level must remain "Needs Verification" or at most "Limited Evidence".
    5. These labels describe the strength of available supporting evidence, NOT whether the person is truthful.
    6. Never output: Fake, Fraud, Liar, False Candidate, Hire, Reject, Good Candidate, Bad Candidate.
    7. Never treat missing evidence as proof that a claim is false.
    8. Never infer personality, honesty, emotion, gender, age, race, religion, health, or other protected/personal traits.
    
    Output strictly as JSON matching the schema.
    Answer:
    1. Evidence Level
    2. Evidence Used
    3. What Supports the Claim
    4. What Is Still Missing
    5. Recommended Next Verification Step
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiVerificationAssessment
            )
        )
        data = json.loads(response.text)
        
        # Enforce integrity on output strings
        data["evidence_used"] = sanitize_uninspected_text(data.get("evidence_used", ""), has_retrieved_evidence)
        data["what_supports"] = sanitize_uninspected_text(data.get("what_supports", ""), has_retrieved_evidence)
        data["what_is_missing"] = sanitize_uninspected_text(data.get("what_is_missing", ""), has_retrieved_evidence)
        data["next_step"] = sanitize_uninspected_text(data.get("next_step", ""), has_retrieved_evidence)
        
        # Ensure allowed evidence levels
        allowed_levels = ["Strong Evidence", "Good Evidence", "Moderate Evidence", "Limited Evidence", "Needs Verification"]
        if data.get("evidence_level") not in allowed_levels:
            data["evidence_level"] = "Needs Verification"
            
        # If no retrieved evidence exists and only uninspected URL/text was supplied, cap at Limited Evidence or Needs Verification
        if not has_retrieved_evidence and data["evidence_level"] in ["Strong Evidence", "Good Evidence"]:
            data["evidence_level"] = "Limited Evidence"
            
        return GeminiVerificationAssessment(**data)
    except Exception as e:
        raise Exception(f"Gemini API Error (Verification Agent): {e}")
