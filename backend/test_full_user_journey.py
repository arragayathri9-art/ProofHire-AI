import requests
import time
import os

BASE_BACKEND = "http://127.0.0.1:8000"
BASE_FRONTEND = "http://localhost:5173"

def run_tests():
    print("=" * 60)
    print("STARTING COMPLETE USER JOURNEY VERIFICATION")
    print("=" * 60)

    # Step 1: Verify Main Frontend Application is reachable at single link
    print("\n[Step 1] Checking Single Main Application Link: http://localhost:5173/")
    r_front = requests.get(BASE_FRONTEND, timeout=5)
    assert r_front.status_code == 200, f"Frontend returned {r_front.status_code}"
    assert "ProofHire" in r_front.text or "vite" in r_front.text or "root" in r_front.text
    print("[OK] Main application entry point http://localhost:5173/ is online and serving 200 OK.")

    # Step 2: Dashboard Data Loading
    print("\n[Step 2] Dashboard Data Loading from Backend API")
    r_analyses = requests.get(f"{BASE_BACKEND}/api/analyses", timeout=5)
    assert r_analyses.status_code == 200, f"GET /api/analyses failed: {r_analyses.text}"
    analyses = r_analyses.json()
    print(f"[OK] Dashboard successfully loads {len(analyses)} existing candidate analyses.")
    
    r_candidates = requests.get(f"{BASE_BACKEND}/api/candidates", timeout=5)
    assert r_candidates.status_code == 200
    candidates = r_candidates.json()
    print(f"[OK] Dashboard metrics: {len(candidates)} candidates, {len(analyses)} analyses.")

    # Step 3: Candidate Detail Endpoint
    print("\n[Step 3] Candidate Detail Route Data (/candidates/{id})")
    target_candidate_id = candidates[0]["id"]
    r_cand_detail = requests.get(f"{BASE_BACKEND}/api/candidates/{target_candidate_id}", timeout=5)
    assert r_cand_detail.status_code == 200
    cand_data = r_cand_detail.json()
    assert "candidate" in cand_data and "skills" in cand_data and "claims" in cand_data
    print(f"[OK] Candidate profile #{target_candidate_id} ({cand_data['candidate']['name']}) loaded with {len(cand_data['skills'])} skills and {len(cand_data['claims'])} claims.")

    # Step 4: Resume Upload + New Analysis Journey
    print("\n[Step 4] User Journey: Start New Analysis -> Upload Resume -> Analyze")
    dummy_pdf_path = os.path.join(os.path.dirname(__file__), "dummy_resume.pdf")
    assert os.path.exists(dummy_pdf_path), "dummy_resume.pdf must exist"

    # Create job
    r_job = requests.post(
        f"{BASE_BACKEND}/api/jobs",
        json={
            "title": "Lead AI Architect",
            "company": "Cognitive Scale Inc.",
            "description": "Seeking a Lead AI Architect with deep Python, LangChain, FastAPI, and LLM verification expertise."
        },
        timeout=60
    )
    assert r_job.status_code == 200
    job_id = r_job.json()["id"]
    print(f"[OK] Target Job created: ID #{job_id}")

    # Analyze candidate
    print("Sending candidate resume for AI analysis...")
    with open(dummy_pdf_path, "rb") as f:
        r_analyze = requests.post(
            f"{BASE_BACKEND}/api/candidates/analyze",
            data={"job_id": job_id},
            files={"file": ("dummy_resume.pdf", f, "application/pdf")},
            timeout=45
        )
    assert r_analyze.status_code == 200, f"Analysis failed: {r_analyze.text}"
    new_analysis_id = r_analyze.json()["analysis_id"]
    print(f"[OK] Analysis created successfully: Analysis ID #{new_analysis_id}")

    # Step 5: Preliminary Analysis
    print(f"\n[Step 5] User Journey: Preliminary Analysis (/analysis/result/{new_analysis_id})")
    r_result = requests.get(f"{BASE_BACKEND}/api/analyses/{new_analysis_id}", timeout=10)
    assert r_result.status_code == 200
    result_data = r_result.json()
    claims = result_data["claims"]
    print(f"[OK] Preliminary analysis loaded: {len(claims)} extracted claims.")
    for c in claims:
        assert c["evidence_level"] == "Needs Verification", f"Initial claim must be Needs Verification, got {c['evidence_level']}"
    print("[OK] All initial claims without evidence correctly verified as 'Needs Verification'.")

    # Step 6: Evidence Verification Center
    print(f"\n[Step 6] User Journey: Continue to Evidence Verification (/evidence/{new_analysis_id})")
    if len(claims) > 0:
        first_claim_id = claims[0]["id"]
        print(f"Submitting URL evidence with automated inspection for claim #{first_claim_id}...")
        r_ev = requests.post(
            f"{BASE_BACKEND}/api/evidence",
            data={
                "claim_id": first_claim_id,
                "evidence_type": "url",
                "title": "GitHub Proof Project",
                "description": "Production repo link demonstrating AI microservice",
                "url": "https://httpbin.org/html",
                "auto_inspect": "true"
            },
            timeout=60
        )
        assert r_ev.status_code == 200
        ev_res = r_ev.json()
        print(f"[OK] Evidence processed: status = '{ev_res['evidence_access_status']}', level = '{ev_res['evidence_level']}'")

    # Step 7: Re-open from Dashboard / Evidence Center
    print(f"\n[Step 7] User Journey: Reopen candidate from Dashboard / Recent Analyses")
    r_reopen = requests.get(f"{BASE_BACKEND}/api/analyses/{new_analysis_id}", timeout=10)
    assert r_reopen.status_code == 200
    reopen_data = r_reopen.json()
    assert reopen_data["candidate"]["name"] is not None
    assert len(reopen_data["claims"]) > 0
    print(f"[OK] Session data intact for {reopen_data['candidate']['name']}: {len(reopen_data['claims'])} claims preserved.")

    print("\n" + "=" * 60)
    print("ALL USER JOURNEY INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
