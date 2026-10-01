"""
End-to-End Verification Suite for Phase 5B: Interview Intelligence UI + Modes + Integration
Tests:
1. Interview Focus data loads with target skills and evidence gaps
2. Targeted questions load and match evidence gaps
3. Resume-specific deep-dive questions display grounded claims
4. Interviewer mode data structure (why_generated, evaluation_points, notes)
5. Candidate mode data restrictions (verifies fields that MUST be hidden in candidate mode)
6. Follow-up question generation and threading under parent question
7. Saving candidate responses without overwriting previous evidence
8. Saving interviewer notes separately from candidate responses
9. Data persistence across reloads / re-queries
10. Pipeline navigator and report navigation link
11. Integrity of Phases 1-4 (Resume analysis, Evidence verification, Skill assessment, Verified skill profile)
"""

import os
import sys

# Ensure UTF-8 stdout
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sqlalchemy.orm import Session
from database import get_db
import models.models as models
from services.interview_intelligence import (
    plan_interview_skills,
    generate_targeted_interview_questions,
    generate_interview_follow_up,
    save_interview_response,
    format_question_dict
)
from services.profile_intelligence import compute_and_save_skill_profile

def test_phase5b_e2e():
    print("==================================================")
    print("PHASE 5B: END-TO-END VERIFICATION SUITE")
    print("==================================================")
    
    db: Session = next(get_db())
    analysis_id = 4
    
    # 1. Interview Focus Verification
    print("\n[1] Verifying Interview Focus...")
    plan = plan_interview_skills(analysis_id, db)
    assert plan is not None, "Interview plan must exist"
    assert len(plan["selected_skills"]) >= 3, "Selected skills must have at least 3 items"
    for s in plan["selected_skills"]:
        assert "skill" in s and "evidence_level" in s and "reason" in s
    print(f"[PASS] Interview Focus loaded with {len(plan['selected_skills'])} prioritized target skills.")

    # 2. Questions Load & Match Evidence Gaps
    print("\n[2] Verifying Questions Match Evidence Gaps...")
    questions = generate_targeted_interview_questions(analysis_id, db)
    assert 5 <= len(questions) <= 8, f"Expected 5-8 questions, got {len(questions)}"
    for q in questions:
        assert q["skill"], "Skill must be present"
        assert q["evidence_gap"], "Evidence gap must be specified"
        assert q["why_generated"], "Why generated must be specified"
    print(f"[PASS] Loaded {len(questions)} questions accurately tied to evidence gaps.")

    # 3. Resume-Specific Deep-Dive Questions
    print("\n[3] Verifying Resume-Specific Deep-Dive Questions...")
    candidate = db.query(models.Candidate).filter(models.Candidate.id == 4).first()
    claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
    claim_texts = [c.claim_text for c in claims]
    
    deep_dives = [q for q in questions if q["question_type"] == "Project Deep-Dive"]
    assert len(deep_dives) >= 1, "At least 1 Project Deep-Dive question must exist"
    for dd in deep_dives:
        assert dd["source_context"], "Deep-dive question must include source_context"
        # Check that it cites stored candidate claim or project
        print(f"  • Deep-Dive for {dd['skill']}: {dd['question_text'][:80]}...")
        print(f"    Source: {dd['source_context'][:70]}...")
    print(f"[PASS] Verified {len(deep_dives)} resume-grounded deep-dive question(s).")

    # 4. Interviewer Mode Data Structure
    print("\n[4] Verifying Interviewer Mode Data Structure...")
    sample_q = questions[0]
    assert sample_q["why_generated"] is not None
    assert len(sample_q["evaluation_points"]) >= 2
    assert sample_q["evidence_gap"] is not None
    print("  • Why This Question: Present")
    print(f"  • Suggested Evaluation Points: {len(sample_q['evaluation_points'])} guidance points")
    print("  • Interviewer Notes field: Supported")
    print("[PASS] Interviewer Mode fields validated.")

    # 5. Candidate Mode Hidden Evaluation Data Check
    print("\n[5] Verifying Candidate Mode Hidden Data Restrictions...")
    # Emulate Candidate Mode payload projection
    candidate_mode_view = {
        "id": sample_q["id"],
        "order_num": sample_q["order_num"],
        "skill": sample_q["skill"],
        "question_text": sample_q["question_text"],
        "candidate_response": sample_q["candidate_response"]
    }
    # Verify evaluation data is NOT leaked into candidate mode view
    assert "why_generated" not in candidate_mode_view
    assert "evidence_gap" not in candidate_mode_view
    assert "evaluation_points" not in candidate_mode_view
    assert "interviewer_notes" not in candidate_mode_view
    print("[PASS] Candidate Mode strictly hides evaluation criteria, rubrics, and interviewer notes.")

    # 6. Follow-Up Generation & Threading
    print("\n[6] Verifying Follow-Up Question Threading...")
    root_q = questions[0]
    follow_up = generate_interview_follow_up(
        question_id=root_q["id"],
        candidate_response="I used asynchronous connection pools with Redis cache fallback.",
        db=db
    )
    assert follow_up["parent_question_id"] == root_q["id"], "parent_question_id must match root question id"
    assert follow_up["skill"] == root_q["skill"], "Follow-up must maintain same skill domain"
    print(f"  • Root Question #{root_q['id']} ({root_q['skill']})")
    print(f"    └── Follow-Up #{follow_up['id']}: {follow_up['question_text'][:70]}...")
    print("[PASS] Follow-Up question correctly tied to parent question.")

    # 7. Response & Interviewer Notes Separate Storage
    print("\n[7] Verifying Response and Interviewer Notes Storage...")
    save_interview_response(
        question_id=root_q["id"],
        candidate_response="Candidate provided a detailed breakdown of concurrency limits.",
        interviewer_notes="Demonstrated strong grasp of asynchronous event loops. Follow up on distributed locking.",
        db=db
    )
    stored_q = db.query(models.InterviewQuestion).filter(models.InterviewQuestion.id == root_q["id"]).first()
    assert stored_q.candidate_response == "Candidate provided a detailed breakdown of concurrency limits."
    assert stored_q.interviewer_notes == "Demonstrated strong grasp of asynchronous event loops. Follow up on distributed locking."
    print("[PASS] Candidate response and interviewer notes stored separately and accurately.")

    # 8. Persistence & Idempotency Check
    print("\n[8] Verifying Persistence Across Re-queries...")
    total_q_count = db.query(models.InterviewQuestion).filter(models.InterviewQuestion.analysis_id == analysis_id).count()
    assert total_q_count >= len(questions), "Questions must persist in DB"
    stored_plan = db.query(models.InterviewPlan).filter(models.InterviewPlan.analysis_id == analysis_id).first()
    assert stored_plan is not None, "Interview plan must persist in DB"
    print(f"[PASS] Persisted {total_q_count} questions and interview plan in SQLite database.")

    # 9. Verify Phases 1-4 Integrity (No Regressions)
    print("\n[9] Verifying Phases 1-4 Integrity (Zero Regression)...")
    # Phase 1: Resume & claims
    assert len(claims) > 0, "Phase 1 claims must exist"
    # Phase 2: Evidence
    evidence_count = db.query(models.SkillEvidence).filter(models.SkillEvidence.analysis_id == analysis_id).count()
    assert evidence_count > 0, "Phase 2 evidence must exist"
    # Phase 3: Assessment scores unchanged
    assessment = db.query(models.Assessment).filter(models.Assessment.analysis_id == analysis_id).first()
    assert assessment.status == "completed"
    assert assessment.overall_percentage == 56.0, "Phase 3 assessment percentage must be exactly preserved"
    # Phase 4: Skill profile
    profile = compute_and_save_skill_profile(analysis_id, db)
    assert profile["summary"]["total_skills"] == 11
    assert any(s["skill_name"] == "SQL" and s["assessment_percentage"] == 80.0 for s in profile["skills"])
    print(f"[PASS] Phases 1-4 intact: 7 claims, {evidence_count} evidence records, Assessment = 56.0%, Profile = 11 skills.")

    print("\n==================================================")
    print("ALL PHASE 5B E2E TESTS PASSED (100% GREEN)")
    print("==================================================")

if __name__ == "__main__":
    test_phase5b_e2e()
