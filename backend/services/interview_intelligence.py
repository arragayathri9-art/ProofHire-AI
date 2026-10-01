"""
Interview Intelligence Service - Phase 5A: Planning + Backend

Generates evidence-aware, non-generic interview questions based strictly on:
- Target job requirements
- Stored resume claims & projects
- Evidence Verification results & access status
- Skill Assessment performance
- Verified Skill Profile evidence gaps

DECISION SUPPORT ONLY:
- NO Hire / Reject recommendations
- NO candidate rankings
- NO employability or job-fit scores
- NO personality inferences
- Strict groundedness in actual candidate data (zero hallucinated projects or achievements)
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from google import genai
from dotenv import load_dotenv

import models.models as models
from services.profile_intelligence import compute_and_save_skill_profile, normalize_skill, skill_matches

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

# --- Section 1: Interview Planning Service ---

def plan_interview_skills(analysis_id: int, db: Session) -> Dict[str, Any]:
    """
    Identifies and prioritizes skills that require deeper interview verification.
    Prioritization criteria:
    1. Job-required skills with Needs Verification
    2. Job-required skills with Limited Evidence
    3. Important skills with Partial or Limited assessment demonstration
    4. Resume claims with unverified or submitted-only evidence
    5. Gaps between resume claims and assessment performance
    Avoids wasting interview time on strongly supported skills unless role-critical.
    """
    # Ensure profile data is fresh
    profile = compute_and_save_skill_profile(analysis_id=analysis_id, db=db)
    
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    candidate_claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
    
    # Sort and evaluate skills
    prioritized_skills: List[Dict[str, Any]] = []
    
    for skill_item in profile["skills"]:
        s_name = skill_item["skill_name"]
        ev_level = skill_item["evidence_level"]
        is_req = skill_item["is_required"]
        is_pref = skill_item["is_preferred"]
        pct = skill_item["assessment_percentage"]
        label = skill_item["assessment_label"]
        claims_count = skill_item["claims_count"]
        retrieved_ev = skill_item["retrieved_evidence_count"]
        
        priority_weight = 0
        reasons: List[str] = []
        
        # 1. Job-required with Needs Verification
        if is_req and ev_level == "Needs Verification":
            priority_weight += 50
            reasons.append("Job-required skill that currently has 'Needs Verification' with no corroborating evidence.")
            
        # 2. Job-required with Limited Evidence
        elif is_req and ev_level == "Limited Evidence":
            priority_weight += 40
            reasons.append(f"Job-required skill with 'Limited Evidence'. Assessment demonstration: {label} ({pct:.1f}%)." if pct is not None else "Job-required skill with 'Limited Evidence'.")
            
        # 3. Assessment Partial or Limited Demonstration
        if pct is not None and pct < 70.0:
            priority_weight += 35
            reasons.append(f"Candidate demonstrated {pct:.1f}% performance ({label}) in targeted assessment; deeper technical probing is needed.")
            
        # 4. Resume claim present but unverified / submitted-only
        if claims_count > 0 and retrieved_ev == 0:
            priority_weight += 25
            reasons.append(f"{claims_count} explicit resume claim(s) exist without inspected verification.")
            
        # 5. Preferred skill with Needs Verification
        if is_pref and ev_level in ["Needs Verification", "Limited Evidence"]:
            priority_weight += 20
            reasons.append("Job-preferred skill requiring practical clarification.")
            
        # Strongly supported skills (e.g. Good/Strong Evidence with >= 70% assessment)
        if ev_level in ["Strong Evidence", "Good Evidence"] and (pct is not None and pct >= 70.0):
            # De-prioritize to avoid wasting interview time
            priority_weight -= 30
            
        if priority_weight > 0:
            full_reason = " ".join(reasons)
            prioritized_skills.append({
                "skill": s_name,
                "priority_weight": priority_weight,
                "evidence_level": ev_level,
                "is_required": is_req,
                "is_preferred": is_pref,
                "assessment_percentage": pct,
                "assessment_label": label,
                "claims_count": claims_count,
                "reason": full_reason
            })

    # Sort descending by priority weight
    prioritized_skills.sort(key=lambda x: x["priority_weight"], reverse=True)
    
    # Select top 4-6 target skills
    selected_for_interview = prioritized_skills[:6]
    
    planning_summary = (
        f"Selected {len(selected_for_interview)} high-priority skill areas targeting unverified claims, "
        f"assessment performance gaps, and critical job requirements."
    )
    
    # Save or update interview plan in database
    existing_plan = db.query(models.InterviewPlan).filter(models.InterviewPlan.analysis_id == analysis_id).first()
    if existing_plan:
        existing_plan.planning_summary = planning_summary
        existing_plan.selected_skills = selected_for_interview
        existing_plan.updated_at = datetime.utcnow()
    else:
        new_plan = models.InterviewPlan(
            analysis_id=analysis_id,
            planning_summary=planning_summary,
            selected_skills=selected_for_interview
        )
        db.add(new_plan)
        
    db.commit()
    
    return {
        "analysis_id": analysis_id,
        "planning_summary": planning_summary,
        "selected_skills": selected_for_interview
    }


# --- Section 2, 3, 4: Question Generation Engine ---

def generate_targeted_interview_questions(analysis_id: int, db: Session) -> List[Dict[str, Any]]:
    """
    Generates 5-8 targeted, non-generic interview questions strictly anchored
    to candidate claims, evidence gaps, and job requirements.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise ValueError("Analysis not found")
        
    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    candidate_claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
    candidate_projects = candidate.projects or []
    
    # 1. Run or get interview plan
    plan_data = plan_interview_skills(analysis_id=analysis_id, db=db)
    selected_skills = plan_data["selected_skills"]
    
    if not selected_skills:
        # Fallback if all skills were somehow strong: pick top required
        for req in (job.required_skills or [])[:4]:
            selected_skills.append({
                "skill": req,
                "reason": f"Core target job requirement for {job.title}.",
                "evidence_level": "Needs Verification",
                "assessment_percentage": None,
                "assessment_label": "Not Assessed"
            })

    # Try Gemini generation with prompt grounded in real candidate claims
    generated_questions = []
    
    try:
        gemini_questions = call_gemini_question_generator(
            job_title=job.title,
            selected_skills=selected_skills,
            claims=candidate_claims,
            projects=candidate_projects
        )
        if gemini_questions and len(gemini_questions) >= 4:
            generated_questions = gemini_questions
    except Exception as e:
        print(f"Gemini Interview Generator fallback triggered: {e}")

    # Fallback to algorithmic generator if Gemini is unavailable or rate-limited
    if not generated_questions:
        generated_questions = algorithmic_question_generator(
            job_title=job.title,
            selected_skills=selected_skills,
            claims=candidate_claims,
            projects=candidate_projects
        )

    # 4. Save generated questions into database
    # Clean up previous questions for this analysis on fresh generation
    db.query(models.InterviewQuestion).filter(
        models.InterviewQuestion.analysis_id == analysis_id
    ).delete()
    
    saved_objects = []
    for idx, q in enumerate(generated_questions):
        db_q = models.InterviewQuestion(
            analysis_id=analysis_id,
            order_num=idx + 1,
            skill=q.get("skill", "General Technical"),
            question_type=q.get("question_type", "Technical"),
            difficulty=q.get("difficulty", "Intermediate"),
            question_text=q.get("question_text", ""),
            source_context=q.get("source_context", ""),
            evidence_gap=q.get("evidence_gap", "Needs Verification"),
            why_generated=q.get("why_generated", ""),
            evaluation_points=q.get("evaluation_points", []),
            candidate_response=None,
            interviewer_notes=None
        )
        db.add(db_q)
        saved_objects.append(db_q)

    db.commit()
    for obj in saved_objects:
        db.refresh(obj)
        
    return [format_question_dict(q) for q in saved_objects]


def call_gemini_question_generator(
    job_title: str,
    selected_skills: List[Dict[str, Any]],
    claims: List[models.CandidateClaim],
    projects: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Invokes Gemini to generate explainable interview questions strictly from stored candidate facts."""
    if not api_key:
        return []

    # Prepare stored facts
    claims_text = "\n".join([f"- Claim: \"{c.claim_text}\" (Source: {c.source_section}, Evidence Level: {c.evidence_level})" for c in claims[:8]])
    projects_text = "\n".join([f"- Project: \"{p.get('project_name', '')}\" - {p.get('description', '')}" for p in projects[:4]])
    skills_text = "\n".join([f"- Skill: {s['skill']} | Evidence Gap: {s['evidence_level']} | Reason: {s['reason']}" for s in selected_skills])

    prompt = f"""You are the ProofHire AI Interview Intelligence Agent.
Generate 5 to 7 highly targeted interview questions for a candidate applying for '{job_title}'.

STRICT RULES:
1. Ground questions ONLY in the actual stored claims and projects below. DO NOT invent fake projects or technologies.
2. If referencing a project or claim, cite the candidate's exact wording in 'source_context'.
3. Every question must have an explicit 'why_generated' stating the evidence gap and role relevance.
4. Question types must be one of:
   - Technical
   - Scenario
   - Project Deep-Dive
   - Debugging / Problem Solving
   - Evidence Clarification
5. Do NOT provide Hire/Reject decisions, employability ratings, or personality judgments.

TARGET SKILLS & GAPS:
{skills_text}

CANDIDATE STORED CLAIMS:
{claims_text}

CANDIDATE STORED PROJECTS:
{projects_text}

Return a valid JSON array of objects with fields:
[
  {{
    "skill": "skill name",
    "question_type": "Project Deep-Dive | Technical | Scenario | Debugging / Problem Solving | Evidence Clarification",
    "difficulty": "Intermediate | Advanced",
    "question_text": "targeted question text",
    "source_context": "exact quote from resume claim or project or assessment gap",
    "evidence_gap": "e.g. Limited Evidence | Needs Verification | Partial Demonstration (53.3%)",
    "why_generated": "Specific justification for why this question is needed for the target job",
    "evaluation_points": ["point 1", "point 2", "point 3"]
  }}
]
"""
    models_to_try = ["gemini-3.8-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    last_err = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            data = json.loads(text)
            if isinstance(data, list) and len(data) >= 4:
                return data
            elif isinstance(data, dict) and "questions" in data:
                return data["questions"]
        except Exception as e:
            last_err = e
            continue
    
    if last_err:
        print(f"Gemini Question Generation note: {last_err}")
    return []


def algorithmic_question_generator(
    job_title: str,
    selected_skills: List[Dict[str, Any]],
    claims: List[models.CandidateClaim],
    projects: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    100% deterministic question generator that constructs grounded questions
    directly from candidate claims and verified evidence gaps.
    Guarantees zero invented technologies or projects.
    """
    questions: List[Dict[str, Any]] = []

    # Match claims to selected skills
    for skill_info in selected_skills:
        s_name = skill_info["skill"]
        ev_gap = skill_info["evidence_level"]
        reason = skill_info["reason"]
        pct = skill_info.get("assessment_percentage")
        
        # 1. Look for matching resume claims for Project Deep-Dive
        matching_claim = None
        for c in claims:
            if skill_matches(s_name, c.claim_text) or (c.skill and skill_matches(s_name, c.skill.skill_name)):
                matching_claim = c
                break

        if matching_claim:
            claim_snippet = matching_claim.claim_text.strip()
            questions.append({
                "skill": s_name,
                "question_type": "Project Deep-Dive",
                "difficulty": "Intermediate",
                "question_text": f"In your resume you noted: \"{claim_snippet}\". Could you walk through the architectural design, trade-offs you considered, and how you verified these results in production?",
                "source_context": f"Resume Claim: \"{claim_snippet}\"",
                "evidence_gap": ev_gap,
                "why_generated": f"{s_name} is relevant to the {job_title} role, but currently has {ev_gap}. Probing this specific claim verifies depth of execution.",
                "evaluation_points": [
                    "Technical depth and clarity of execution",
                    "Understanding of design trade-offs and alternative approaches",
                    "Methodology used to measure claimed efficiency or outcome",
                    "Production reliability and error handling considerations"
                ]
            })
            continue

        # 2. Look for matching projects
        matching_proj = None
        for p in projects:
            p_desc = p.get("description", "")
            p_techs = p.get("technologies") or []
            if any(skill_matches(s_name, t) for t in p_techs) or skill_matches(s_name, p_desc):
                matching_proj = p
                break

        if matching_proj:
            p_name = matching_proj.get("project_name", "your project")
            questions.append({
                "skill": s_name,
                "question_type": "Project Deep-Dive",
                "difficulty": "Intermediate",
                "question_text": f"In your project \"{p_name}\", how did you utilize {s_name}? Describe your approach to structuring the solution and addressing edge cases.",
                "source_context": f"Project: \"{p_name}\" ({matching_proj.get('description', '')})",
                "evidence_gap": ev_gap,
                "why_generated": f"Supporting evidence for {s_name} in {p_name} was submitted but requires conversational deep-dive to verify hands-on mastery.",
                "evaluation_points": [
                    f"Core {s_name} patterns and best practices",
                    "Architectural structuring and component decoupling",
                    "Edge case handling and validation strategies"
                ]
            })
            continue

        # 3. Assessment-based question if assessment demonstration was partial/limited
        if pct is not None and pct < 70.0:
            questions.append({
                "skill": s_name,
                "question_type": "Debugging / Problem Solving",
                "difficulty": "Intermediate",
                "question_text": f"In the technical assessment for {s_name}, you achieved {pct:.1f}% ({skill_info.get('assessment_label', '')}). When designing a robust {s_name} workflow, how do you diagnose performance bottlenecks and resolve unexpected edge failures?",
                "source_context": f"Assessment Demonstration: {pct:.1f}% ({skill_info.get('assessment_label', '')})",
                "evidence_gap": f"Partial Assessment Demonstration ({pct:.1f}%)",
                "why_generated": f"The candidate demonstrated partial proficiency in the standardized assessment. This problem-solving question evaluates real-world diagnostic capability.",
                "evaluation_points": [
                    "Systematic debugging and root cause analysis",
                    "Knowledge of standard profiling and monitoring tools",
                    "Resilience patterns and recovery strategies"
                ]
            })
            continue

        # 4. Scenario question for job-required skills with Needs Verification
        questions.append({
            "skill": s_name,
            "question_type": "Scenario",
            "difficulty": "Intermediate",
            "question_text": f"The {job_title} role requires working with {s_name}. Imagine you need to implement a scalable {s_name} component under high concurrency with strict latency requirements. How would you design and validate the implementation?",
            "source_context": f"Target Job Requirement: {s_name} (Evidence Level: {ev_gap})",
            "evidence_gap": ev_gap,
            "why_generated": f"{s_name} is required for the {job_title} role but currently lacks verified evidence in the profile.",
            "evaluation_points": [
                "Scalability and concurrency architecture",
                "Latency management and resource efficiency",
                "Testing and validation methodology"
            ]
        })

    # Ensure at least 5 questions
    if len(questions) < 5 and claims:
        for c in claims:
            if len(questions) >= 6:
                break
            if not any(c.claim_text in q["source_context"] for q in questions):
                questions.append({
                    "skill": c.skill.skill_name if c.skill else "Engineering Practice",
                    "question_type": "Evidence Clarification",
                    "difficulty": "Intermediate",
                    "question_text": f"Regarding your claim: \"{c.claim_text}\", what specific tooling, metrics, and validation tests did you deploy to achieve this outcome?",
                    "source_context": f"Resume Claim: \"{c.claim_text}\"",
                    "evidence_gap": c.evidence_level or "Needs Verification",
                    "why_generated": "Claimed accomplishment on resume lacks corroborating external repository evidence.",
                    "evaluation_points": [
                        "Clarity of individual contribution",
                        "Accuracy and rigor of measurement metrics",
                        "Tooling selection rationale"
                    ]
                })

    return questions[:8]


# --- Section 5: Follow-Up Backend ---

def generate_interview_follow_up(
    question_id: int,
    candidate_response: str,
    db: Session
) -> Dict[str, Any]:
    """
    Generates a targeted follow-up question strictly connected to the parent question's
    skill and context domain.
    """
    parent_q = db.query(models.InterviewQuestion).filter(models.InterviewQuestion.id == question_id).first()
    if not parent_q:
        raise ValueError("Parent interview question not found")

    skill = parent_q.skill
    context = parent_q.source_context or ""
    
    # Generate follow-up probing deeper
    follow_up_text = (
        f"Following up on your explanation of {skill}: Can you elaborate on the specific failure modes you encountered, "
        f"and how you ensured zero data loss or downtime during deployment?"
    )
    
    # If candidate provided an actual response, attempt context-aware probe
    if candidate_response and len(candidate_response.strip()) > 20:
        clean_resp = candidate_response.strip()
        follow_up_text = (
            f"You mentioned that \"{clean_resp[:80]}...\". How would your approach change if system traffic increased tenfold "
            f"or if upstream dependencies experienced intermittent latency spikes?"
        )

    # Calculate next order number
    max_order = db.query(models.InterviewQuestion).filter(
        models.InterviewQuestion.analysis_id == parent_q.analysis_id
    ).count()

    follow_up = models.InterviewQuestion(
        analysis_id=parent_q.analysis_id,
        order_num=max_order + 1,
        skill=skill,
        question_type="Technical",
        difficulty="Advanced",
        question_text=follow_up_text,
        source_context=f"Follow-up to Question #{parent_q.id}: \"{parent_q.question_text[:70]}...\"",
        evidence_gap=parent_q.evidence_gap,
        why_generated=f"Follow-up probe to test depth, edge cases, and boundary conditions for {skill}.",
        evaluation_points=[
            f"Depth of architectural reasoning for {skill}",
            "Handling of scalability constraints and degradation",
            "Clarity under technical scrutiny"
        ],
        parent_question_id=parent_q.id,
        candidate_response=None,
        interviewer_notes=None
    )
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)

    return format_question_dict(follow_up)


# --- Section 6: Response & Notes Storage ---

def save_interview_response(
    question_id: int,
    candidate_response: Optional[str],
    interviewer_notes: Optional[str],
    db: Session
) -> Dict[str, Any]:
    """
    Stores candidate response and interviewer evaluation notes on the question.
    Preserves all existing resume and assessment evidence separately.
    """
    question = db.query(models.InterviewQuestion).filter(models.InterviewQuestion.id == question_id).first()
    if not question:
        raise ValueError("Interview question not found")

    if candidate_response is not None:
        question.candidate_response = candidate_response
    if interviewer_notes is not None:
        question.interviewer_notes = interviewer_notes

    db.commit()
    db.refresh(question)

    return format_question_dict(question)


def format_question_dict(q: models.InterviewQuestion) -> Dict[str, Any]:
    """Helper to convert InterviewQuestion ORM model to dictionary."""
    return {
        "id": q.id,
        "analysis_id": q.analysis_id,
        "order_num": q.order_num,
        "skill": q.skill,
        "question_type": q.question_type,
        "difficulty": q.difficulty,
        "question_text": q.question_text,
        "source_context": q.source_context,
        "evidence_gap": q.evidence_gap,
        "why_generated": q.why_generated,
        "evaluation_points": q.evaluation_points or [],
        "parent_question_id": q.parent_question_id,
        "candidate_response": q.candidate_response,
        "interviewer_notes": q.interviewer_notes,
        "created_at": q.created_at.isoformat() if q.created_at else None
    }
