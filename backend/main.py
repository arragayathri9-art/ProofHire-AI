from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models.models as models
from schemas.schemas import (
    JobCreate, JobResponse, CandidateResponse, AnalysisResultResponse, GeminiJobExtraction,
    AssessmentResponseSave, AssessmentSubmitPayload,
    InterviewResponsePayload, InterviewFollowUpPayload,
    GitHubEvidenceAnalyzePayload
)
from services.resume_parser import extract_text_from_pdf, analyze_resume_with_gemini
from services.job_intelligence import analyze_job_with_gemini
from services.evidence_intelligence import analyze_evidence_with_gemini, verify_claim_with_gemini
from services.url_inspector import inspect_url
from services.github_service import (
    parse_github_url,
    fetch_github_repository,
    extract_skill_signals,
    build_repository_intelligence_summary
)
from services.assessment_planner import plan_assessment_with_gemini
from services.question_generator import generate_full_assessment_questions
from services.assessment_evaluator import evaluate_single_question, get_demonstration_level
from services.profile_intelligence import compute_and_save_skill_profile, map_assessment_percentage_to_label
from services.interview_intelligence import (
    plan_interview_skills,
    generate_targeted_interview_questions,
    generate_interview_follow_up,
    save_interview_response,
    format_question_dict
)
from services.report_intelligence import aggregate_proofhire_report
from services.certificate_intelligence import process_certificate_evidence
from utils.comparison import compare_skills
from datetime import datetime
import os
import shutil

Base.metadata.create_all(bind=engine)

def ensure_db_schema():
    """Ensure newly added columns exist in SQLite database without requiring full rebuild."""
    try:
        with engine.connect() as conn:
            for table, col in [("skill_evidence", "evidence_access_status"), ("candidate_claims", "evidence_access_status")]:
                res = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
                cols = [c[1] for c in res]
                if col not in cols:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col} VARCHAR")
            
            # Ensure skill_evidence GitHub columns
            res_se = conn.exec_driver_sql("PRAGMA table_info(skill_evidence)").fetchall()
            existing_se = [c[1] for c in res_se]
            se_github_cols = [
                ("repository_owner", "VARCHAR"),
                ("repository_name", "VARCHAR"),
                ("repository_url", "VARCHAR"),
                ("primary_language", "VARCHAR"),
                ("languages", "JSON"),
                ("topics", "JSON"),
                ("readme_summary", "TEXT"),
                ("repository_structure", "JSON"),
                ("retrieved_at", "DATETIME"),
                ("github_access_status", "VARCHAR"),
                ("skill_signals", "JSON"),
                ("certificate_name", "VARCHAR"),
                ("issuer", "VARCHAR"),
                ("certificate_candidate_name", "VARCHAR"),
                ("issue_date", "VARCHAR"),
                ("expiry_date", "VARCHAR"),
                ("credential_id", "VARCHAR"),
                ("credential_url", "VARCHAR"),
                ("document_extraction_status", "VARCHAR"),
                ("verification_status", "VARCHAR"),
                ("certificate_metadata", "JSON"),
            ]
            for col, ctype in se_github_cols:
                if col not in existing_se:
                    conn.exec_driver_sql(f"ALTER TABLE skill_evidence ADD COLUMN {col} {ctype}")

            # Ensure skill_verifications table columns
            res_sv = conn.exec_driver_sql("PRAGMA table_info(skill_verifications)").fetchall()
            existing_sv = [c[1] for c in res_sv]
            sv_columns = [
                ("analysis_id", "INTEGER"), ("candidate_id", "INTEGER"), ("skill_name", "VARCHAR"),
                ("resume_claim_present", "BOOLEAN"), ("claims_count", "INTEGER"), ("evidence_count", "INTEGER"),
                ("retrieved_evidence_count", "INTEGER"), ("assessment_percentage", "FLOAT"), ("assessment_label", "VARCHAR"),
                ("evidence_level", "VARCHAR"), ("evidence_strength", "VARCHAR"), ("claim_status", "VARCHAR"),
                ("github_evidence", "VARCHAR"), ("assessment_status", "VARCHAR"), ("proof_sources", "JSON"),
                ("job_group", "VARCHAR"), ("explanation", "TEXT"),
                ("next_verification_step", "TEXT"), ("sources_breakdown", "JSON"), ("graph_data", "JSON"),
                ("created_at", "DATETIME"), ("updated_at", "DATETIME")
            ]
            for col, ctype in sv_columns:
                if col not in existing_sv:
                    conn.exec_driver_sql(f"ALTER TABLE skill_verifications ADD COLUMN {col} {ctype}")
            
            conn.commit()
    except Exception as e:
        print(f"Database schema verification note: {e}")

ensure_db_schema()

app = FastAPI(title="ProofHire AI API")

cors_origins_env = os.getenv("ALLOWED_ORIGINS") or os.getenv("FRONTEND_URL")

if cors_origins_env and cors_origins_env.strip() == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://proofhire-ai.onrender.com",
    ]
    if cors_origins_env:
        for origin in cors_origins_env.split(","):
            cleaned = origin.strip()
            if cleaned and cleaned not in allowed_origins:
                allowed_origins.append(cleaned)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

os.makedirs("uploads", exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to ProofHire AI API"}

@app.post("/api/jobs", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    try:
        extracted = analyze_job_with_gemini(job.title, job.company or "", job.description)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_job = models.Job(
        title=job.title,
        company=job.company,
        description=job.description,
        required_skills=extracted.required_skills,
        preferred_skills=extracted.preferred_skills,
        minimum_experience=extracted.minimum_experience,
        education_requirements=extracted.education_requirements
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@app.get("/api/jobs", response_model=list[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    return db.query(models.Job).all()

@app.get("/api/candidates", response_model=list[CandidateResponse])
def get_candidates(db: Session = Depends(get_db)):
    return db.query(models.Candidate).order_by(models.Candidate.id.desc()).all()

@app.get("/api/candidates/{candidate_id}")
def get_candidate_detail(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    resume = db.query(models.Resume).filter(models.Resume.candidate_id == candidate.id).order_by(models.Resume.id.desc()).first()
    skills = db.query(models.CandidateSkill).filter(models.CandidateSkill.candidate_id == candidate.id).all()
    claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
    analyses = db.query(models.Analysis).filter(models.Analysis.candidate_id == candidate.id).order_by(models.Analysis.id.desc()).all()
    
    for claim in claims:
        claim.evidence = db.query(models.SkillEvidence).filter(models.SkillEvidence.claim_id == claim.id).all()
        
    latest_analysis = analyses[0] if analyses else None
    job = None
    if latest_analysis:
        job = db.query(models.Job).filter(models.Job.id == latest_analysis.job_id).first()
        
    return {
        "candidate": candidate,
        "resume": resume,
        "skills": [s.skill_name for s in skills],
        "claims": claims,
        "analyses": analyses,
        "latest_analysis_id": latest_analysis.id if latest_analysis else None,
        "job": job
    }

@app.get("/api/analyses")
def get_analyses(db: Session = Depends(get_db)):
    analyses = db.query(models.Analysis).order_by(models.Analysis.id.desc()).all()
    results = []
    for a in analyses:
        candidate = db.query(models.Candidate).filter(models.Candidate.id == a.candidate_id).first()
        job = db.query(models.Job).filter(models.Job.id == a.job_id).first()
        claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == a.candidate_id).all()
        
        total_evidence = 0
        for c in claims:
            evs = db.query(models.SkillEvidence).filter(models.SkillEvidence.claim_id == c.id).all()
            total_evidence += len(evs)

        assessment = db.query(models.Assessment).filter(models.Assessment.analysis_id == a.id).first()
        assessment_status = assessment.status if assessment else "not_generated"
        skill_verifs_count = db.query(models.SkillVerification).filter(models.SkillVerification.analysis_id == a.id).count()
        interview_plan = db.query(models.InterviewPlan).filter(models.InterviewPlan.analysis_id == a.id).first()

        # Determine exact current stage and continue route
        if interview_plan:
            stage = "Interview Intelligence"
            continue_route = f"/interview/{a.id}"
        elif skill_verifs_count > 0:
            stage = "Verified Skill Profile"
            continue_route = f"/skill-profile/{a.id}"
        elif assessment and assessment.status == "completed":
            stage = "Skill Assessment"
            continue_route = f"/assessment/{a.id}"
        elif total_evidence > 0:
            stage = "Evidence Verification"
            continue_route = f"/evidence/{a.id}"
        else:
            stage = "Resume Analysis"
            continue_route = f"/analysis/result/{a.id}"

        formatted_updated = a.created_at.strftime("%b %d, %Y") if a.created_at else "Recently"
            
        results.append({
            "id": a.id,
            "candidate_id": a.candidate_id,
            "candidate_name": candidate.name if candidate else "Unknown Candidate",
            "job_id": a.job_id,
            "job_title": job.title if job else "N/A",
            "job_company": job.company if job else "",
            "created_at": a.created_at,
            "last_updated": formatted_updated,
            "claims_count": len(claims),
            "evidence_count": total_evidence,
            "current_stage": stage,
            "continue_route": continue_route,
            "assessment_status": assessment_status,
            "skills_present_count": len(a.skills_present or [])
        })
    return results

@app.post("/api/candidates/analyze")
async def analyze_candidate(
    job_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    resume_text = extract_text_from_pdf(file_path)
    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        
    try:
        extracted_candidate = analyze_resume_with_gemini(resume_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    name = extracted_candidate.candidate_name or "Unknown Candidate"
    email = extracted_candidate.email
    
    db_candidate = models.Candidate(
        name=name,
        email=email,
        phone=extracted_candidate.phone,
        location=extracted_candidate.location,
        professional_summary=extracted_candidate.professional_summary,
        experience=[exp.dict() for exp in extracted_candidate.experience],
        projects=[proj.dict() for proj in extracted_candidate.projects],
        education=[edu.dict() for edu in extracted_candidate.education],
        certifications=[cert.dict() for cert in extracted_candidate.certifications],
        links=extracted_candidate.links
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    
    db_resume = models.Resume(
        candidate_id=db_candidate.id,
        filename=file.filename,
        file_path=file_path,
        raw_text=resume_text
    )
    db.add(db_resume)
    
    candidate_skills = extracted_candidate.skills
    for skill_name in candidate_skills:
        db_skill = models.CandidateSkill(candidate_id=db_candidate.id, skill_name=skill_name)
        db.add(db_skill)
        db.commit()
        db.refresh(db_skill)
        
    # Process and deduplicate claims with Needs Verification default
    seen_claims = set()
    for claim in extracted_candidate.professional_claims:
        normalized_claim = " ".join(claim.claim.strip().lower().split())
        claim_key = f"{normalized_claim}::{claim.source_section.lower().strip()}"
        
        if claim_key not in seen_claims:
            seen_claims.add(claim_key)
            
            matched_skill_id = None
            if claim.related_skills:
                for req_skill in claim.related_skills:
                    db_skill = db.query(models.CandidateSkill).filter(
                        models.CandidateSkill.candidate_id == db_candidate.id,
                        models.CandidateSkill.skill_name == req_skill
                    ).first()
                    if db_skill:
                        matched_skill_id = db_skill.id
                        break
            
            # Claims start with zero additional evidence, remaining strictly 'Needs Verification'
            db_claim = models.CandidateClaim(
                candidate_id=db_candidate.id,
                skill_id=matched_skill_id,
                claim_text=claim.claim.strip(),
                claim_type=claim.claim_type,
                source_section=claim.source_section,
                verification_status="needs_verification",
                evidence_level="Needs Verification",
                evidence_access_status=None,
                evidence_used="Resume claim only (no additional evidence submitted)",
                what_supports=f"Stated in candidate resume under {claim.source_section}.",
                what_is_missing="No additional supporting evidence has been provided yet.",
                next_step="Submit supporting evidence (code repository, deployment URL, or documentation) to begin verification."
            )
            db.add(db_claim)
            
    db.commit()
    
    comparison = compare_skills(
        candidate_skills, 
        job.required_skills, 
        job.preferred_skills
    )
    
    db_analysis = models.Analysis(
        candidate_id=db_candidate.id,
        job_id=job.id,
        skills_present=comparison["skills_present"],
        potential_skill_gaps=comparison["potential_skill_gaps"],
        skills_requiring_verification=comparison["skills_requiring_verification"]
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    
    return {
        "analysis_id": db_analysis.id,
        "candidate_id": db_candidate.id,
        "candidate_name": db_candidate.name,
        "job_title": job.title
    }

@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
    skills = db.query(models.CandidateSkill).filter(models.CandidateSkill.candidate_id == candidate.id).all()
    
    for claim in claims:
        claim.evidence = db.query(models.SkillEvidence).filter(models.SkillEvidence.claim_id == claim.id).all()
        # Enforce: claims with zero additional evidence remain Needs Verification
        if not claim.evidence:
            if not claim.evidence_level or claim.evidence_level == "N/A":
                claim.evidence_level = "Needs Verification"
            if not claim.evidence_used:
                claim.evidence_used = "Resume claim only (no additional evidence submitted)"
            if not claim.what_is_missing:
                claim.what_is_missing = "No additional supporting evidence has been provided yet."
            if not claim.next_step:
                claim.next_step = "Submit supporting evidence (code repository, deployment URL, or documentation) to begin verification."
        
    all_evidence = db.query(models.SkillEvidence).filter(models.SkillEvidence.analysis_id == analysis_id).all()
    
    assessment = db.query(models.Assessment).filter(models.Assessment.analysis_id == analysis_id).first()
    skill_verifs_count = db.query(models.SkillVerification).filter(models.SkillVerification.analysis_id == analysis_id).count()
    interview_plan = db.query(models.InterviewPlan).filter(models.InterviewPlan.analysis_id == analysis_id).first()

    pipeline_stages = {
        "resume": "completed",
        "evidence": "completed" if len(all_evidence) > 0 or assessment else "current",
        "assessment": "completed" if (assessment and assessment.status == "completed") else ("current" if assessment else "pending"),
        "profile": "completed" if skill_verifs_count > 0 else "pending",
        "interview": "completed" if interview_plan else "pending",
        "report": "completed" if interview_plan else "pending"
    }

    if interview_plan:
        stage = "Interview Intelligence"
    elif skill_verifs_count > 0:
        stage = "Verified Skill Profile"
    elif assessment and assessment.status == "completed":
        stage = "Skill Assessment"
    elif len(all_evidence) > 0:
        stage = "Evidence Verification"
    else:
        stage = "Resume Analysis"

    return {
        "analysis": analysis,
        "candidate": candidate,
        "job": job,
        "claims": claims,
        "candidate_skills": [s.skill_name for s in skills],
        "evidence": all_evidence,
        "pipeline_stages": pipeline_stages,
        "current_stage": stage
    }

@app.post("/api/evidence")
def create_evidence(
    claim_id: int = Form(...),
    evidence_type: str = Form(...),
    title: str = Form(""),
    description: str = Form(""),
    url: str = Form(""),
    auto_inspect: bool = Form(True),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    claim = db.query(models.CandidateClaim).filter(models.CandidateClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    candidate = db.query(models.Candidate).filter(models.Candidate.id == claim.candidate_id).first()
    analysis = db.query(models.Analysis).filter(models.Analysis.candidate_id == candidate.id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    resume = db.query(models.Resume).filter(models.Resume.candidate_id == candidate.id).first()
    
    # 1. Process Evidence Content with strict evidence access status tracking
    extracted_text = ""
    file_path = ""
    evidence_access_status = "submitted_only"
    
    if evidence_type == "pdf" and file:
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        pdf_text = extract_text_from_pdf(file_path)
        if pdf_text and pdf_text.strip():
            extracted_text = f"Uploaded PDF: {file.filename}\nExtracted Content:\n{pdf_text}"
            evidence_access_status = "retrieved"
        else:
            extracted_text = f"Uploaded PDF ({file.filename}) could not be read or was empty."
            evidence_access_status = "retrieval_failed"
    elif evidence_type == "url":
        url_text, status = inspect_url(url, auto_inspect=auto_inspect)
        evidence_access_status = status
        if evidence_access_status == "retrieved":
            extracted_text = (
                f"Evidence Access Status: retrieved (Inspected by ProofHire)\n"
                f"{url_text}\n"
                f"Candidate Description: {description}"
            )
        elif evidence_access_status == "retrieval_failed":
            extracted_text = (
                f"Evidence Access Status: retrieval_failed\n"
                f"{url_text}\n"
                f"Candidate Description: {description}"
            )
        else:
            extracted_text = (
                f"Evidence Access Status: submitted_only\n"
                f"Supplied URL: {url}\n"
                "A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.\n"
                f"Candidate Description: {description}"
            )
    elif evidence_type == "github":
        parsed = parse_github_url(url)
        if parsed["valid"]:
            repo_data = fetch_github_repository(parsed["owner"], parsed["repo"])
            if repo_data.get("success"):
                signals = extract_skill_signals(repo_data)
                extracted_text = build_repository_intelligence_summary(repo_data, signals)
                evidence_access_status = "retrieved"
            else:
                extracted_text = f"GitHub retrieval failed: {repo_data.get('error', 'Unknown error')}\nURL: {url}"
                evidence_access_status = "retrieval_failed"
        else:
            extracted_text = f"Invalid GitHub URL: {url}\n{parsed.get('error')}"
            evidence_access_status = "retrieval_failed"
    else:
        # plain text evidence submitted by user
        evidence_access_status = "submitted_only"
        extracted_text = (
            f"Evidence Access Status: submitted_only (User-submitted text)\n"
            f"Description: {description}"
        )
        
    # 2. Evidence Agent
    related_skills = [claim.skill.skill_name] if claim.skill else []
    job_context = f"Job Title: {job.title}\nRequirements: {job.required_skills}"
    
    evidence_analysis = None
    try:
        evidence_analysis = analyze_evidence_with_gemini(
            claim_text=claim.claim_text,
            related_skills=related_skills,
            evidence_text=extracted_text,
            job_context=job_context,
            evidence_access_status=evidence_access_status
        )
    except Exception as e:
        print(f"Evidence Agent Error: {e}")
        
    # 3. Save Evidence with evidence_access_status
    github_fields = {}
    if evidence_type == "github" and 'repo_data' in locals() and repo_data.get("success"):
        github_fields = {
            "repository_owner": repo_data.get("owner"),
            "repository_name": repo_data.get("repository_name"),
            "repository_url": repo_data.get("repository_url"),
            "primary_language": repo_data.get("primary_language"),
            "languages": repo_data.get("languages", {}),
            "topics": repo_data.get("topics", []),
            "readme_summary": repo_data.get("readme_summary"),
            "repository_structure": repo_data.get("repository_structure", []),
            "retrieved_at": datetime.utcnow(),
            "github_access_status": "retrieved",
            "skill_signals": signals if 'signals' in locals() else []
        }

    db_evidence = models.SkillEvidence(
        candidate_id=candidate.id,
        analysis_id=analysis.id,
        claim_id=claim.id,
        evidence_type=evidence_type,
        title=title or (f"GitHub: {repo_data.get('owner')}/{repo_data.get('repository_name')}" if ('repo_data' in locals() and repo_data.get("success")) else ""),
        description=description or (repo_data.get("description") if ('repo_data' in locals() and repo_data.get("success")) else ""),
        url=url,
        file_path=file_path,
        extracted_text=extracted_text,
        analysis_status="analyzed" if evidence_analysis else "error",
        evidence_access_status=evidence_access_status,
        evidence_summary=evidence_analysis.information_contained if evidence_analysis else None,
        supported_skills=evidence_analysis.supported_skills if evidence_analysis else [],
        **github_fields
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    
    # 4. Verification Agent across all evidence for this claim
    all_evidence = db.query(models.SkillEvidence).filter(models.SkillEvidence.claim_id == claim.id).all()
    has_retrieved_evidence = any(e.evidence_access_status == "retrieved" for e in all_evidence)
    
    # Aggregate access status for the claim
    if has_retrieved_evidence:
        overall_claim_access = "retrieved"
    elif any(e.evidence_access_status == "retrieval_failed" for e in all_evidence):
        overall_claim_access = "retrieval_failed"
    elif all_evidence:
        overall_claim_access = "submitted_only"
    else:
        overall_claim_access = None

    evidence_texts = [
        f"[Type: {e.evidence_type.upper()} | Access Status: {e.evidence_access_status or 'submitted_only'}]\n" +
        (e.extracted_text or e.description or "")
        for e in all_evidence
    ]
    resume_context = resume.raw_text if resume else ""
    
    try:
        verification = verify_claim_with_gemini(
            claim_text=claim.claim_text,
            evidence_texts=evidence_texts,
            resume_context=resume_context,
            has_retrieved_evidence=has_retrieved_evidence
        )
        
        claim.evidence_level = verification.evidence_level
        claim.evidence_access_status = overall_claim_access
        claim.evidence_used = verification.evidence_used
        claim.what_supports = verification.what_supports
        claim.what_is_missing = verification.what_is_missing
        claim.next_step = verification.next_step
        claim.verification_status = "Reviewed"
        db.commit()
    except Exception as e:
        print(f"Verification Agent Error: {e}")

    return {
        "message": "Evidence processed", 
        "evidence_id": db_evidence.id,
        "evidence_access_status": evidence_access_status,
        "evidence_level": claim.evidence_level
    }

@app.post("/api/evidence/github")
def analyze_github_evidence(
    payload: GitHubEvidenceAnalyzePayload,
    db: Session = Depends(get_db)
):
    """
    Connects existing GitHub API service to ProofHire Evidence Center.
    Retrieves real repository metadata, language distribution, file tree, and README.
    Derives deterministic skill signals from real retrieved files.
    Runs Evidence Agent and Claim Verification Agent.
    Strictly records evidence_access_status as 'retrieved' or appropriate failure.
    """
    claim = db.query(models.CandidateClaim).filter(models.CandidateClaim.id == payload.claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    candidate = db.query(models.Candidate).filter(models.Candidate.id == claim.candidate_id).first()
    analysis = db.query(models.Analysis).filter(models.Analysis.id == payload.analysis_id).first()
    if not analysis and candidate:
        analysis = db.query(models.Analysis).filter(models.Analysis.candidate_id == candidate.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    resume = db.query(models.Resume).filter(models.Resume.candidate_id == candidate.id).first()

    # 1. Parse and validate GitHub URL
    parsed = parse_github_url(payload.repository_url)
    if not parsed["valid"]:
        raise HTTPException(
            status_code=400,
            detail=parsed.get("error") or "Invalid GitHub repository URL. Must be in the format: https://github.com/owner/repository"
        )

    owner = parsed["owner"]
    repo = parsed["repo"]

    # 2. Fetch repository data from GitHub REST API
    repo_data = fetch_github_repository(owner, repo)
    if not repo_data.get("success"):
        err_type = repo_data.get("error_type")
        err_msg = repo_data.get("error") or "Failed to retrieve GitHub repository."
        if err_type == "not_found":
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{owner}/{repo}' was not found on GitHub or is private. ProofHire can only inspect public repositories."
            )
        elif err_type in ("rate_limited", "forbidden"):
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded or access forbidden. Please verify your GITHUB_TOKEN or wait before trying again."
            )
        elif err_type == "network_error":
            raise HTTPException(
                status_code=502,
                detail=f"Network error while connecting to GitHub API: {err_msg}"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=err_msg
            )

    # 3. Extract skill signals from REAL retrieved repository files
    signals = extract_skill_signals(repo_data)

    # 4. Build repository intelligence summary
    summary_text = build_repository_intelligence_summary(repo_data, signals)
    evidence_access_status = "retrieved"

    # 5. Evidence Agent with Gemini
    related_skills = [claim.skill.skill_name] if (claim.skill and claim.skill.skill_name) else []
    job_context = f"Job Title: {job.title}\nRequirements: {job.required_skills}" if job else ""
    evidence_analysis = None
    try:
        evidence_analysis = analyze_evidence_with_gemini(
            claim_text=claim.claim_text,
            related_skills=related_skills,
            evidence_text=summary_text,
            job_context=job_context,
            evidence_access_status=evidence_access_status
        )
    except Exception as e:
        print(f"Evidence Agent Error: {e}")

    # 6. Save SkillEvidence with complete GitHub metadata
    db_evidence = models.SkillEvidence(
        candidate_id=candidate.id,
        analysis_id=analysis.id,
        claim_id=claim.id,
        evidence_type="github",
        title=f"GitHub: {owner}/{repo}",
        description=payload.description or repo_data.get("description") or f"Public GitHub repository by {owner}",
        url=repo_data.get("repository_url") or parsed["normalized_url"],
        file_path="",
        extracted_text=summary_text,
        analysis_status="analyzed" if evidence_analysis else "error",
        evidence_access_status=evidence_access_status,
        github_access_status="retrieved",
        repository_owner=owner,
        repository_name=repo,
        repository_url=repo_data.get("repository_url") or parsed["normalized_url"],
        primary_language=repo_data.get("primary_language"),
        languages=repo_data.get("languages", {}),
        topics=repo_data.get("topics", []),
        readme_summary=repo_data.get("readme_summary"),
        repository_structure=repo_data.get("repository_structure", []),
        retrieved_at=datetime.utcnow(),
        skill_signals=signals,
        evidence_summary=evidence_analysis.information_contained if evidence_analysis else summary_text,
        supported_skills=evidence_analysis.supported_skills if evidence_analysis else [s["skill"] for s in signals]
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)

    # 7. Verification Agent across all evidence for this claim
    all_evidence = db.query(models.SkillEvidence).filter(models.SkillEvidence.claim_id == claim.id).all()
    has_retrieved_evidence = any(e.evidence_access_status == "retrieved" for e in all_evidence)
    overall_claim_access = "retrieved" if has_retrieved_evidence else "submitted_only"

    evidence_texts = [
        f"[Type: {e.evidence_type.upper()} | Access Status: {e.evidence_access_status or 'submitted_only'}]\n" +
        (e.extracted_text or e.description or "")
        for e in all_evidence
    ]
    resume_context = resume.raw_text if resume else ""

    try:
        verification = verify_claim_with_gemini(
            claim_text=claim.claim_text,
            evidence_texts=evidence_texts,
            resume_context=resume_context,
            has_retrieved_evidence=has_retrieved_evidence
        )
        claim.evidence_level = verification.evidence_level
        claim.evidence_access_status = overall_claim_access
        claim.evidence_used = verification.evidence_used
        claim.what_supports = verification.what_supports
        claim.what_is_missing = verification.what_is_missing
        claim.next_step = verification.next_step
        claim.verification_status = "Reviewed"
        db.commit()
    except Exception as e:
        print(f"Verification Agent Error: {e}")

    # 8. Prepare connection data
    related_skill_name = claim.skill.skill_name if (claim.skill and claim.skill.skill_name) else (signals[0]["skill"] if signals else "Software Engineering")
    connection = {
        "claim_being_verified": claim.claim_text,
        "github_repository": f"{owner}/{repo}",
        "detected_repository_signals": [s["skill"] for s in signals],
        "related_skill": related_skill_name
    }

    readme_avail = bool(repo_data.get("readme_summary") and repo_data.get("readme_summary") != "README unavailable.")

    return {
        "message": "GitHub repository successfully retrieved and analyzed",
        "evidence_id": db_evidence.id,
        "evidence_access_status": "retrieved",
        "repository_name": repo,
        "owner": owner,
        "description": repo_data.get("description"),
        "primary_language": repo_data.get("primary_language"),
        "languages": repo_data.get("languages", {}),
        "default_branch": repo_data.get("default_branch", "main"),
        "readme_summary": repo_data.get("readme_summary"),
        "readme_status": "Available (Indexed)" if readme_avail else "README unavailable",
        "github_access_status": "retrieved",
        "skill_signals": signals,
        "evidence_connection": connection,
        "evidence_level": claim.evidence_level
    }

# ==========================================
# PHASE 7A: CERTIFICATE & CREDENTIAL INTELLIGENCE API
# ==========================================

@app.post("/api/evidence/certificate")
def upload_certificate_evidence(
    analysis_id: int = Form(...),
    claim_id: Optional[int] = Form(None),
    certificate_name: Optional[str] = Form(None),
    issuer: Optional[str] = Form(None),
    credential_id: Optional[str] = Form(None),
    credential_url: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Phase 7A: Certificate and Credential Intelligence Endpoint.
    Extracts text and metadata from PDF, PNG, JPG/JPEG documents.
    Structures information using Gemini with deterministic fallback.
    Honest verification statuses:
    - DOCUMENT EXTRACTED
    - CREDENTIAL URL VERIFIED
    - SUBMITTED ONLY
    - VERIFICATION UNAVAILABLE
    - VERIFICATION FAILED
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a certificate in PDF, PNG, or JPG/JPEG format."
        )

    # Save file safely
    os.makedirs("uploads/certificates", exist_ok=True)
    safe_filename = f"{analysis_id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    file_path = os.path.join("uploads", "certificates", safe_filename)

    file_bytes = file.file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    # Content type
    content_type = file.content_type or ("application/pdf" if ext == ".pdf" else f"image/{ext.replace('.', '')}")

    user_provided = {
        "certificate_name": certificate_name,
        "issuer": issuer,
        "credential_id": credential_id,
        "credential_url": credential_url,
        "candidate_name": candidate.name
    }

    # Run Certificate Intelligence Pipeline
    cert_res = process_certificate_evidence(
        file_path=file_path,
        filename=file.filename,
        content_type=content_type,
        file_bytes=file_bytes,
        user_provided=user_provided
    )

    # Identify claim to associate
    target_claim = None
    if claim_id:
        target_claim = db.query(models.CandidateClaim).filter(models.CandidateClaim.id == claim_id).first()
    
    if not target_claim:
        # Match with candidate's existing claims based on detected skills
        candidate_claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
        for c in candidate_claims:
            c_skill = c.skill.skill_name.lower() if c.skill else ""
            if any(s.lower() in c_skill or c_skill in s.lower() for s in cert_res["skills"]):
                target_claim = c
                break
        if not target_claim and candidate_claims:
            target_claim = candidate_claims[0]

    # Create SkillEvidence
    db_evidence = models.SkillEvidence(
        candidate_id=candidate.id,
        analysis_id=analysis.id,
        claim_id=target_claim.id if target_claim else None,
        evidence_type="certificate",
        title=f"Certificate: {cert_res['certificate_name']}",
        description=cert_res["summary"],
        url=cert_res["credential_url"],
        file_path=file_path,
        extracted_text=cert_res["raw_text_snippet"],
        analysis_status="analyzed",
        evidence_access_status="retrieved" if cert_res["document_extraction_status"] == "EXTRACTED" else "submitted_only",
        supported_skills=cert_res["skills"],
        certificate_name=cert_res["certificate_name"],
        issuer=cert_res["issuer"],
        certificate_candidate_name=cert_res["candidate_name"],
        issue_date=cert_res["issue_date"],
        expiry_date=cert_res["expiry_date"],
        credential_id=cert_res["credential_id"],
        credential_url=cert_res["credential_url"],
        document_extraction_status=cert_res["document_extraction_status"],
        verification_status=cert_res["verification_status"],
        certificate_metadata=cert_res,
        evidence_summary=cert_res["status_explanation"]
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)

    # Re-evaluate target claim verification if applicable
    if target_claim:
        all_claim_evidence = db.query(models.SkillEvidence).filter(models.SkillEvidence.claim_id == target_claim.id).all()
        has_retrieved_evidence = any(e.evidence_access_status == "retrieved" for e in all_claim_evidence)
        target_claim.evidence_access_status = "retrieved" if has_retrieved_evidence else "submitted_only"
        
        # If verification is not yet Strong, update evidence_level to reflect credential
        if target_claim.evidence_level not in ["Strong Evidence", "Strong"]:
            if cert_res["verification_status"] == "CREDENTIAL URL VERIFIED":
                target_claim.evidence_level = "Good Evidence"
            else:
                target_claim.evidence_level = "Moderate Evidence"
        target_claim.verification_status = "Reviewed"
        db.commit()

    # Recompute Verified Skill Profile
    try:
        compute_and_save_skill_profile(analysis_id=analysis.id, db=db)
    except Exception as e:
        print(f"Skill profile recompute note: {e}")

    return {
        "message": "Certificate and credential successfully processed",
        "evidence_id": db_evidence.id,
        "certificate_name": cert_res["certificate_name"],
        "issuer": cert_res["issuer"],
        "candidate_name": cert_res["candidate_name"],
        "issue_date": cert_res["issue_date"],
        "expiry_date": cert_res["expiry_date"],
        "credential_id": cert_res["credential_id"],
        "credential_url": cert_res["credential_url"],
        "skills": cert_res["skills"],
        "document_extraction_status": cert_res["document_extraction_status"],
        "verification_status": cert_res["verification_status"],
        "status_explanation": cert_res["status_explanation"],
        "integrity_disclaimer": cert_res["integrity_disclaimer"],
        "claim_id": target_claim.id if target_claim else None,
        "evidence": {
            "id": db_evidence.id,
            "evidence_type": "certificate",
            "certificate_name": cert_res["certificate_name"],
            "issuer": cert_res["issuer"],
            "certificate_candidate_name": cert_res["candidate_name"],
            "issue_date": cert_res["issue_date"],
            "expiry_date": cert_res["expiry_date"],
            "credential_id": cert_res["credential_id"],
            "credential_url": cert_res["credential_url"],
            "supported_skills": cert_res["skills"],
            "document_extraction_status": cert_res["document_extraction_status"],
            "verification_status": cert_res["verification_status"],
            "evidence_summary": cert_res["status_explanation"]
        }
    }

# ==========================================
# PHASE 3: PERSONALIZED SKILL ASSESSMENT API
# ==========================================

@app.get("/api/assessments/analysis/{analysis_id}")
def get_assessment_by_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Fetch current assessment state for a candidate analysis session."""
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    candidate_skills = db.query(models.CandidateSkill).filter(models.CandidateSkill.candidate_id == candidate.id).all()
    
    assessment = db.query(models.Assessment).filter(models.Assessment.analysis_id == analysis_id).first()
    if not assessment:
        return {
            "status": "not_generated",
            "analysis_id": analysis.id,
            "candidate_id": candidate.id,
            "candidate_name": candidate.name if candidate else "Unknown Candidate",
            "job_title": job.title if job else "Target Role",
            "job_company": job.company if job else "",
            "candidate_skills": [s.skill_name for s in candidate_skills],
            "questions": [],
            "results": []
        }
        
    responses = {
        r.question_id: r 
        for r in db.query(models.AssessmentResponse).filter(models.AssessmentResponse.assessment_id == assessment.id).all()
    }
    
    questions_data = []
    for q in assessment.questions:
        resp = responses.get(q.id)
        if assessment.status == "completed":
            # Complete results view: includes evaluated feedback and correct answer
            questions_data.append({
                "id": q.id,
                "assessment_id": q.assessment_id,
                "order_num": q.order_num,
                "skill": q.skill,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "question_text": q.question_text,
                "options": q.options or [],
                "correct_answer": q.correct_answer,
                "candidate_answer": resp.candidate_answer if resp else "",
                "score": resp.score if resp else 0.0,
                "max_score": q.max_score,
                "is_correct": resp.is_correct if resp else False,
                "evaluation_feedback": resp.evaluation_feedback if resp else "No answer recorded.",
                "rubric_breakdown": resp.rubric_breakdown if resp else {}
            })
        else:
            # Active assessment: STRICTLY hide correct_answer and internal criteria
            questions_data.append({
                "id": q.id,
                "assessment_id": q.assessment_id,
                "order_num": q.order_num,
                "skill": q.skill,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "question_text": q.question_text,
                "options": q.options or [],
                "max_score": q.max_score,
                "candidate_answer": resp.candidate_answer if resp else ""
            })
            
    results_data = []
    if assessment.status == "completed":
        for res in assessment.results:
            skill_qs = [qd for qd in questions_data if qd.get("skill", "").lower() == res.skill.lower()]
            results_data.append({
                "id": res.id,
                "skill": res.skill,
                "score": res.score,
                "max_score": res.max_score,
                "percentage": res.percentage,
                "questions_count": res.questions_count,
                "demonstration_level": res.demonstration_level,
                "evidence_before_assessment": res.evidence_before_assessment,
                "feedback_summary": res.feedback_summary,
                "questions": skill_qs
            })

    return {
        "id": assessment.id,
        "analysis_id": analysis.id,
        "candidate_id": candidate.id,
        "candidate_name": candidate.name if candidate else "Unknown Candidate",
        "job_title": job.title if job else "Target Role",
        "job_company": job.company if job else "",
        "status": assessment.status,
        "selected_skills": assessment.selected_skills or [],
        "total_score": assessment.total_score,
        "total_max_score": assessment.total_max_score,
        "overall_percentage": assessment.overall_percentage,
        "created_at": assessment.created_at,
        "completed_at": assessment.completed_at,
        "questions": questions_data,
        "results": results_data
    }

@app.post("/api/assessments/generate/{analysis_id}")
def generate_assessment(analysis_id: int, regenerate: bool = Query(False), db: Session = Depends(get_db)):
    """
    Invokes Assessment Planning Agent and Question Generation Agent to build
    a customized, non-generic assessment based on candidate claims, target job, and evidence levels.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
    candidate_skills = [s.skill_name for s in db.query(models.CandidateSkill).filter(models.CandidateSkill.candidate_id == candidate.id).all()]
    
    existing = db.query(models.Assessment).filter(models.Assessment.analysis_id == analysis_id).first()
    if existing and not regenerate:
        return {"message": "Assessment already exists", "assessment_id": existing.id, "status": existing.status}
        
    if existing and regenerate:
        db.delete(existing)
        db.commit()

    # 1. Structure claims & evidence levels for the Planning Agent
    claims_info = []
    claims_by_skill = {}
    for c in claims:
        skill_name = c.skill.skill_name if c.skill else ""
        claims_info.append({
            "skill": skill_name,
            "claim_text": c.claim_text,
            "evidence_level": c.evidence_level or "Needs Verification",
            "evidence_used": c.evidence_used or ""
        })
        if skill_name:
            claims_by_skill.setdefault(skill_name.lower(), []).append(c.claim_text)

    # 2. Invoke Assessment Planning Agent
    plan_output = plan_assessment_with_gemini(
        job_title=job.title,
        job_required=job.required_skills or [],
        job_preferred=job.preferred_skills or [],
        candidate_skills=candidate_skills,
        claims_info=claims_info,
        skills_requiring_verification=analysis.skills_requiring_verification or [],
        potential_skill_gaps=analysis.potential_skill_gaps or []
    )
    
    selected_skills_data = [s.dict() if hasattr(s, "dict") else dict(s) for s in plan_output.selected_skills]

    # 3. Invoke Question Generation Agent
    generated_questions = generate_full_assessment_questions(
        selected_skills=selected_skills_data,
        target_job=job.title,
        claims_by_skill=claims_by_skill
    )

    # 4. Save Assessment and Questions
    assessment = models.Assessment(
        analysis_id=analysis.id,
        candidate_id=candidate.id,
        status="ready",
        selected_skills=selected_skills_data
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    for q in generated_questions:
        db_q = models.AssessmentQuestion(
            assessment_id=assessment.id,
            order_num=q.get("order_num", 1),
            skill=q.get("skill", "General"),
            question_type=q.get("question_type", "mcq"),
            difficulty=q.get("difficulty", "Intermediate"),
            question_text=q.get("question_text", ""),
            options=q.get("options", []),
            correct_answer=str(q.get("correct_answer", "")),
            evaluation_criteria=q.get("evaluation_criteria", {}),
            max_score=q.get("max_score", 5)
        )
        db.add(db_q)
    
    db.commit()
    db.refresh(assessment)
    return {"message": "Assessment generated successfully", "assessment_id": assessment.id, "status": assessment.status}

@app.post("/api/assessments/{assessment_id}/save-progress")
def save_assessment_progress(
    assessment_id: int, 
    payload: AssessmentResponseSave, 
    db: Session = Depends(get_db)
):
    """Saves candidate response for a question while maintaining active session state."""
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    if assessment.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot edit a completed assessment")

    if assessment.status == "ready":
        assessment.status = "in_progress"
    
    existing_resp = db.query(models.AssessmentResponse).filter(
        models.AssessmentResponse.assessment_id == assessment_id,
        models.AssessmentResponse.question_id == payload.question_id
    ).first()
    
    if existing_resp:
        existing_resp.candidate_answer = payload.candidate_answer
        existing_resp.submitted_at = datetime.utcnow()
    else:
        new_resp = models.AssessmentResponse(
            assessment_id=assessment_id,
            question_id=payload.question_id,
            candidate_answer=payload.candidate_answer,
            submitted_at=datetime.utcnow()
        )
        db.add(new_resp)
        
    db.commit()
    return {"message": "Progress saved", "question_id": payload.question_id}

@app.post("/api/assessments/{assessment_id}/submit")
def submit_assessment(
    assessment_id: int, 
    payload: AssessmentSubmitPayload, 
    db: Session = Depends(get_db)
):
    """
    Submits candidate assessment, runs deterministic and rubric evaluations,
    calculates mathematical scores, neutral demonstration levels, and adds results to evidence.
    """
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    # Save/update any responses from the payload
    for r in payload.responses:
        resp = db.query(models.AssessmentResponse).filter(
            models.AssessmentResponse.assessment_id == assessment_id,
            models.AssessmentResponse.question_id == r.question_id
        ).first()
        if resp:
            resp.candidate_answer = r.candidate_answer
            resp.submitted_at = datetime.utcnow()
        else:
            db.add(models.AssessmentResponse(
                assessment_id=assessment_id,
                question_id=r.question_id,
                candidate_answer=r.candidate_answer,
                submitted_at=datetime.utcnow()
            ))
    db.commit()

    questions = db.query(models.AssessmentQuestion).filter(models.AssessmentQuestion.assessment_id == assessment_id).order_by(models.AssessmentQuestion.order_num).all()
    responses = {
        r.question_id: r 
        for r in db.query(models.AssessmentResponse).filter(models.AssessmentResponse.assessment_id == assessment_id).all()
    }

    skill_scores = {}
    total_score = 0.0
    total_max_score = 0.0

    for q in questions:
        resp = responses.get(q.id)
        candidate_ans = resp.candidate_answer if resp else ""
        
        eval_result = evaluate_single_question(
            question_type=q.question_type,
            question_text=q.question_text,
            candidate_answer=candidate_ans,
            correct_answer=q.correct_answer or "",
            criteria=q.evaluation_criteria or {},
            max_score=q.max_score
        )
        
        if not resp:
            resp = models.AssessmentResponse(
                assessment_id=assessment_id,
                question_id=q.id,
                candidate_answer="",
                submitted_at=datetime.utcnow()
            )
            db.add(resp)

        resp.score = eval_result["score"]
        resp.is_correct = eval_result["is_correct"]
        resp.evaluation_feedback = eval_result["feedback"]
        resp.rubric_breakdown = eval_result.get("rubric_breakdown", {})
        
        # Mathematical accumulation
        skill_key = q.skill.strip()
        if skill_key not in skill_scores:
            skill_scores[skill_key] = {"score": 0.0, "max": 0.0, "count": 0}
        skill_scores[skill_key]["score"] += resp.score
        skill_scores[skill_key]["max"] += q.max_score
        skill_scores[skill_key]["count"] += 1

        total_score += resp.score
        total_max_score += q.max_score

    # Remove existing AssessmentResults before recalculating
    db.query(models.AssessmentResult).filter(models.AssessmentResult.assessment_id == assessment_id).delete()

    # Pre-assessment evidence level mapping from selected_skills plan
    ev_before_map = {}
    for item in (assessment.selected_skills or []):
        sk = item.get("skill", "").lower().strip()
        ev_before_map[sk] = item.get("evidence_level_before", "Needs Verification")

    for skill_name, data in skill_scores.items():
        pct = round((data["score"] / data["max"]) * 100.0, 1) if data["max"] > 0 else 0.0
        demonstration = get_demonstration_level(pct)
        ev_before = ev_before_map.get(skill_name.lower(), "Needs Verification")
        
        db_res = models.AssessmentResult(
            assessment_id=assessment.id,
            skill=skill_name,
            score=round(data["score"], 1),
            max_score=round(data["max"], 1),
            percentage=pct,
            questions_count=data["count"],
            demonstration_level=demonstration,
            evidence_before_assessment=ev_before,
            feedback_summary=f"Candidate achieved {data['score']:.1f} / {data['max']:.1f} points ({pct:.0f}%) on {skill_name} assessment questions."
        )
        db.add(db_res)

        # CONNECT WITH EVIDENCE: Add SkillEvidence record alongside existing evidence
        existing_ev = db.query(models.SkillEvidence).filter(
            models.SkillEvidence.analysis_id == assessment.analysis_id,
            models.SkillEvidence.evidence_type == "skill_assessment",
            models.SkillEvidence.title == f"ProofHire Skill Assessment: {skill_name}"
        ).first()

        evidence_desc = (
            f"Candidate scored {data['score']:.1f}/{data['max']:.1f} ({pct:.0f}%) across {data['count']} questions. "
            f"Demonstration Level: {demonstration}. Prior Evidence: {ev_before}."
        )

        if existing_ev:
            existing_ev.description = evidence_desc
            existing_ev.evidence_summary = f"{demonstration} ({pct:.0f}%)"
        else:
            new_ev = models.SkillEvidence(
                candidate_id=assessment.candidate_id,
                analysis_id=assessment.analysis_id,
                claim_id=None,
                evidence_type="skill_assessment",
                title=f"ProofHire Skill Assessment: {skill_name}",
                description=evidence_desc,
                analysis_status="verified",
                evidence_access_status="retrieved",
                evidence_summary=f"{demonstration} ({pct:.0f}%)",
                supported_skills=[skill_name]
            )
            db.add(new_ev)

    overall_pct = round((total_score / total_max_score) * 100.0, 1) if total_max_score > 0 else 0.0
    assessment.total_score = round(total_score, 1)
    assessment.total_max_score = round(total_max_score, 1)
    assessment.overall_percentage = overall_pct
    assessment.status = "completed"
    assessment.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(assessment)
    return {
        "message": "Assessment submitted and evaluated successfully", 
        "assessment_id": assessment.id,
        "total_score": assessment.total_score,
        "total_max_score": assessment.total_max_score,
        "overall_percentage": assessment.overall_percentage
    }

# ==========================================
# PHASE 4: VERIFIED SKILL PROFILE + PROOF GRAPH API
# ==========================================

@app.get("/api/skill-profile/{analysis_id}")
def get_verified_skill_profile(analysis_id: int, db: Session = Depends(get_db)):
    """
    Retrieves or calculates the Verified Skill Profile for the candidate analysis.
    Uses deterministic evidence aggregation and real stored evidence records.
    Upserts SkillVerification records safely into the database without creating duplicates.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    try:
        profile_data = compute_and_save_skill_profile(analysis_id=analysis_id, db=db)
        return profile_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate verified skill profile: {str(e)}")

@app.post("/api/skill-profile/{analysis_id}/recompute")
def recompute_verified_skill_profile(analysis_id: int, db: Session = Depends(get_db)):
    """
    Explicitly recalculates the Verified Skill Profile from all latest stored database records.
    Does NOT regenerate historical evidence or call external LLM scoring.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    try:
        profile_data = compute_and_save_skill_profile(analysis_id=analysis_id, db=db)
        return {
            "message": "Skill profile recomputed successfully from stored evidence and assessment records",
            **profile_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recompute verified skill profile: {str(e)}")

# ==========================================
# PHASE 5A: INTERVIEW INTELLIGENCE API
# ==========================================

@app.post("/api/interview/generate/{analysis_id}")
def generate_interview(analysis_id: int, db: Session = Depends(get_db)):
    """
    Generates an evidence-aware interview plan and 5-8 targeted interview questions
    grounded in candidate resume claims, evidence gaps, and assessment performance.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    try:
        plan = plan_interview_skills(analysis_id=analysis_id, db=db)
        questions = generate_targeted_interview_questions(analysis_id=analysis_id, db=db)
        return {
            "message": "Interview plan and targeted questions generated successfully",
            "analysis_id": analysis_id,
            "plan": plan,
            "questions_count": len(questions),
            "questions": questions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interview generation failed: {str(e)}")

@app.get("/api/interview/{analysis_id}")
def get_interview(analysis_id: int, db: Session = Depends(get_db)):
    """
    Retrieves interview plan and generated questions for the candidate analysis.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    
    plan = db.query(models.InterviewPlan).filter(models.InterviewPlan.analysis_id == analysis_id).first()
    questions = db.query(models.InterviewQuestion).filter(
        models.InterviewQuestion.analysis_id == analysis_id
    ).order_by(models.InterviewQuestion.order_num).all()

    # If no questions generated yet, generate them automatically
    if not questions:
        try:
            plan_data = plan_interview_skills(analysis_id=analysis_id, db=db)
            q_list = generate_targeted_interview_questions(analysis_id=analysis_id, db=db)
            return {
                "analysis_id": analysis_id,
                "candidate_name": candidate.name if candidate else "Candidate",
                "job_title": job.title if job else "Role",
                "plan": plan_data,
                "questions_count": len(q_list),
                "questions": q_list
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to auto-generate interview: {str(e)}")

    formatted_questions = [format_question_dict(q) for q in questions]
    plan_dict = {
        "analysis_id": analysis_id,
        "planning_summary": plan.planning_summary if plan else "Standard interview plan",
        "selected_skills": plan.selected_skills if plan else []
    }

    return {
        "analysis_id": analysis_id,
        "candidate_name": candidate.name if candidate else "Candidate",
        "job_title": job.title if job else "Role",
        "plan": plan_dict,
        "questions_count": len(formatted_questions),
        "questions": formatted_questions
    }

@app.post("/api/interview/{question_id}/follow-up")
def create_follow_up_question(
    question_id: int, 
    payload: InterviewFollowUpPayload, 
    db: Session = Depends(get_db)
):
    """
    Generates a targeted follow-up question tied to a parent question.
    """
    parent = db.query(models.InterviewQuestion).filter(models.InterviewQuestion.id == question_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent question not found")

    try:
        follow_up = generate_interview_follow_up(
            question_id=question_id,
            candidate_response=payload.candidate_response or "",
            db=db
        )
        return {
            "message": "Follow-up question generated successfully",
            "follow_up": follow_up
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate follow-up question: {str(e)}")

@app.post("/api/interview/{question_id}/response")
def submit_question_response(
    question_id: int, 
    payload: InterviewResponsePayload, 
    db: Session = Depends(get_db)
):
    """
    Saves candidate response and/or interviewer evaluation notes.
    Preserves all resume and assessment evidence separately.
    """
    question = db.query(models.InterviewQuestion).filter(models.InterviewQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Interview question not found")

    try:
        updated = save_interview_response(
            question_id=question_id,
            candidate_response=payload.candidate_response,
            interviewer_notes=payload.interviewer_notes,
            db=db
        )
        return {
            "message": "Interview response and notes saved successfully",
            "question": updated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save interview response: {str(e)}")

# ==========================================
# PHASE 6A: FINAL PROOFHIRE REPORT API
# ==========================================

@app.get("/api/reports/{analysis_id}")
def get_final_report(analysis_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the complete, unified ProofHire Evidence Report.
    Purely aggregates existing stored results across Phases 1-5 without re-running models.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    try:
        report_data = aggregate_proofhire_report(analysis_id=analysis_id, db=db)
        return report_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@app.post("/api/reports/{analysis_id}/refresh")
def refresh_final_report(analysis_id: int, db: Session = Depends(get_db)):
    """
    Refreshes report aggregation from the latest stored database records.
    Does not rerun LLM analysis or regenerate historical evidence.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    try:
        report_data = aggregate_proofhire_report(analysis_id=analysis_id, db=db)
        return {
            "message": "Report data refreshed successfully from stored records",
            **report_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh report: {str(e)}")



