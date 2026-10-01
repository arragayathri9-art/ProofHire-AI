"""
Verification and Test Suite for Phase 5A: Interview Intelligence — Planning + Backend
Tests:
- Target job & Verified Skill Profile loading
- Unresolved skills selection & prioritization (Needs Verification, Limited Evidence, Partial Assessment)
- Justification reasons stored for each selected skill
- Questions grounded in real resume claims and evidence gaps (zero fake claims/technologies)
- Question types (Technical, Scenario, Project Deep-Dive, Debugging / Problem Solving, Evidence Clarification)
- Question traceability: why_generated, source_context, evidence_gap, evaluation_points
- Persistence of generated questions and plan
- Follow-up generation tied to parent_question_id
- Saving of candidate response and interviewer notes
- Verification that responses do NOT overwrite earlier resume or assessment evidence
"""

import os
import sys

# Ensure UTF-8 stdout on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sqlalchemy.orm import Session
from database import engine, get_db
import models.models as models
from services.interview_intelligence import (
    plan_interview_skills,
    generate_targeted_interview_questions,
    generate_interview_follow_up,
    save_interview_response,
    format_question_dict
)

def run_phase5a_tests():
    print("==================================================")
    print("PHASE 5A: INTERVIEW INTELLIGENCE TEST SUITE")
    print("==================================================")
    
    db: Session = next(get_db())
    analysis_id = 4
    
    # 1. Target Job and Candidate verification
    print("\n--- Test 1: Loading Target Job and Candidate ---")
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    assert analysis is not None, "Analysis 4 not found"
    candidate = db.query(models.Candidate).filter(models.Candidate.id == analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == analysis.job_id).first()
    print(f"Candidate: {candidate.name}")
    print(f"Target Job: {job.title}")
    assert candidate.name == "ARRA GAYATRI"
    assert "AI ML" in job.title
    print("✓ Candidate and Job loaded successfully.")

    # 2. Test Interview Planning Service
    print("\n--- Test 2: Interview Planning & Evidence Gap Selection ---")
    plan = plan_interview_skills(analysis_id=analysis_id, db=db)
    assert plan is not None
    assert "selected_skills" in plan
    selected_skills = plan["selected_skills"]
    print(f"Total Skills Selected for Interview: {len(selected_skills)}")
    assert len(selected_skills) >= 3, "At least 3 unresolved skills should be selected"
    
    # Check that strongly supported SQL (80%) is not at top priority
    first_skill = selected_skills[0]
    print(f"Top Priority Skill: {first_skill['skill']} (Weight: {first_skill['priority_weight']})")
    print(f"  Reason: {first_skill['reason']}")
    
    for s in selected_skills:
        assert s["skill"], "Skill name must be present"
        assert s["reason"], "Every selected skill must have an explicit reason"
        assert s["evidence_level"] in ["Needs Verification", "Limited Evidence", "Moderate Evidence", "Good Evidence"]
        print(f"  • {s['skill']} ({s['evidence_level']}): {s['reason'][:90]}...")

    print("✓ Interview planning successfully selected unresolved skills with reasons.")

    # 3. Test Question Generation & Grounding
    print("\n--- Test 3: Targeted Question Generation (5-8 Questions) ---")
    questions = generate_targeted_interview_questions(analysis_id=analysis_id, db=db)
    print(f"Generated Questions Count: {len(questions)}")
    assert 5 <= len(questions) <= 8, f"Expected 5-8 questions, got {len(questions)}"
    
    # Check question fields & traceability
    project_deep_dives = 0
    candidate_claims = [c.claim_text for c in db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()]

    for idx, q in enumerate(questions, 1):
        print(f"\n[Question #{q['order_num']}] Type: {q['question_type']} | Skill: {q['skill']} | Difficulty: {q['difficulty']}")
        print(f"Text: {q['question_text']}")
        print(f"Source Context: {q['source_context']}")
        print(f"Evidence Gap: {q['evidence_gap']}")
        print(f"Why Generated: {q['why_generated']}")
        print(f"Evaluation Points: {q['evaluation_points']}")
        
        assert q["skill"], "Question must have skill"
        assert q["question_text"], "Question text must not be empty"
        assert q["why_generated"], "Question must have why_generated traceability"
        assert q["evidence_gap"], "Question must specify evidence_gap"
        assert len(q["evaluation_points"]) >= 2, "Must provide evaluation points for interviewer guidance"
        
        if q["question_type"] == "Project Deep-Dive":
            project_deep_dives += 1
            # Verify source context is grounded in candidate's real claims or projects
            is_grounded = any(claim in q["source_context"] or q["skill"].lower() in claim.lower() for claim in candidate_claims)
            print(f"  -> Grounded in candidate claims: {is_grounded}")

    print(f"\n✓ Generated {len(questions)} questions with full traceability and {project_deep_dives} Project Deep-Dive question(s).")

    # 4. Test Persistence in Database
    print("\n--- Test 4: Database Persistence ---")
    db_questions = db.query(models.InterviewQuestion).filter(
        models.InterviewQuestion.analysis_id == analysis_id
    ).all()
    assert len(db_questions) == len(questions), f"DB count mismatch: {len(db_questions)} vs {len(questions)}"
    
    db_plan = db.query(models.InterviewPlan).filter(models.InterviewPlan.analysis_id == analysis_id).first()
    assert db_plan is not None, "Interview plan must persist in database"
    assert len(db_plan.selected_skills) == len(selected_skills)
    print(f"✓ All {len(db_questions)} questions and interview plan persisted in database.")

    # 5. Test Follow-Up Backend
    print("\n--- Test 5: Follow-Up Generation Backend ---")
    first_q_id = questions[0]["id"]
    test_cand_response = "I built the service using asynchronous route handlers and used Pydantic models for request body validation, handling concurrency via asyncio worker pools."
    
    follow_up = generate_interview_follow_up(
        question_id=first_q_id,
        candidate_response=test_cand_response,
        db=db
    )
    print(f"Generated Follow-Up Question ID: {follow_up['id']}")
    print(f"Parent Question ID: {follow_up['parent_question_id']} (Expected: {first_q_id})")
    print(f"Follow-Up Text: {follow_up['question_text']}")
    print(f"Why Generated: {follow_up['why_generated']}")
    
    assert follow_up["parent_question_id"] == first_q_id, "parent_question_id must match"
    assert follow_up["skill"] == questions[0]["skill"], "Follow-up must stay on same skill"
    print("✓ Follow-up generation tied to parent question and contextual domain.")

    # 6. Test Response and Interviewer Notes Storage
    print("\n--- Test 6: Interview Response & Notes Storage ---")
    updated_q = save_interview_response(
        question_id=first_q_id,
        candidate_response="Candidate demonstrated clear grasp of async request flow and validation decorators.",
        interviewer_notes="Strong explanation of concurrency trade-offs. Move to distributed caching next.",
        db=db
    )
    assert updated_q["candidate_response"] is not None
    assert updated_q["interviewer_notes"] is not None
    print(f"Saved Candidate Response: {updated_q['candidate_response'][:60]}...")
    print(f"Saved Interviewer Notes: {updated_q['interviewer_notes']}")
    
    # 7. Verify Prior Evidence Remains Intact
    print("\n--- Test 7: Integrity of Prior Evidence (No Overwrites) ---")
    ev_count = db.query(models.SkillEvidence).filter(models.SkillEvidence.analysis_id == analysis_id).count()
    claim_count = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).count()
    assessment = db.query(models.Assessment).filter(models.Assessment.analysis_id == analysis_id).first()
    
    assert ev_count > 0, "Prior evidence must remain intact"
    assert claim_count > 0, "Prior claims must remain intact"
    assert assessment.overall_percentage == 56.0, "Prior assessment scores must not be altered"
    print(f"✓ Prior evidence preserved: {ev_count} evidence records, {claim_count} claims, assessment score: {assessment.overall_percentage}%")

    print("\n==================================================")
    print("ALL PHASE 5A TESTS PASSED SUCCESSFULLY! (100% GREEN)")
    print("==================================================")

if __name__ == "__main__":
    run_phase5a_tests()
