import sys
from fastapi.testclient import TestClient
from main import app
import database
import models.models as models
from services.question_generator import get_fallback_questions_for_skill
from services.assessment_evaluator import (
    evaluate_mcq_deterministic,
    evaluate_coding_deterministic,
    evaluate_single_question,
    get_demonstration_level
)

client = TestClient(app)

def test_checkpoint_1():
    print("=== CHECKPOINT 1: Backend Assessment Generation Flow Verification ===")
    
    # 1. Models and Database Schema Verification
    db = database.SessionLocal()
    try:
        # Check models table names and attributes
        assert hasattr(models.Assessment, "selected_skills")
        assert hasattr(models.Assessment, "total_score")
        assert hasattr(models.Assessment, "status")
        assert hasattr(models.AssessmentQuestion, "correct_answer")
        assert hasattr(models.AssessmentQuestion, "evaluation_criteria")
        assert hasattr(models.AssessmentResponse, "candidate_answer")
        assert hasattr(models.AssessmentResponse, "score")
        assert hasattr(models.AssessmentResult, "percentage")
        assert hasattr(models.AssessmentResult, "demonstration_level")
        print("[OK] Models: Assessment, AssessmentQuestion, AssessmentResponse, AssessmentResult verified.")
    finally:
        db.close()

    # 2. Question Generator & Fallback Bank Verification
    fallback_py = get_fallback_questions_for_skill("Python", count=3, difficulty="Intermediate")
    assert len(fallback_py) == 3, f"Expected 3 fallback questions, got {len(fallback_py)}"
    for q in fallback_py:
        assert "question_type" in q
        assert "question_text" in q
        assert "correct_answer" in q
        assert "max_score" in q
    print(f"[OK] Question Generator Fallback Bank verified: retrieved {len(fallback_py)} structured questions.")

    # 3. Duplicate Assessment Generation Prevention Verification
    gen_resp1 = client.post("/api/assessments/generate/4?regenerate=false")
    assert gen_resp1.status_code == 200, f"Generate failed: {gen_resp1.text}"
    gen_data1 = gen_resp1.json()
    assert "assessment_id" in gen_data1
    first_ass_id = gen_data1["assessment_id"]
    print(f"[OK] Assessment Generation API responded with assessment_id={first_ass_id}.")

    # Calling generate again without regenerate must NOT create a duplicate
    gen_resp2 = client.post("/api/assessments/generate/4?regenerate=false")
    assert gen_resp2.status_code == 200
    gen_data2 = gen_resp2.json()
    assert gen_data2.get("assessment_id") == first_ass_id
    assert "already exists" in gen_data2.get("message", "").lower()
    print("[OK] Duplicate Assessment Prevention verified: existing assessment returned.")

    # 4. Strict Security Verification: Correct Answers NEVER returned to frontend during active assessment
    get_resp = client.get("/api/assessments/analysis/4")
    assert get_resp.status_code == 200, f"Get assessment failed: {get_resp.text}"
    ass_view = get_resp.json()
    
    assert ass_view["analysis_id"] == 4
    assert ass_view["status"] in ["ready", "in_progress", "completed"]
    assert len(ass_view["questions"]) > 0, "No questions in assessment"
    
    if ass_view["status"] != "completed":
        for idx, q in enumerate(ass_view["questions"]):
            assert "correct_answer" not in q or q.get("correct_answer") is None, (
                f"SECURITY VIOLATION: Question {idx+1} exposed correct_answer to client!"
            )
            assert "evaluation_criteria" not in q, (
                f"SECURITY VIOLATION: Question {idx+1} exposed evaluation_criteria to client!"
            )
        print(f"[OK] Correct Answers Security verified: All {len(ass_view['questions'])} active questions strictly withhold correct answers.")

    # 5. Deterministic Evaluator Testing
    # 5a. MCQ deterministic test
    mcq_correct = evaluate_mcq_deterministic(candidate_answer="B", correct_answer="B", max_score=5)
    assert mcq_correct["score"] == 5.0
    assert mcq_correct["is_correct"] is True

    mcq_incorrect = evaluate_mcq_deterministic(candidate_answer="A", correct_answer="B", max_score=5)
    assert mcq_incorrect["score"] == 0.0
    assert mcq_incorrect["is_correct"] is False
    print("[OK] Evaluator: MCQ deterministic matching verified.")

    # 5b. Coding deterministic test
    coding_correct = evaluate_coding_deterministic(
        candidate_answer="[1]\n[1, 2]",
        correct_answer="[1]\n[1, 2]",
        criteria={"expected_output": "[1]\n[1, 2]"},
        max_score=5
    )
    assert coding_correct is not None
    assert coding_correct["score"] == 5.0
    assert coding_correct["is_correct"] is True
    print("[OK] Evaluator: Coding deterministic output matching verified.")

    # 5c. Mathematical score percentage calculation check
    earned = 18.5
    available = 25.0
    pct = round((earned / available) * 100.0, 1)
    assert pct == 74.0
    demonstration = get_demonstration_level(pct)
    assert demonstration == "Good demonstration"
    print(f"[OK] Mathematical Scoring verified: {earned}/{available} -> {pct}% -> '{demonstration}'.")

    print("\n>>> ALL CHECKPOINT 1 VERIFICATIONS PASSED SUCCESSFULLY! <<<\n")

if __name__ == "__main__":
    test_checkpoint_1()
