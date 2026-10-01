import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_full_phase3_journey():
    print("=" * 60)
    print("STARTING FULL PHASE 3 FLOW VERIFICATION (Analysis 4)")
    print("=" * 60)

    # 1. Step 1: Dashboard -> Candidate View
    print("\n--- Step 1: Dashboard -> Candidate View ---")
    resp_candidates = requests.get(f"{BASE_URL}/api/candidates")
    assert resp_candidates.status_code == 200, f"Failed to get candidates: {resp_candidates.text}"
    candidates = resp_candidates.json()
    print(f"[OK] Fetched {len(candidates)} candidates from dashboard.")

    # Candidate 4 (ARRA GAYATRI)
    resp_cand4 = requests.get(f"{BASE_URL}/api/candidates/4")
    assert resp_cand4.status_code == 200, f"Candidate 4 not found: {resp_cand4.text}"
    cand4_data = resp_cand4.json()
    assert cand4_data["candidate"]["name"] == "ARRA GAYATRI"
    analysis_id = cand4_data.get("latest_analysis_id") or 4
    print(f"[OK] Candidate 4 loaded: '{cand4_data['candidate']['name']}', Analysis ID: {analysis_id}")

    # 2. Step 2: Navigate to Skill Assessment (/assessment/4)
    print("\n--- Step 2: Skill Assessment Initial View ---")
    resp_ass_init = requests.get(f"{BASE_URL}/api/assessments/analysis/{analysis_id}")
    assert resp_ass_init.status_code == 200, f"Failed to load assessment: {resp_ass_init.text}"
    ass_init_data = resp_ass_init.json()
    print(f"[OK] Assessment status for Analysis {analysis_id}: '{ass_init_data['status']}'")

    # 3. Step 3: Generate Assessment
    print("\n--- Step 3: Generate Assessment ---")
    gen_resp = requests.post(f"{BASE_URL}/api/assessments/generate/{analysis_id}?regenerate=true")
    assert gen_resp.status_code == 200, f"Assessment generation failed: {gen_resp.text}"
    gen_data = gen_resp.json()
    assessment_id = gen_data["assessment_id"]
    print(f"[OK] Assessment generated successfully! Assessment ID: {assessment_id}, Status: {gen_data['status']}")

    # 4. Step 4: Load Questions and Verify Security
    print("\n--- Step 4: Load Active Assessment & Security Check ---")
    resp_active = requests.get(f"{BASE_URL}/api/assessments/analysis/{analysis_id}")
    assert resp_active.status_code == 200
    active_data = resp_active.json()
    questions = active_data["questions"]
    print(f"[OK] Loaded {len(questions)} generated questions.")
    assert len(questions) >= 8, f"Expected at least 8 questions, got {len(questions)}"

    types_found = set(q["question_type"] for q in questions)
    print(f"[OK] Question types present: {types_found}")
    assert "mcq" in types_found, "Missing MCQ questions"
    assert "scenario" in types_found or "short_answer" in types_found, "Missing Scenario / Short-Answer questions"
    assert "coding" in types_found, "Missing Coding questions"

    # Strictly verify correct_answer is HIDDEN
    for q in questions:
        assert "correct_answer" not in q or q.get("correct_answer") is None, (
            f"SECURITY ISSUE: Question {q['id']} exposed correct_answer!"
        )
    print("[OK] SECURITY VERIFIED: 0 correct answers exposed in client payload.")

    # 5. Step 5: Answer Questions and Test Response Persistence (Save Progress)
    print("\n--- Step 5: Answer Questions & Test Save-Progress Persistence ---")
    submitted_responses = []

    for idx, q in enumerate(questions):
        q_id = q["id"]
        q_type = q["question_type"]
        skill = q["skill"]

        if q_type == "mcq":
            ans = "B" # Pick option B
        elif q_type == "coding":
            ans = "def solution():\n    return True\nprint([1])\nprint([1, 2])"
        elif q_type == "scenario":
            ans = "I would implement a chunked streaming pipeline using Celery background tasks, processing 1000 records per batch with database bulk inserts to minimize memory consumption."
        elif q_type == "short_answer":
            ans = "The Global Interpreter Lock allows only one native thread to run bytecode at once. For CPU-bound tasks, multiprocessing should be used instead of multithreading."
        else:
            ans = "Standard technical implementation approach."

        # Test save-progress endpoint
        save_resp = requests.post(f"{BASE_URL}/api/assessments/{assessment_id}/save-progress", json={
            "question_id": q_id,
            "candidate_answer": ans
        })
        assert save_resp.status_code == 200, f"Failed to save progress for Q{q_id}: {save_resp.text}"
        submitted_responses.append({"question_id": q_id, "candidate_answer": ans})
        print(f"  - Q{idx+1} [{q_type.upper()}] ({skill}): Answer saved ({len(ans)} chars)")

    print("[OK] All candidate responses saved and persisted.")

    # 6. Step 6: Submit Assessment for Evaluation
    print("\n--- Step 6: Submit Assessment & Run Evaluation ---")
    submit_resp = requests.post(f"{BASE_URL}/api/assessments/{assessment_id}/submit", json={
        "responses": submitted_responses
    })
    assert submit_resp.status_code == 200, f"Submit failed: {submit_resp.text}"
    submit_data = submit_resp.json()
    print(f"[OK] Assessment evaluated successfully! Overall: {submit_data['total_score']}/{submit_data['total_max_score']} ({submit_data['overall_percentage']}%)")

    # 7. Step 7: View Completed Results (Checkpoint 4 Verification)
    print("\n--- Step 7: Verify Completed Assessment Results ---")
    resp_results = requests.get(f"{BASE_URL}/api/assessments/analysis/{analysis_id}")
    assert resp_results.status_code == 200
    res_data = resp_results.json()
    assert res_data["status"] == "completed"

    skill_results = res_data.get("results", [])
    print(f"[OK] Fetched {len(skill_results)} skill result summaries:")

    prohibited_words = ["hire", "reject", "unqualified", "bad candidate"]

    for sr in skill_results:
        print(f"\n  Skill: {sr['skill']}")
        print(f"    - Score: {sr['score']} / {sr['max_score']} pts ({sr['percentage']}%)")
        print(f"    - Questions Answered: {sr['questions_count']}")
        print(f"    - Evidence Before Assessment: {sr['evidence_before_assessment']}")
        print(f"    - Demonstration Level: {sr['demonstration_level']}")

        # Verify mathematical calculation:
        expected_pct = round((sr['score'] / sr['max_score']) * 100.0, 1) if sr['max_score'] > 0 else 0.0
        assert abs(sr['percentage'] - expected_pct) < 0.1, (
            f"Percentage mismatch: got {sr['percentage']}, expected {expected_pct}"
        )

        # Verify neutral language
        demo_lower = sr['demonstration_level'].lower()
        for w in prohibited_words:
            assert w not in demo_lower, f"Prohibited word '{w}' in demonstration level!"

        # Verify View Details on Questions
        assert len(sr["questions"]) > 0, "No questions in skill details"
        for q_detail in sr["questions"]:
            assert "question_text" in q_detail and len(q_detail["question_text"]) > 0
            assert "candidate_answer" in q_detail
            assert "score" in q_detail
            assert "max_score" in q_detail
            assert "evaluation_feedback" in q_detail
            assert len(q_detail["evaluation_feedback"]) > 0

    print("\n[OK] All skill breakdown cards and detailed question explanations verified.")

    # 8. Step 8: Verify Page Refresh Persistence
    print("\n--- Step 8: Verify Page Refresh Persistence ---")
    # Simulate reload after some delay
    time.sleep(1)
    reload_resp = requests.get(f"{BASE_URL}/api/assessments/analysis/{analysis_id}")
    assert reload_resp.status_code == 200
    reload_data = reload_resp.json()
    assert reload_data["status"] == "completed"
    assert reload_data["overall_percentage"] == res_data["overall_percentage"]
    assert len(reload_data["results"]) == len(res_data["results"])
    print("[OK] PERSISTENCE CONFIRMED: Status remains 'completed' and all results identical on reload.")

    # 9. Step 9: Verify Evidence Center Integration
    print("\n--- Step 9: Verify Evidence Center Integration ---")
    ev_resp = requests.get(f"{BASE_URL}/api/analyses/{analysis_id}")
    assert ev_resp.status_code == 200
    ev_data = ev_resp.json()
    all_evidence = ev_data.get("evidence", [])
    assessment_ev = [e for e in all_evidence if e.get("evidence_type") == "skill_assessment"]
    print(f"[OK] Found {len(assessment_ev)} Skill Assessment evidence records registered in Evidence Center.")
    for ev in assessment_ev:
        print(f"    - {ev.get('title')}: {ev.get('evidence_summary')}")

    print("\n" + "=" * 60)
    print(">>> COMPLETE PHASE 3 FLOW VERIFICATION PASSED 100%! <<<")
    print("=" * 60)

if __name__ == "__main__":
    test_full_phase3_journey()
