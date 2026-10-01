import os
import sys
import json
import requests

# Fix windows console unicode output
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("==================================================")
    print("RUNNING GITHUB EVIDENCE -> VERIFIED SKILL PROFILE TEST")
    print("==================================================")

    # 1. Fetch analysis 4 profile
    resp = requests.get(f"{BASE_URL}/api/skill-profile/4")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    profile = resp.json()

    candidate_name = profile.get("candidate_name")
    print(f"Candidate: {candidate_name}")
    print(f"Target Job: {profile.get('job_title')}")
    skills = profile.get("skills", [])
    assert len(skills) > 0, "No skills found in profile"

    # Find Python skill
    python_skill = next((s for s in skills if s["skill_name"].lower() == "python"), None)
    assert python_skill is not None, "Python skill not found in profile"

    # ------------------------------------------------------------------
    # Test 1: GitHub Evidence Mapping
    # Python files / signals from GitHub repository mapped to Python skill
    # ------------------------------------------------------------------
    has_github_mapped = (
        python_skill.get("github_evidence") == "Retrieved" and
        len(python_skill.get("github_signals", [])) > 0
    )
    sig_descriptions = [s.get("source", "") for s in python_skill.get("github_signals", [])]
    print(f"\n[Test 1] Python GitHub Signals: {sig_descriptions}")
    t1_pass = has_github_mapped and any("python" in d.lower() or "py" in d.lower() for d in sig_descriptions)

    # ------------------------------------------------------------------
    # Test 2: Skill Proof Sources
    # Non-fabricated proof sources checklist under skill
    # Example:
    # ✓ Resume claim
    # ✓ GitHub repository retrieved: psf/requests
    # ✓ Python files detected
    # ✓ Assessment score: ...
    # Evidence Strength: Strong
    # ------------------------------------------------------------------
    proof_sources = python_skill.get("proof_sources", [])
    print(f"\n[Test 2] Python Proof Sources ({len(proof_sources)}):")
    for ps in proof_sources:
        print(f"  {ps}")
    
    t2_pass = (
        len(proof_sources) >= 4 and
        any("resume claim" in ps.lower() for ps in proof_sources) and
        any("github repository" in ps.lower() for ps in proof_sources) and
        any("python" in ps.lower() or "file" in ps.lower() for ps in proof_sources) and
        any("evidence strength" in ps.lower() for ps in proof_sources)
    )

    # ------------------------------------------------------------------
    # Test 3: Assessment Integration
    # Assessment performance integrated into skill proof card & score
    # ------------------------------------------------------------------
    assessment_status = python_skill.get("assessment_status")
    assessment_pct = python_skill.get("assessment_percentage")
    print(f"\n[Test 3] Assessment Status: {assessment_status}, Percentage: {assessment_pct}")
    t3_pass = assessment_status in ["Passed", "Partial", "Needs Improvement", "Not Tested"]

    # ------------------------------------------------------------------
    # Test 4: Evidence Strength
    # Deterministic evidence strength assigned: Strong / Moderate / Limited / Unverified
    # ------------------------------------------------------------------
    strength = python_skill.get("evidence_strength")
    print(f"\n[Test 4] Evidence Strength: {strength}")
    t4_pass = strength in ["Strong", "Moderate", "Limited", "Unverified"]

    # ------------------------------------------------------------------
    # Test 5: Skill Proof Graph
    # Relationships:
    # Candidate -> Python -> Resume Claim, GitHub Repository (-> Signal), Skill Assessment (-> Score)
    # ------------------------------------------------------------------
    graph_data = python_skill.get("graph_data", {})
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    node_types = {n.get("type") for n in nodes}
    print(f"\n[Test 5] Skill Proof Graph Node Types: {node_types}")
    print(f"Total Nodes: {len(nodes)}, Total Edges: {len(edges)}")
    for n in nodes:
        print(f"  Node: id={n.get('id')}, type={n.get('type')}, label={n.get('label')}")

    has_candidate_node = any(n.get("type") == "Candidate" for n in nodes)
    has_skill_node = any(n.get("type") == "Skill" for n in nodes)
    has_claim_node = any(n.get("type") == "Resume Claim" for n in nodes)
    has_github_node = any(n.get("type") == "GitHub Repository" for n in nodes)
    has_signal_node = any(n.get("type") == "GitHub Signal" for n in nodes)
    has_assess_node = any(n.get("type") == "Skill Assessment" for n in nodes)

    t5_pass = (
        has_candidate_node and 
        has_skill_node and 
        has_claim_node and 
        has_github_node and 
        has_signal_node and 
        has_assess_node
    )

    # ------------------------------------------------------------------
    # Test 6: Explainability
    # "Why this skill rating?" narrative grounded in factual sources
    # ------------------------------------------------------------------
    explanation = python_skill.get("explanation", "")
    print(f"\n[Test 6] Explanation: {explanation}")
    t6_pass = (
        len(explanation) > 30 and
        "python" in explanation.lower() and
        ("github" in explanation.lower() or "repository" in explanation.lower())
    )

    # ------------------------------------------------------------------
    # Test 7: False Verification Protection
    # If a candidate claims a skill but has NO GitHub evidence AND assessment is weak/not tested:
    # MUST show "Needs Verification" / "Unverified"
    # ------------------------------------------------------------------
    unverified_skills = [
        s for s in skills 
        if s.get("github_evidence") == "None" and 
           (s.get("assessment_status") in ["Not Tested", "Needs Improvement"] or s.get("assessment_percentage") is None or s.get("assessment_percentage") < 50.0)
    ]
    print(f"\n[Test 7] Skills with no GitHub and weak/not-tested assessment ({len(unverified_skills)}):")
    false_verification_detected = False
    for uv in unverified_skills:
        print(f"  - {uv['skill_name']}: Strength={uv.get('evidence_strength')}, Level={uv.get('evidence_level')}")
        if uv.get("evidence_strength") in ["Strong", "Moderate"] or uv.get("evidence_level") in ["Strong Evidence", "Moderate Evidence", "Good Evidence"]:
            false_verification_detected = True
            print(f"    FAIL: {uv['skill_name']} was falsely verified without GitHub or strong assessment!")

    t7_pass = not false_verification_detected and len(unverified_skills) > 0

    print("\n==================================================")
    print("GITHUB -> SKILL PROFILE TEST")
    print(f"GitHub Evidence Mapping: {'PASS' if t1_pass else 'FAIL'}")
    print(f"Skill Proof Sources: {'PASS' if t2_pass else 'FAIL'}")
    print(f"Assessment Integration: {'PASS' if t3_pass else 'FAIL'}")
    print(f"Evidence Strength: {'PASS' if t4_pass else 'FAIL'}")
    print(f"Skill Proof Graph: {'PASS' if t5_pass else 'FAIL'}")
    print(f"Explainability: {'PASS' if t6_pass else 'FAIL'}")
    print(f"False Verification Protection: {'PASS' if t7_pass else 'FAIL'}")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
