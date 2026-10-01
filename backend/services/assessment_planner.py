import os
import json
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv
from schemas.schemas import AssessmentPlanOutput, SelectedSkillPlan
from utils.retry import with_gemini_retry

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

def algorithmic_assessment_plan(
    job_required: List[str],
    job_preferred: List[str],
    candidate_skills: List[str],
    claims_info: List[Dict[str, Any]],
    skills_requiring_verification: List[str],
    potential_skill_gaps: List[str]
) -> List[Dict[str, Any]]:
    """
    Deterministic rule-based fallback prioritization:
    Priority order:
    1. Job-required skills with 'Needs Verification' or 'Limited Evidence'
    2. Job-required skills in skills_requiring_verification
    3. Job-required skills with 'Moderate Evidence' (needs additional demonstration)
    4. Job-required skills in potential_skill_gaps (gap check)
    5. Job-preferred skills with claimed evidence needing verification
    """
    evidence_by_skill = {}
    for c in claims_info:
        s = c.get("skill") or c.get("skill_name")
        if s:
            evidence_by_skill[s.lower()] = c.get("evidence_level") or "Needs Verification"

    all_target_skills = []
    
    # 1. Job required skills requiring verification or with limited/needs verification evidence
    for req in job_required:
        req_lower = req.lower()
        ev_level = evidence_by_skill.get(req_lower, "Needs Verification")
        
        priority = "Moderate"
        diff = "Intermediate"
        rationale = ""

        is_in_req_verif = any(req_lower in s.lower() for s in skills_requiring_verification)
        is_in_gaps = any(req_lower in s.lower() for s in potential_skill_gaps)

        if ev_level in ["Needs Verification", "Limited Evidence"]:
            priority = "High"
            diff = "Intermediate"
            rationale = f"Core job-required skill with '{ev_level}' on resume claims. Requires practical demonstration to establish baseline proficiency."
        elif ev_level == "Moderate Evidence":
            priority = "High"
            diff = "Intermediate"
            rationale = f"Core job-required skill with '{ev_level}'. Additional assessment provides objective demonstration of technical depth."
        elif is_in_req_verif:
            priority = "High"
            diff = "Intermediate"
            rationale = "Flagged during resume analysis as requiring verification for target job role."
        elif is_in_gaps:
            priority = "High"
            diff = "Basic"
            rationale = "Identified as a potential skill gap against job requirements. Assessing baseline competency."
        else:
            priority = "Moderate"
            diff = "Intermediate"
            rationale = f"Job-required skill. Current evidence: {ev_level}. Verifying comprehensive application."

        all_target_skills.append({
            "skill": req,
            "priority": priority,
            "evidence_level_before": ev_level,
            "recommended_difficulty": diff,
            "question_count": 3,
            "rationale": rationale
        })

    # Pick top 3-4 skills
    if not all_target_skills and candidate_skills:
        for s in candidate_skills[:3]:
            all_target_skills.append({
                "skill": s,
                "priority": "Moderate",
                "evidence_level_before": "Needs Verification",
                "recommended_difficulty": "Intermediate",
                "question_count": 3,
                "rationale": "Key candidate-claimed skill relevant to professional qualification."
            })

    # Deduplicate by skill name
    unique_skills = []
    seen = set()
    for item in all_target_skills:
        if item["skill"].lower() not in seen:
            seen.add(item["skill"].lower())
            unique_skills.append(item)

    # Sort High priority first, select 3 or 4 skills
    unique_skills.sort(key=lambda x: 0 if x["priority"] == "High" else 1)
    selected = unique_skills[:4]
    
    # Balance question counts to reach ~9-10 questions
    if len(selected) == 3:
        selected[0]["question_count"] = 4
        selected[1]["question_count"] = 3
        selected[2]["question_count"] = 3
    elif len(selected) == 4:
        selected[0]["question_count"] = 3
        selected[1]["question_count"] = 3
        selected[2]["question_count"] = 2
        selected[3]["question_count"] = 2
    elif len(selected) == 2:
        selected[0]["question_count"] = 5
        selected[1]["question_count"] = 5

    return selected

@with_gemini_retry("Assessment Planner Agent")
def plan_assessment_with_gemini(
    job_title: str,
    job_required: List[str],
    job_preferred: List[str],
    candidate_skills: List[str],
    claims_info: List[Dict[str, Any]],
    skills_requiring_verification: List[str],
    potential_skill_gaps: List[str],
    model_name: str = "gemini-3.5-flash"
) -> AssessmentPlanOutput:
    """
    Intelligent Assessment Planning Agent using Gemini with fallback.
    Selects 3 to 4 job-relevant skills prioritizing:
    - Job-required skills
    - Claimed skills with Limited or Moderate Evidence
    - Skills marked Needs Verification
    - Potential skill gaps
    Explains internally why each skill was selected.
    """
    prompt = f"""
    You are the Assessment Planning Agent for "ProofHire AI".
    Your objective is to determine WHICH 3 to 4 professional skills MUST be assessed for this candidate.
    
    INPUT DATA:
    Target Job: {job_title}
    Required Skills: {json.dumps(job_required)}
    Preferred Skills: {json.dumps(job_preferred)}
    
    Candidate Claimed Skills: {json.dumps(candidate_skills)}
    Skills Requiring Verification: {json.dumps(skills_requiring_verification)}
    Potential Skill Gaps: {json.dumps(potential_skill_gaps)}
    Candidate Claims & Evidence Levels: {json.dumps(claims_info)}
    
    PRIORITIZATION RULES:
    1. Assess ONLY job-related skills. Never assess irrelevant or personal skills.
    2. Give highest priority to Job-Required skills that:
       - Have 'Limited Evidence' or 'Needs Verification'
       - Have 'Moderate Evidence' needing practical demonstration
       - Are in 'Skills Requiring Verification' or 'Potential Skill Gaps'
    3. Select 3 to 4 skills total.
    4. For each selected skill, assign:
       - 'priority': 'High' or 'Moderate'
       - 'evidence_level_before': The candidate's evidence level before this assessment (e.g., 'Needs Verification', 'Limited Evidence', 'Moderate Evidence', or 'Good Evidence')
       - 'recommended_difficulty': 'Basic', 'Intermediate', or 'Advanced' based on candidate background
       - 'question_count': integer between 2 and 4 (total questions across all selected skills should sum to 8-10)
       - 'rationale': A clear, professional explanation of WHY this skill was selected based on job requirements and evidence state.
       
    Respond STRICTLY in JSON matching the specified schema.
    """
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AssessmentPlanOutput
            )
        )
        data = json.loads(response.text)
        plan = AssessmentPlanOutput(**data)
        if plan.selected_skills:
            return plan
    except Exception as e:
        print(f"Gemini Assessment Planner warning: {e}. Using deterministic planning rules.")

    # Fallback to algorithmic plan
    fallback_items = algorithmic_assessment_plan(
        job_required, job_preferred, candidate_skills, claims_info,
        skills_requiring_verification, potential_skill_gaps
    )
    selected_plans = [SelectedSkillPlan(**item) for item in fallback_items]
    return AssessmentPlanOutput(
        selected_skills=selected_plans,
        planning_summary="Assessment planned using ProofHire priority selection matrix based on job requirements and evidence verification gaps."
    )
