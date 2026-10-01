from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON, Float
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # JSON extracted fields
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    minimum_experience = Column(String, nullable=True)
    education_requirements = Column(String, nullable=True)
    
    analyses = relationship("Analysis", back_populates="job")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    professional_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # JSON arrays for complex objects
    experience = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    education = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    links = Column(JSON, default=list)
    
    resumes = relationship("Resume", back_populates="candidate")
    analyses = relationship("Analysis", back_populates="candidate")
    skills = relationship("CandidateSkill", back_populates="candidate")
    claims = relationship("CandidateClaim", back_populates="candidate")
    assessments = relationship("Assessment", back_populates="candidate")
    skill_verifications = relationship("SkillVerification", back_populates="candidate", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    filename = Column(String)
    file_path = Column(String)
    raw_text = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    candidate = relationship("Candidate", back_populates="resumes")

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    skill_name = Column(String, index=True)
    
    candidate = relationship("Candidate", back_populates="skills")
    claims = relationship("CandidateClaim", back_populates="skill")

class CandidateClaim(Base):
    __tablename__ = "candidate_claims"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    skill_id = Column(Integer, ForeignKey("candidate_skills.id"), nullable=True)
    claim_text = Column(Text)
    claim_type = Column(String) # e.g., "skill_experience", "project_achievement"
    source_section = Column(String)
    verification_status = Column(String, default="not_verified")
    
    # Phase 2 Verification fields
    evidence_level = Column(String, nullable=True)
    evidence_access_status = Column(String, nullable=True) # submitted_only, retrieved, retrieval_failed
    evidence_used = Column(Text, nullable=True)
    what_supports = Column(Text, nullable=True)
    what_is_missing = Column(Text, nullable=True)
    next_step = Column(Text, nullable=True)
    
    candidate = relationship("Candidate", back_populates="claims")
    skill = relationship("CandidateSkill", back_populates="claims")

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Comparison results (JSON)
    skills_present = Column(JSON, default=list)
    potential_skill_gaps = Column(JSON, default=list)
    skills_requiring_verification = Column(JSON, default=list)
    
    candidate = relationship("Candidate", back_populates="analyses")
    job = relationship("Job", back_populates="analyses")
    assessments = relationship("Assessment", back_populates="analysis")
    skill_verifications = relationship("SkillVerification", back_populates="analysis", cascade="all, delete-orphan")
    interview_questions = relationship("InterviewQuestion", back_populates="analysis", cascade="all, delete-orphan", order_by="InterviewQuestion.order_num")
    interview_plan = relationship("InterviewPlan", back_populates="analysis", uselist=False, cascade="all, delete-orphan")

# --- PREPARATION FOR PHASE 2/3 ---

class SkillEvidence(Base):
    __tablename__ = "skill_evidence"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True)
    claim_id = Column(Integer, ForeignKey("candidate_claims.id"), nullable=True)
    evidence_type = Column(String)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Evidence Agent outputs
    analysis_status = Column(String, default="pending")
    evidence_access_status = Column(String, nullable=True) # submitted_only, retrieved, retrieval_failed
    evidence_summary = Column(Text, nullable=True)
    supported_skills = Column(JSON, default=list)
    
    # GitHub Repository Intelligence fields
    repository_owner = Column(String, nullable=True)
    repository_name = Column(String, nullable=True)
    repository_url = Column(String, nullable=True)
    primary_language = Column(String, nullable=True)
    languages = Column(JSON, default=dict, nullable=True)
    topics = Column(JSON, default=list, nullable=True)
    readme_summary = Column(Text, nullable=True)
    repository_structure = Column(JSON, default=list, nullable=True)
    retrieved_at = Column(DateTime, nullable=True)
    github_access_status = Column(String, nullable=True) # retrieved, submitted_only, retrieval_failed
    skill_signals = Column(JSON, default=list, nullable=True)
    
    # Certificate & Credential Intelligence fields (Phase 7A)
    certificate_name = Column(String, nullable=True)
    issuer = Column(String, nullable=True)
    certificate_candidate_name = Column(String, nullable=True)
    issue_date = Column(String, nullable=True)
    expiry_date = Column(String, nullable=True)
    credential_id = Column(String, nullable=True)
    credential_url = Column(String, nullable=True)
    document_extraction_status = Column(String, nullable=True) # EXTRACTED, PARTIAL, FAILED
    verification_status = Column(String, nullable=True) # DOCUMENT EXTRACTED, CREDENTIAL URL VERIFIED, SUBMITTED ONLY, VERIFICATION UNAVAILABLE, VERIFICATION FAILED
    certificate_metadata = Column(JSON, default=dict, nullable=True)
    
class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True)
    status = Column(String, default="ready") # not_generated, ready, in_progress, completed
    selected_skills = Column(JSON, default=list) # [{skill, priority, rationale, evidence_level_before, question_count}]
    total_score = Column(Float, nullable=True)
    total_max_score = Column(Float, nullable=True)
    overall_percentage = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    candidate = relationship("Candidate", back_populates="assessments")
    analysis = relationship("Analysis", back_populates="assessments")
    questions = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan", order_by="AssessmentQuestion.order_num")
    responses = relationship("AssessmentResponse", back_populates="assessment", cascade="all, delete-orphan")
    results = relationship("AssessmentResult", back_populates="assessment", cascade="all, delete-orphan")

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), index=True)
    order_num = Column(Integer, default=1)
    skill = Column(String, index=True)
    question_type = Column(String) # mcq, scenario, short_answer, coding
    difficulty = Column(String) # Basic, Intermediate, Advanced
    question_text = Column(Text)
    options = Column(JSON, default=list) # For MCQ: ["A) ...", "B) ...", "C) ...", "D) ..."]
    correct_answer = Column(Text) # Deterministic correct option or reference code/answer (NEVER sent to client before submission)
    evaluation_criteria = Column(JSON, default=dict) # Rubrics, expected output, test cases
    max_score = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    assessment = relationship("Assessment", back_populates="questions")
    response = relationship("AssessmentResponse", back_populates="question", uselist=False, cascade="all, delete-orphan")

class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), index=True)
    question_id = Column(Integer, ForeignKey("assessment_questions.id"), index=True)
    candidate_answer = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    evaluation_feedback = Column(Text, nullable=True)
    rubric_breakdown = Column(JSON, nullable=True) # {"correctness": 2, "relevance": 1, ...}
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    assessment = relationship("Assessment", back_populates="responses")
    question = relationship("AssessmentQuestion", back_populates="response")

class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), index=True)
    skill = Column(String, index=True)
    score = Column(Float)
    max_score = Column(Float)
    percentage = Column(Float)
    questions_count = Column(Integer)
    demonstration_level = Column(String) # "Strong demonstration in this assessment", "Good demonstration", etc.
    evidence_before_assessment = Column(String, nullable=True) # "Moderate Evidence", "Needs Verification", etc.
    feedback_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    assessment = relationship("Assessment", back_populates="results")
    
class SkillVerification(Base):
    __tablename__ = "skill_verifications"
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True)
    skill_name = Column(String, index=True)
    resume_claim_present = Column(Boolean, default=False)
    claims_count = Column(Integer, default=0)
    evidence_count = Column(Integer, default=0)
    retrieved_evidence_count = Column(Integer, default=0)
    assessment_percentage = Column(Float, nullable=True)
    assessment_label = Column(String, nullable=True) # Strong Demonstration, Good Demonstration, Partial Demonstration, Limited Demonstration, Not Demonstrated in This Assessment, Not Assessed
    evidence_level = Column(String, default="Needs Verification") # Strong Evidence, Good Evidence, Moderate Evidence, Limited Evidence, Needs Verification
    evidence_strength = Column(String, default="Unverified", nullable=True) # Strong, Moderate, Limited, Unverified
    claim_status = Column(String, default="Not Claimed", nullable=True) # Claimed, Not Claimed
    github_evidence = Column(String, default="None", nullable=True) # Retrieved, None
    assessment_status = Column(String, default="Not Tested", nullable=True) # Passed, Partial, Needs Improvement, Not Tested
    proof_sources = Column(JSON, default=list, nullable=True)
    job_group = Column(String, default="Needs Further Verification") # Well Supported, Partially Supported, Needs Further Verification, Not Demonstrated Yet
    explanation = Column(Text, nullable=True)
    next_verification_step = Column(Text, nullable=True)
    sources_breakdown = Column(JSON, default=dict)
    graph_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    analysis = relationship("Analysis", back_populates="skill_verifications")
    candidate = relationship("Candidate", back_populates="skill_verifications")
    
class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), index=True)
    order_num = Column(Integer, default=1)
    skill = Column(String, index=True)
    question_type = Column(String) # Technical, Scenario, Project Deep-Dive, Debugging / Problem Solving, Evidence Clarification
    difficulty = Column(String, default="Intermediate") # Basic, Intermediate, Advanced
    question_text = Column(Text)
    source_context = Column(Text, nullable=True) # Resume claim or project quote or assessment demonstration
    evidence_gap = Column(String, nullable=True) # e.g. "Needs Verification", "Limited Evidence", "Partial Demonstration (53.3%)"
    why_generated = Column(Text, nullable=True) # Explainable reason for this interview question
    evaluation_points = Column(JSON, default=list) # List of guidance criteria for interviewer
    parent_question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=True)
    candidate_response = Column(Text, nullable=True)
    interviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    analysis = relationship("Analysis", back_populates="interview_questions")
    parent = relationship("InterviewQuestion", remote_side=[id], backref="follow_ups")

class InterviewPlan(Base):
    __tablename__ = "interview_plans"
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), index=True)
    planning_summary = Column(Text, nullable=True)
    selected_skills = Column(JSON, default=list) # [{skill, reason, priority, evidence_level, assessment_pct, assessment_label}]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    analysis = relationship("Analysis", back_populates="interview_plan")

