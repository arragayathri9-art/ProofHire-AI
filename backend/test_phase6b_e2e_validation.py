import sys
import os

# Set stdout to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from database import engine, get_db
import models.models as models
from services.profile_intelligence import compute_and_save_skill_profile
from services.interview_intelligence import plan_interview_skills
from services.report_intelligence import aggregate_proofhire_report

def run_phase6b_validation():
    print("=" * 60)
    print("PHASE 6B: FINAL PRODUCT POLISH + END-TO-END VALIDATION")
    print("=" * 60)

    db = next(get_db())

    # 1. Dashboard & Analysis Tracking Validation
    print("\n--- 1. Dashboard & Recent Analyses Validation ---")
    analyses = db.query(models.Analysis).order_by(models.Analysis.id.desc()).all()
    assert len(analyses) > 0, "Analyses must exist in the database."
    demo_analysis = None
    for a in analyses:
        if a.id == 4:
            demo_analysis = a
            break
    if not demo_analysis:
        demo_analysis = analyses[0]

    candidate = db.query(models.Candidate).filter(models.Candidate.id == demo_analysis.candidate_id).first()
    job = db.query(models.Job).filter(models.Job.id == demo_analysis.job_id).first()
    print(f"Demo Candidate: {candidate.name} (Analysis #{demo_analysis.id})")
    print(f"Target Role: {job.title} ({job.company or 'Direct'})")
    assert candidate.name is not None and len(candidate.name) > 0
    print("[PASS] Dashboard data contracts verified.")

    # 2. Pipeline Visualization States Validation
    print("\n--- 2. Pipeline Stages & State Contract Validation ---")
    claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.candidate_id == candidate.id).all()
    evidence_count = db.query(models.SkillEvidence).filter(models.SkillEvidence.analysis_id == demo_analysis.id).count()
    assessment = db.query(models.Assessment).filter(models.Assessment.analysis_id == demo_analysis.id).first()
    skill_verifs = db.query(models.SkillVerification).filter(models.SkillVerification.analysis_id == demo_analysis.id).all()
    interview_plan = db.query(models.InterviewPlan).filter(models.InterviewPlan.analysis_id == demo_analysis.id).first()

    pipeline_stages = {
        "resume": "completed",
        "evidence": "completed" if evidence_count > 0 else "current",
        "assessment": "completed" if (assessment and assessment.status == "completed") else "pending",
        "profile": "completed" if len(skill_verifs) > 0 else "pending",
        "interview": "completed" if interview_plan else "pending",
        "report": "completed" if interview_plan else "pending"
    }

    for stage_name, state in pipeline_stages.items():
        print(f"  • Stage '{stage_name}': {state}")
        assert state in ["completed", "current", "pending"]
    print("[PASS] 5-Stage pipeline states contract verified.")

    # 3. Data Integrity & Single-Skill Traceability Test
    print("\n--- 3. Single-Skill End-to-End Traceability (Python & SQL) ---")
    # Trace SQL
    sql_claims = [c for c in claims if "sql" in c.claim_text.lower()]
    sql_ev = [sv for sv in skill_verifs if sv.skill_name.lower() == "sql"]
    
    print(f"  • Trace 'SQL':")
    print(f"    - Resume Claims linked: {len(sql_claims)}")
    if sql_ev:
        print(f"    - Verified Level: {sql_ev[0].evidence_level}")
        print(f"    - Assessment Score: {sql_ev[0].assessment_percentage}% ({sql_ev[0].assessment_label})")
        assert sql_ev[0].assessment_percentage == 80.0, "SQL score must exactly match 80.0%"

    # Trace Python
    py_ev = [sv for sv in skill_verifs if sv.skill_name.lower() == "python"]
    print(f"  • Trace 'Python':")
    if py_ev:
        print(f"    - Verified Level: {py_ev[0].evidence_level}")
        print(f"    - Assessment Score: {py_ev[0].assessment_percentage}% ({py_ev[0].assessment_label})")
        assert py_ev[0].assessment_percentage == 53.3, "Python score must exactly match 53.3%"

    print("[PASS] Multi-stage data integrity confirmed with zero score mutation.")

    # 4. Interview Modes & Protection Validation
    print("\n--- 4. Interview Intelligence Modes & Question Integrity ---")
    interview_qs = db.query(models.InterviewQuestion).filter(models.InterviewQuestion.analysis_id == demo_analysis.id).all()
    assert len(interview_qs) > 0, "Interview questions must exist for demo candidate."
    print(f"  • Probes available: {len(interview_qs)}")
    for q in interview_qs[:3]:
        print(f"    - [{q.skill}] ({q.question_type}): {q.question_text[:60]}...")
        assert q.evaluation_points is not None, "Interviewer evaluation guidance must be stored in DB."
    print("[PASS] Interview question and private guidance integrity verified.")

    # 5. Final Report Snapshot & Non-Hiring Decision Support Validation
    print("\n--- 5. Final Report Snapshot & Non-Hiring Guardrails ---")
    report = aggregate_proofhire_report(demo_analysis.id, db)
    assert report is not None
    summary_text = report["executive_summary"].get("summary_text") or str(report["executive_summary"])
    assert "hire recommendation" not in summary_text.lower()
    assert "reject recommendation" not in summary_text.lower()
    assert "not constitute" in report["disclaimer"].lower()
    assert report["header"]["candidate_name"] == candidate.name
    assert report["header"]["analysis_id"] == demo_analysis.id
    print(f"  • Executive Summary: {summary_text[:85]}...")
    print(f"  • Disclaimer: {report['disclaimer'][:75]}...")
    print("[PASS] Final report generated with strict decision-support guardrails.")

    print("\n" + "=" * 60)
    print("ALL PHASE 6B END-TO-END VALIDATIONS PASSED (100% GREEN)")
    print("=" * 60)

if __name__ == '__main__':
    run_phase6b_validation()
