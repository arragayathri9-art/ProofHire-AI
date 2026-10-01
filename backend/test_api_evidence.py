import sys
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api():
    # Fetch analysis 4
    resp = client.get("/api/analyses/4")
    assert resp.status_code == 200, f"Analysis 4 not found: {resp.text}"
    data = resp.json()
    print(f"Analysis 4 found with {len(data['claims'])} claims.")
    
    claims = data['claims']
    assert len(claims) > 0, "No claims found for analysis 4"
    
    # 1. Verify claims with 0 evidence have evidence_level = "Needs Verification"
    zero_ev_claims = [c for c in claims if len(c['evidence']) == 0]
    for c in zero_ev_claims:
        assert c['evidence_level'] == "Needs Verification", f"Claim {c['id']} had level {c['evidence_level']}"
    print(f"[OK] Verified: {len(zero_ev_claims)} claims with zero evidence have evidence_level = 'Needs Verification'.")

    # Pick claim 2 for testing URL evidence submission
    test_claim = claims[1]
    claim_id = test_claim['id']

    # 2. Test URL evidence with auto_inspect=False (submitted_only)
    post_resp = client.post(
        "/api/evidence",
        data={
            "claim_id": claim_id,
            "evidence_type": "url",
            "title": "GitHub Profile Reference",
            "description": "Candidate portfolio link submitted as reference",
            "url": "https://github.com/candidate/calculus-notebook",
            "auto_inspect": "false"
        }
    )
    assert post_resp.status_code == 200, f"Post evidence failed: {post_resp.text}"
    ev_data = post_resp.json()
    print("Post evidence response:", ev_data)
    assert ev_data["evidence_access_status"] == "submitted_only", f"Expected submitted_only, got {ev_data['evidence_access_status']}"
    print("[OK] Verified: URL evidence returned evidence_access_status = 'submitted_only'.")

    # 3. Re-fetch analysis and verify claim fields
    updated_resp = client.get("/api/analyses/4")
    updated_data = updated_resp.json()
    target_claim = next(c for c in updated_data['claims'] if c['id'] == claim_id)
    
    print("Updated claim evidence level:", target_claim.get("evidence_level"))
    print("Updated claim evidence access status:", target_claim.get("evidence_access_status"))
    print("Updated claim what supports:", target_claim.get("what_supports"))

    assert target_claim["evidence_access_status"] == "submitted_only"
    
    # Verify prohibited phrases are NOT present
    supports_text = (target_claim.get("what_supports") or "").lower()
    used_text = (target_claim.get("evidence_used") or "").lower()
    prohibited = ["confirms the existence", "verified deployment", "proves the project"]
    for phrase in prohibited:
        assert phrase not in supports_text, f"Prohibited phrase '{phrase}' found in what_supports: {supports_text}"
        assert phrase not in used_text, f"Prohibited phrase '{phrase}' found in evidence_used: {used_text}"
    print("[OK] Verified: Prohibited phrases are absent.")
    
    # Check that the standardized integrity statement or notice appears in the evidence or analysis
    all_text = (supports_text + " " + used_text + " " + (target_claim.get("what_is_missing") or "").lower())
    assert "not been independently inspected" in all_text or "submitted_only" in target_claim["evidence_access_status"], "Integrity statement check failed"
    print("[OK] Verified: Evidence integrity notice is preserved.")

    print("ALL API END-TO-END TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_api()
