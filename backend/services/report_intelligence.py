"""
Report Intelligence Service - Phase 6A: Final ProofHire Report

Aggregates existing stored results across all 5 verification phases:
1. Resume Analysis (Phase 1)
2. Evidence Verification (Phase 2)
3. Skill Assessment (Phase 3)
4. Verified Skill Profile (Phase 4)
5. Interview Intelligence (Phase 5)

STRICT DECISION SUPPORT PRINCIPLES:
- Pure aggregation of stored database facts.
- ZERO rerun of LLM prompts or scoring models.
- ZERO Hire / Reject recommendations.
- ZERO employability scores, job-fit percentages, or candidate rankings.
- Factual traceability connecting all findings to underlying pipeline records.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import models.models as models
from services.profile_intelligence import compute_and_save_skill_profile, map_assessment_percentage_to_label

def aggregate_proofhire_report(analysis_id: int, db: Session) -> Dict[str, Any]:
    """
    Constructs a complete, factual snapshot of candidate evaluation dossier
    strictly from stored database records.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise ValueError("Analysis session not found")

    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    resume = db.query(models.Resume).filter(models.Resume.candidate_id == candidate.id).order_by(models.Resume.id.desc()).first()

    # 1. Fetch Phase 1 Data (Resume & Claims)
    candidate_skills = [s.skill_name for s in db.query(models.CandidateSkill).filter(models.CandidateSkill.candidate_id == candidate.id).all()]
    claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
    
    # 2. Fetch Phase 2 Data (Evidence Verification)
    evidence_records = db.query(models.SkillEvidence).filter(models.SkillEvidence.analysis_id == analysis.id).all()
    
    # Phase 7B: Separate certificate evidence records for dedicated report section
    certificate_evidence_records = [
        ev for ev in evidence_records if getattr(ev, 'evidence_type', '') == 'certificate'
    ]
    non_certificate_evidence_records = [
        ev for ev in evidence_records if getattr(ev, 'evidence_type', '') != 'certificate'
    ]
    
    # 3. Fetch Phase 3 Data (Assessment)
    assessment = db.query(models.Assessment).filter(models.Assessment.analysis_id == analysis.id).first()
    assessment_results = []
    if assessment:
        assessment_results = db.query(models.AssessmentResult).filter(models.AssessmentResult.assessment_id == assessment.id).all()

    # 4. Fetch Phase 4 Data (Verified Skill Profile)
    skill_verifications = db.query(models.SkillVerification).filter(models.SkillVerification.analysis_id == analysis.id).all()
    if not skill_verifications:
        # If not computed yet, compute and save once
        compute_and_save_skill_profile(analysis_id=analysis.id, db=db)
        skill_verifications = db.query(models.SkillVerification).filter(models.SkillVerification.analysis_id == analysis.id).all()

    # 5. Fetch Phase 5 Data (Interview Intelligence)
    interview_plan = db.query(models.InterviewPlan).filter(models.InterviewPlan.analysis_id == analysis.id).first()
    interview_questions = db.query(models.InterviewQuestion).filter(
        models.InterviewQuestion.analysis_id == analysis.id
    ).order_by(models.InterviewQuestion.order_num).all()

    # --- Construct Section 1: Header ---
    report_date = datetime.utcnow().strftime("%B %d, %Y")
    header = {
        "title": "PROOFHIRE EVIDENCE REPORT",
        "subtitle": "Evidence-based summary generated from the ProofHire verification pipeline.",
        "candidate_name": candidate.name,
        "candidate_email": candidate.email or "N/A",
        "candidate_location": candidate.location or "N/A",
        "target_job": job.title,
        "company": job.company or "ProofHire Enterprise",
        "analysis_id": analysis.id,
        "report_generated_date": report_date
    }

    # --- Construct Section 2: Executive Summary ---
    total_skills = len(skill_verifications)
    strong_count = sum(1 for sv in skill_verifications if sv.evidence_level == "Strong Evidence")
    good_count = sum(1 for sv in skill_verifications if sv.evidence_level == "Good Evidence")
    moderate_count = sum(1 for sv in skill_verifications if sv.evidence_level == "Moderate Evidence")
    limited_count = sum(1 for sv in skill_verifications if sv.evidence_level == "Limited Evidence")
    needs_verif_count = sum(1 for sv in skill_verifications if sv.evidence_level == "Needs Verification")
    
    well_supported_count = strong_count + good_count
    needs_more_evidence_count = moderate_count + limited_count + needs_verif_count

    exec_summary_text = (
        f"ProofHire synthesized multi-source evidence across resume claims, external submitted artifacts, "
        f"standardized technical assessments, and targeted interview probes for the target role of '{job.title}'. "
        f"A total of {total_skills} job-relevant skills were evaluated: {well_supported_count} skill(s) currently demonstrate "
        f"strong or good empirical support, while {needs_more_evidence_count} skill area(s) may benefit from further practical verification. "
        f"This document provides transparent, factual decision support for human hiring reviewers."
    )

    executive_summary = {
        "summary_text": exec_summary_text,
        "metrics": {
            "total_skills_analyzed": total_skills,
            "well_supported_count": well_supported_count,
            "needs_further_verification_count": needs_more_evidence_count,
            "strong_evidence": strong_count,
            "good_evidence": good_count,
            "moderate_evidence": moderate_count,
            "limited_evidence": limited_count,
            "needs_verification": needs_verif_count,
            "total_claims_recorded": len(claims),
            "evidence_sources_tracked": len(evidence_records),
            "certificate_evidence_submitted": len(certificate_evidence_records),
            "assessment_completed": assessment.status == "completed" if assessment else False,
            "assessment_overall_score": assessment.overall_percentage if assessment else None,
            "interview_probes_generated": len(interview_questions)
        }
    }

    # --- Construct Section 3: Evidence Journey ---
    evidence_journey = [
        {
            "step": 1,
            "name": "Resume Analysis",
            "status": "Completed",
            "summary": f"{len(candidate_skills)} skills identified, {len(claims)} professional claims extracted from resume."
        },
        {
            "step": 2,
            "name": "Evidence Verification",
            "status": "Completed",
            "summary": f"{len(non_certificate_evidence_records)} external evidence artifact(s) evaluated. {len(certificate_evidence_records)} certificate(s) submitted."
        },
        {
            "step": 3,
            "name": "Skill Assessment",
            "status": "Completed" if (assessment and assessment.status == "completed") else "In Progress",
            "summary": f"Completed {len(assessment_results)} skill evaluations (Overall Score: {assessment.overall_percentage:.1f}%)" if (assessment and assessment.overall_percentage is not None) else "No standardized assessment completed."
        },
        {
            "step": 4,
            "name": "Verified Skill Profile",
            "status": "Completed",
            "summary": f"Categorized {total_skills} skills using deterministic multi-source evidence aggregation."
        },
        {
            "step": 5,
            "name": "Interview Intelligence",
            "status": "Completed" if len(interview_questions) > 0 else "Ready",
            "summary": f"{len(interview_questions)} evidence-anchored interview probes generated focusing on remaining verification gaps."
        }
    ]

    # --- Construct Section 4: Resume Analysis (Phase 1) ---
    resume_section = {
        "filename": resume.filename if resume else "candidate_resume.pdf",
        "skills_identified": candidate_skills,
        "projects": candidate.projects or [],
        "education": candidate.education or [],
        "certifications": candidate.certifications or [],
        "professional_claims_count": len(claims),
        "potential_skill_gaps": analysis.potential_skill_gaps or []
    }

    # --- Construct Section 5: Evidence Verification (Phase 2) ---
    evidence_section_claims = []
    for c in claims:
        evidence_section_claims.append({
            "id": c.id,
            "claim_text": c.claim_text,
            "source_section": c.source_section,
            "verification_status": c.verification_status,
            "evidence_level": c.evidence_level or "Needs Verification",
            "evidence_access_status": c.evidence_access_status or ("retrieved" if c.evidence_level in ["Strong Evidence", "Good Evidence"] else "submitted_only"),
            "evidence_used": c.evidence_used or "Resume claim documentation",
            "what_supports": c.what_supports or "Direct candidate claim in resume",
            "what_is_missing": c.what_is_missing or "External repository inspection or live demonstration"
        })

    # --- Construct Section 5B: Certificate Evidence (Phase 7B) ---
    certificate_evidence_section = []
    for ev in certificate_evidence_records:
        cert_skills = ev.supported_skills or []
        url_verif = getattr(ev, 'url_verification_data', None) or {}
        cred_comparison = getattr(ev, 'credential_comparison', None) or {}
        
        certificate_evidence_section.append({
            "id": ev.id,
            "certificate_name": getattr(ev, 'certificate_name', None) or ev.title or "Certificate",
            "issuer": getattr(ev, 'issuer', None) or "Issuing Organization",
            "candidate_name": getattr(ev, 'candidate_name', None),
            "issue_date": getattr(ev, 'issue_date', None),
            "expiry_date": getattr(ev, 'expiry_date', None),
            "credential_id": getattr(ev, 'credential_id', None),
            "credential_url": ev.url or getattr(ev, 'credential_url', None),
            "skills_covered": cert_skills,
            "verification_status": getattr(ev, 'verification_status', 'DOCUMENT EXTRACTED'),
            "document_extraction_status": getattr(ev, 'document_extraction_status', None),
            "url_verification": url_verif,
            "credential_comparison": cred_comparison,
            "evidence_weight": {
                "type": "credential_supporting",
                "label": "Credential / Supporting Evidence",
                "note": "Certificate is supporting evidence. Practical demonstration (assessment/GitHub) provides stronger proof."
            },
            "integrity_disclaimer": (
                "ProofHire does NOT claim this certificate is authentic based on document existence alone. "
                "Only documented extraction and reachable verification URLs were validated."
            ),
            "summary": ev.description or f"Certificate submitted for {', '.join(cert_skills[:3]) if cert_skills else 'technical qualification'}."
        })

    # --- Construct Section 6: Skill Assessment (Phase 3) ---
    assessment_section = {
        "status": assessment.status if assessment else "not_generated",
        "overall_percentage": assessment.overall_percentage if assessment else None,
        "total_score": assessment.total_score if assessment else None,
        "total_max_score": assessment.total_max_score if assessment else None,
        "results": [
            {
                "skill": ar.skill,
                "score": ar.score,
                "max_score": ar.max_score,
                "percentage": ar.percentage,
                "demonstration_level": ar.demonstration_level,
                "evidence_before": ar.evidence_before_assessment,
                "feedback": ar.feedback_summary
            }
            for ar in assessment_results
        ]
    }

    # --- Construct Section 7 & 8: Verified Skill Profile & Matrix (Phase 4) ---
    skill_matrix = []
    well_supported_skills = []
    needs_further_verification_skills = []

    for sv in skill_verifications:
        # Determine matrix string representations
        resume_str = f"Claimed ({sv.claims_count})" if sv.resume_claim_present else "Not clearly claimed"
        
        if sv.retrieved_evidence_count > 0:
            evidence_str = f"{sv.retrieved_evidence_count} inspected source(s)"
        elif sv.evidence_count > 0:
            evidence_str = f"{sv.evidence_count} submitted source(s)"
        else:
            evidence_str = "No inspected evidence"

        if sv.assessment_percentage is not None:
            assessment_str = f"{sv.assessment_percentage:.1f}% ({sv.assessment_label})"
        else:
            assessment_str = "Not assessed"

        item_dict = {
            "skill": sv.skill_name,
            "resume": resume_str,
            "evidence": evidence_str,
            "assessment": assessment_str,
            "evidence_level": sv.evidence_level,
            "job_group": sv.job_group,
            "explanation": sv.explanation,
            "next_verification_step": sv.next_verification_step
        }
        skill_matrix.append(item_dict)

        if sv.evidence_level in ["Strong Evidence", "Good Evidence"]:
            well_supported_skills.append({
                "skill": sv.skill_name,
                "evidence_level": sv.evidence_level,
                "summary": sv.explanation
            })
        else:
            needs_further_verification_skills.append({
                "skill": sv.skill_name,
                "evidence_level": sv.evidence_level,
                "next_step": sv.next_verification_step,
                "summary": sv.explanation
            })

    # --- Construct Section 9: Interview Intelligence (Phase 5) ---
    interview_focus = interview_plan.selected_skills if interview_plan else []
    
    interview_questions_list = []
    for q in interview_questions:
        interview_questions_list.append({
            "id": q.id,
            "order_num": q.order_num,
            "skill": q.skill,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "question_text": q.question_text,
            "source_context": q.source_context,
            "why_generated": q.why_generated,
            "candidate_response": q.candidate_response,
            "has_response": bool(q.candidate_response),
            "parent_question_id": q.parent_question_id,
            "is_follow_up": q.parent_question_id is not None
        })

    # --- Construct Section 10: Disclaimer ---
    disclaimer = (
        "ProofHire provides evidence-based decision support. The report summarizes "
        "information available to the system and does not constitute an automated "
        "hiring decision. Final employment decisions remain with the responsible human reviewer."
    )

    return {
        "analysis_id": analysis.id,
        "header": header,
        "executive_summary": executive_summary,
        "evidence_journey": evidence_journey,
        "resume_analysis": resume_section,
        "evidence_verification": evidence_section_claims,
        "certificate_evidence": certificate_evidence_section,  # Phase 7B
        "skill_assessment": assessment_section,
        "skill_matrix": skill_matrix,
        "well_supported_skills": well_supported_skills,
        "needs_further_verification_skills": needs_further_verification_skills,
        "needs_verification_notice": (
            "'Needs Further Verification' does not mean the candidate lacks the skill. "
            "It means ProofHire currently has insufficient evidence to establish stronger support."
        ),
        "interview_intelligence": {
            "focus_skills": interview_focus,
            "questions": interview_questions_list,
            "questions_count": len(interview_questions_list)
        },
        "disclaimer": disclaimer
    }
