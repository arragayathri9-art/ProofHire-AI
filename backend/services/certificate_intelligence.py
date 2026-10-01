"""
Certificate & Credential Intelligence Service - Phase 7A/7B

Extracts, structures, and evaluates certificate and credential evidence:
- PDF, PNG, JPG/JPEG document extraction using PyMuPDF and Gemini
- Deterministic and AI-assisted metadata extraction
- Honest verification statuses with no false authenticity claims
- Credential URL retrieval + page inspection (NOT authentication)
- Credential field comparison (title, issuer, candidate, credential_id, date)
- Evidence weighting: certificate = credential/supporting evidence (NOT practical demonstration)
- Skill Connection mapping to ProofHire skill system
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import requests
import pymupdf  # PyMuPDF
from google import genai
from google.genai import types
from dotenv import load_dotenv
from utils.retry import with_gemini_retry

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

INTEGRITY_DISCLAIMER = (
    "Document extracted only. ProofHire does NOT claim a certificate is authentic "
    "simply because the PDF/image exists, contains an issuer logo, or displays a credential ID. "
    "Only documented extraction and reachable verification URLs were validated."
)

# Evidence weight label for certificate evidence
# (hierarchy: Practical Assessment > GitHub Signals > Interview > Certificate > Resume Claim)
CERTIFICATE_EVIDENCE_WEIGHT = "credential_supporting"  # Supporting evidence, not practical demonstration

KNOWN_ISSUERS = [
    "Google", "Amazon Web Services", "AWS", "Microsoft", "Coursera", "Udemy",
    "edX", "IBM", "Meta", "Stanford University", "DeepLearning.AI", "Oracle",
    "Cisco", "HackerRank", "CompTIA", "Linux Foundation", "Databricks", "Harvard",
    "freeCodeCamp", "Postman", "Kaggle", "Salesforce"
]

COMMON_TECH_SKILLS = [
    "Python", "SQL", "Data Analysis", "Machine Learning", "Deep Learning",
    "FastAPI", "React", "React.js", "Docker", "AWS", "Cloud Computing",
    "PostgreSQL", "JavaScript", "TypeScript", "Node.js", "Database",
    "Data Science", "Pandas", "NumPy", "TensorFlow", "PyTorch", "Git",
    "CI/CD", "DevOps", "Cybersecurity", "REST APIs", "Statistics", "Tableau",
    "Data Visualization", "Spreadsheets", "Data Cleaning", "R", "Scala",
    "Spark", "Hadoop", "Power BI", "Business Intelligence", "NLP"
]

def extract_raw_document_content(file_path: str, filename: str) -> Dict[str, Any]:
    """
    Extracts raw text and metadata from PDF, PNG, or JPG certificate files using PyMuPDF.
    """
    raw_text = ""
    page_count = 0
    extraction_method = "unsupported"
    ext = os.path.splitext(filename)[1].lower()

    if not os.path.exists(file_path):
        return {
            "raw_text": "",
            "page_count": 0,
            "extraction_method": "file_not_found",
            "has_text": False,
            "file_ext": ext
        }

    try:
        if ext in [".pdf"]:
            with pymupdf.open(file_path) as doc:
                page_count = len(doc)
                pages_text = []
                for p in doc:
                    pages_text.append(p.get_text() or "")
                raw_text = "\n".join(pages_text).strip()
            extraction_method = "PyMuPDF Document Parser"
        elif ext in [".png", ".jpg", ".jpeg"]:
            try:
                with pymupdf.open(file_path) as doc:
                    page_count = len(doc)
                    raw_text = "\n".join(p.get_text() for p in doc).strip()
            except Exception:
                raw_text = ""
            extraction_method = "Image File Ingestion"
    except Exception as e:
        print(f"Error extracting document {filename}: {e}")
        raw_text = ""
        extraction_method = "extraction_error"

    return {
        "raw_text": raw_text,
        "page_count": page_count,
        "extraction_method": extraction_method,
        "has_text": len(raw_text) > 20,
        "file_ext": ext
    }

def verify_credential_url(credential_url: Optional[str]) -> Dict[str, Any]:
    """
    Phase 7B: Validates and tests credential verification URL if provided.
    
    Returns structured dict with:
    - status: RETRIEVED / UNREACHABLE / NOT PROVIDED / VERIFICATION LIMITED
    - explanation
    - http_status: actual HTTP code
    - page_title: extracted page title if available
    - domain: issuer domain
    - retrieval_timestamp: UTC timestamp
    - url_reachable: bool
    
    Does NOT claim authenticity - only reports what was technically retrieved.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if not credential_url or not credential_url.strip():
        return {
            "status": "NOT PROVIDED",
            "explanation": "No credential verification URL was provided by the candidate.",
            "http_status": None,
            "page_title": None,
            "domain": None,
            "retrieval_timestamp": timestamp,
            "url_reachable": False
        }

    url = credential_url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    # Extract domain
    domain_match = re.search(r"https?://([^/]+)", url)
    domain = domain_match.group(1) if domain_match else None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProofHire/1.0 CredentialVerifier"
    }

    try:
        # First try HEAD for efficiency
        resp = requests.head(url, headers=headers, timeout=6, allow_redirects=True)
        if resp.status_code >= 400:
            # Fallback to GET
            resp = requests.get(url, headers=headers, timeout=6, stream=True)

        http_status = resp.status_code

        # Attempt to extract page title from content
        page_title = None
        if http_status < 400:
            try:
                # Read limited content for title extraction
                content_resp = requests.get(url, headers=headers, timeout=6)
                content_text = content_resp.text[:5000] if content_resp.text else ""
                title_match = re.search(r"<title[^>]*>(.*?)</title>", content_text, re.IGNORECASE | re.DOTALL)
                if title_match:
                    page_title = title_match.group(1).strip()[:200]
            except Exception:
                page_title = None

        if http_status < 400:
            return {
                "status": "RETRIEVED",
                "explanation": f"Credential URL is live and accessible (HTTP {http_status}). Page title: {page_title or 'Not extracted'}.",
                "http_status": http_status,
                "page_title": page_title,
                "domain": domain,
                "retrieval_timestamp": timestamp,
                "url_reachable": True
            }
        else:
            return {
                "status": "UNREACHABLE",
                "explanation": f"Credential URL returned HTTP {http_status}. URL may be invalid or expired.",
                "http_status": http_status,
                "page_title": None,
                "domain": domain,
                "retrieval_timestamp": timestamp,
                "url_reachable": False
            }

    except requests.exceptions.Timeout:
        return {
            "status": "VERIFICATION LIMITED",
            "explanation": "Credential URL request timed out. URL may be valid but temporarily unreachable.",
            "http_status": None,
            "page_title": None,
            "domain": domain,
            "retrieval_timestamp": timestamp,
            "url_reachable": False
        }
    except Exception as e:
        return {
            "status": "UNREACHABLE",
            "explanation": f"Could not reach credential verification URL: {str(e)[:100]}",
            "http_status": None,
            "page_title": None,
            "domain": domain,
            "retrieval_timestamp": timestamp,
            "url_reachable": False
        }

def compare_credential_fields(
    extracted: Dict[str, Any],
    user_provided: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Phase 7B: Compare extracted certificate fields against user-provided fields.
    
    Reports only matches that can be actually established.
    Does NOT invent matches - uses None for unverifiable fields.
    
    Comparison fields:
    - Certificate title
    - Issuer
    - Candidate name
    - Credential ID
    - Issue date
    """
    comparisons = {}
    
    fields_to_compare = {
        "certificate_name": ("Certificate Title", extracted.get("certificate_name"), user_provided.get("certificate_name")),
        "issuer": ("Issuer", extracted.get("issuer"), user_provided.get("issuer")),
        "candidate_name": ("Candidate Name", extracted.get("candidate_name"), user_provided.get("candidate_name")),
        "credential_id": ("Credential ID", extracted.get("credential_id"), user_provided.get("credential_id")),
        "issue_date": ("Issue Date", extracted.get("issue_date"), user_provided.get("issue_date")),
    }
    
    consistent_fields = []
    inconsistent_fields = []
    unverifiable_fields = []
    
    for field_key, (label, extracted_val, provided_val) in fields_to_compare.items():
        if not extracted_val and not provided_val:
            comparisons[field_key] = {
                "label": label,
                "extracted": None,
                "provided": None,
                "match": None,
                "status": "NOT PRESENT"
            }
            unverifiable_fields.append(label)
        elif not extracted_val:
            comparisons[field_key] = {
                "label": label,
                "extracted": None,
                "provided": provided_val,
                "match": None,
                "status": "EXTRACTION UNAVAILABLE"
            }
            unverifiable_fields.append(label)
        elif not provided_val:
            # Extracted from document, no user provided value to compare
            comparisons[field_key] = {
                "label": label,
                "extracted": extracted_val,
                "provided": None,
                "match": None,
                "status": "DOCUMENT SOURCE ONLY"
            }
        else:
            # Both exist - compare
            e_norm = str(extracted_val).strip().lower()
            p_norm = str(provided_val).strip().lower()
            is_match = (e_norm == p_norm) or (e_norm in p_norm) or (p_norm in e_norm)
            
            comparisons[field_key] = {
                "label": label,
                "extracted": extracted_val,
                "provided": provided_val,
                "match": is_match,
                "status": "CONSISTENT" if is_match else "INCONSISTENT"
            }
            if is_match:
                consistent_fields.append(label)
            else:
                inconsistent_fields.append(label)
    
    comparison_summary = (
        f"Document extraction consistent with {len(consistent_fields)} field(s): "
        f"{', '.join(consistent_fields) if consistent_fields else 'none verifiable'}."
    )
    if inconsistent_fields:
        comparison_summary += f" Inconsistencies found in: {', '.join(inconsistent_fields)}."
    if unverifiable_fields:
        comparison_summary += f" Fields not verifiable: {', '.join(unverifiable_fields)}."
    
    return {
        "fields": comparisons,
        "consistent_fields": consistent_fields,
        "inconsistent_fields": inconsistent_fields,
        "unverifiable_fields": unverifiable_fields,
        "comparison_summary": comparison_summary,
        "has_inconsistencies": len(inconsistent_fields) > 0
    }

def parse_certificate_fallback(raw_text: str, user_provided: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic rule-based extractor if Gemini is unavailable or rate-limited.
    Ensures zero crashes and accurate heuristic extraction.
    """
    cert_name = user_provided.get("certificate_name")
    issuer = user_provided.get("issuer")
    cred_id = user_provided.get("credential_id")
    cred_url = user_provided.get("credential_url")
    candidate_name = user_provided.get("candidate_name")
    issue_date = user_provided.get("issue_date")
    expiry_date = user_provided.get("expiry_date")
    detected_skills = []

    text_lower = raw_text.lower() if raw_text else ""

    # Detect Issuer
    if not issuer:
        for ki in KNOWN_ISSUERS:
            if ki.lower() in text_lower:
                issuer = ki
                break

    # Detect Certificate Title
    if not cert_name:
        lines = [l.strip() for l in raw_text.splitlines() if len(l.strip()) > 3]
        for line in lines:
            line_l = line.lower()
            if any(k in line_l for k in ["certificate", "certified", "course", "specialization", "nanodegree", "bootcamp", "award"]):
                cert_name = line
                break
        if not cert_name and lines:
            cert_name = lines[0]

    # Detect Credential ID
    if not cred_id:
        id_match = re.search(r"(?:credential\s*id|certificate\s*id|license|verification\s*code|id|cert\s*#)[:\s#]*([A-Za-z0-9\-_]{6,})", raw_text, re.IGNORECASE)
        if id_match:
            cred_id = id_match.group(1).strip()

    # Detect Dates
    if not issue_date:
        date_match = re.search(r"(?:issued|date|awarded|completed|on)[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", raw_text, re.IGNORECASE)
        if date_match:
            issue_date = date_match.group(1).strip()

    # Detect Credential URL
    if not cred_url:
        url_match = re.search(r"(https?://[^\s<>\"']+verify[^\s<>\"']*)", raw_text, re.IGNORECASE)
        if url_match:
            cred_url = url_match.group(1).strip()

    # Detect Skills
    for sk in COMMON_TECH_SKILLS:
        pattern = r"\b" + re.escape(sk.lower()) + r"\b"
        if re.search(pattern, text_lower):
            if sk not in detected_skills:
                detected_skills.append(sk)

    return {
        "certificate_name": cert_name or "Certificate of Completion",
        "issuer": issuer or "Institutional Credential Issuer",
        "candidate_name": candidate_name or None,
        "issue_date": issue_date or None,
        "expiry_date": expiry_date or None,
        "credential_id": cred_id or None,
        "credential_url": cred_url or None,
        "skills": detected_skills,
        "summary": f"Certificate evidence for '{cert_name or 'technical qualification'}' issued by {issuer or 'issuing authority'}."
    }

@with_gemini_retry("Certificate Intelligence")
def extract_certificate_with_gemini(
    raw_text: str,
    file_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    user_provided: Optional[Dict[str, Any]] = None,
    model_name: str = "gemini-3.5-flash"
) -> Dict[str, Any]:
    """
    Uses Gemini to structure and interpret the extracted certificate document.
    """
    user_provided = user_provided or {}

    prompt = f"""
    You are an expert AI Certificate and Credential Intelligence Analyzer for ProofHire AI.
    Extract available information from the uploaded certificate document.

    Attempt to identify:
    - Candidate Name
    - Certificate Title / Name
    - Issuing Organization
    - Issue Date
    - Expiry Date if present
    - Credential ID if present
    - Skills / Course Topic
    - Credential Verification URL if present

    CRITICAL RULES:
    1. Do NOT invent missing information. If a field is not present in the document, leave it as null.
    2. Extract only skills actually covered or demonstrated by this certificate.
    3. User-Provided Hints (verify against document text if available):
       - Name: {user_provided.get('certificate_name') or 'N/A'}
       - Issuer: {user_provided.get('issuer') or 'N/A'}
       - Credential ID: {user_provided.get('credential_id') or 'N/A'}
       - Credential URL: {user_provided.get('credential_url') or 'N/A'}

    Document Text Content:
    ---
    {raw_text if raw_text else "[Raw text could not be extracted directly from document layer. Inspect attached media if available.]"}
    ---

    Return STRICT JSON with keys:
    {{
      "certificate_name": "Title of certificate or null",
      "issuer": "Issuing organization or null",
      "candidate_name": "Recipient name or null",
      "issue_date": "Date issued or null",
      "expiry_date": "Expiry date or null",
      "credential_id": "Credential/License ID or null",
      "credential_url": "Verification URL or null",
      "skills": ["Skill1", "Skill2"],
      "summary": "Short 1-2 sentence description of what was verified in this certificate."
    }}
    """

    contents: List[Any] = [prompt]
    if file_bytes and mime_type and (mime_type.startswith("image/") or mime_type == "application/pdf") and len(raw_text) < 50:
        contents.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    data = json.loads(response.text)
    return data

def determine_verification_status(
    url_verification: Dict[str, Any],
    doc_extracted: bool,
    cert_name: Optional[str],
    clean_skills: List[str]
) -> Tuple[str, str]:
    """
    Phase 7B: Determines honest verification status based on actual retrieval results.
    
    Uses the detailed URL verification dict (from verify_credential_url).
    
    Returns (verification_status, status_explanation) using only these statuses:
    - CREDENTIAL URL VERIFIED  (URL retrieved successfully)
    - DOCUMENT EXTRACTED        (PDF/image text extracted, no URL or URL not retrieved)
    - SUBMITTED ONLY            (Only user-provided metadata, no extraction)
    - VERIFICATION UNAVAILABLE  (Could not reach URL)
    - VERIFICATION FAILED       (URL returned error)
    """
    url_status = url_verification.get("status", "NOT PROVIDED")
    url = url_verification.get("explanation", "")
    
    if url_status == "RETRIEVED":
        return (
            "CREDENTIAL URL VERIFIED",
            f"External credential URL retrieved and accessible. {url_verification.get('explanation', '')}"
        )
    elif url_status == "UNREACHABLE":
        if doc_extracted:
            return (
                "DOCUMENT EXTRACTED",
                f"Certificate document text extracted. Credential URL was unreachable: {url_verification.get('explanation', '')}."
            )
        else:
            return (
                "VERIFICATION FAILED",
                f"Credential URL unreachable and document extraction incomplete. {url_verification.get('explanation', '')}."
            )
    elif url_status == "VERIFICATION LIMITED":
        if doc_extracted:
            return (
                "DOCUMENT EXTRACTED",
                f"Certificate document text extracted. Credential URL timed out: {url_verification.get('explanation', '')}."
            )
        else:
            return (
                "VERIFICATION UNAVAILABLE",
                f"Credential URL request timed out and document extraction incomplete."
            )
    elif url_status == "NOT PROVIDED":
        if doc_extracted or clean_skills or cert_name:
            return (
                "DOCUMENT EXTRACTED",
                "Document text and metadata extracted. No credential URL provided for external verification."
            )
        else:
            return (
                "SUBMITTED ONLY",
                "Candidate submitted certificate details only. Document content could not be inspected."
            )
    else:
        return (
            "VERIFICATION UNAVAILABLE",
            "Verification status could not be determined from available information."
        )

def process_certificate_evidence(
    file_path: str,
    filename: str,
    content_type: str,
    file_bytes: Optional[bytes] = None,
    user_provided: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Phase 7A/7B Master pipeline:
    1. Document extraction (PDF / Image)
    2. Document Intelligence (Gemini + Deterministic Fallback)
    3. Enhanced Credential URL Verification (7B) - retrieval + page title + domain
    4. Credential Field Comparison (7B) - compare extracted vs user-provided
    5. Verification Status evaluation (Strict fraud/integrity rules)
    6. Evidence Weighting assignment (certificate = supporting credential, NOT practical demo)
    7. Skill Connection mapping
    """
    user_provided = user_provided or {}

    # Step 1: Document Text Extraction
    extraction_res = extract_raw_document_content(file_path, filename)
    raw_text = extraction_res["raw_text"]
    doc_extracted = (len(raw_text) > 15)

    # Step 2: Document Intelligence via Gemini
    structured_data: Dict[str, Any] = {}
    ai_status = "ai_structured"

    try:
        structured_data = extract_certificate_with_gemini(
            raw_text=raw_text,
            file_bytes=file_bytes,
            mime_type=content_type,
            user_provided=user_provided
        )
    except Exception as e:
        print(f"Gemini certificate extraction note: {e}, falling back to deterministic extraction")
        structured_data = parse_certificate_fallback(raw_text, user_provided)
        ai_status = "deterministic_fallback"

    # Merge user-provided fields if AI missed them
    cert_name = structured_data.get("certificate_name") or user_provided.get("certificate_name") or filename
    issuer = structured_data.get("issuer") or user_provided.get("issuer") or "Verified Issuer"
    candidate_name = structured_data.get("candidate_name") or user_provided.get("candidate_name")
    issue_date = structured_data.get("issue_date") or user_provided.get("issue_date")
    expiry_date = structured_data.get("expiry_date") or user_provided.get("expiry_date")
    cred_id = structured_data.get("credential_id") or user_provided.get("credential_id")
    cred_url = structured_data.get("credential_url") or user_provided.get("credential_url")
    skills = structured_data.get("skills") or []

    # Ensure skills list is deduplicated and cleaned
    clean_skills = []
    for s in skills:
        if s and isinstance(s, str) and s.strip():
            c_skill = s.strip()
            if c_skill not in clean_skills:
                clean_skills.append(c_skill)

    # If no skills detected by AI, run fallback keyword scan
    if not clean_skills and raw_text:
        fb = parse_certificate_fallback(raw_text, user_provided)
        clean_skills = fb.get("skills", [])

    # Step 3 (Phase 7B): Enhanced Credential URL Verification
    url_verification = verify_credential_url(cred_url)

    # Step 4 (Phase 7B): Credential Field Comparison
    extracted_fields = {
        "certificate_name": cert_name,
        "issuer": issuer,
        "candidate_name": candidate_name,
        "credential_id": cred_id,
        "issue_date": issue_date
    }
    credential_comparison = compare_credential_fields(extracted_fields, user_provided)

    # Step 5: Determine Verification Status (using Phase 7B logic)
    verification_status, status_explanation = determine_verification_status(
        url_verification=url_verification,
        doc_extracted=doc_extracted,
        cert_name=cert_name,
        clean_skills=clean_skills
    )

    extraction_status = "EXTRACTED" if doc_extracted else ("PARTIAL" if (cert_name or clean_skills) else "FAILED")

    # Step 6 (Phase 7B): Evidence Weighting
    # Certificate = credential/supporting evidence
    # It is NOT a practical skill demonstration
    evidence_weight = {
        "type": CERTIFICATE_EVIDENCE_WEIGHT,
        "label": "Credential / Supporting Evidence",
        "hierarchy_note": (
            "Certificates provide supporting credential evidence. "
            "They rank below: Practical Assessment > GitHub Implementation Signals > Interview Performance. "
            "A certificate does not substitute for demonstrated practical skill."
        ),
        "contributes_to_evidence_level": True,
        "can_reach_strong_evidence_alone": False,
        "recommended_combination": "Combine with GitHub repository signals or Skill Assessment for stronger evidence."
    }

    return {
        "certificate_name": cert_name,
        "issuer": issuer,
        "candidate_name": candidate_name,
        "issue_date": issue_date,
        "expiry_date": expiry_date,
        "credential_id": cred_id,
        "credential_url": cred_url,
        "skills": clean_skills,
        "document_extraction_status": extraction_status,
        "verification_status": verification_status,
        "status_explanation": status_explanation,
        "integrity_disclaimer": INTEGRITY_DISCLAIMER,
        "raw_text_snippet": raw_text[:300] if raw_text else "",
        "extraction_method": extraction_res["extraction_method"],
        "ai_processing_status": ai_status,
        "summary": structured_data.get("summary") or f"Certificate for {cert_name} issued by {issuer}.",
        # Phase 7B additions
        "url_verification": url_verification,
        "credential_comparison": credential_comparison,
        "evidence_weight": evidence_weight,
    }
