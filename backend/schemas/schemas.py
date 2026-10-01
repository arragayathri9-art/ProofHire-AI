from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

# --- Gemini Extraction Schemas ---

class ExtractedExperience(BaseModel):
    company: str
    role: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration_if_available: Optional[str]
    description: str
    technologies_if_available: List[str]

class ExtractedProject(BaseModel):
    project_name: str
    description: str
    technologies: List[str]
    project_link_if_available: Optional[str]

class ExtractedEducation(BaseModel):
    institution: str
    degree: str
    field: Optional[str]
    start_date_if_available: Optional[str]
    end_date_if_available: Optional[str]

class ExtractedCertification(BaseModel):
    name: str
    issuer: str
    date_if_available: Optional[str]
    credential_link_if_available: Optional[str]

class ExtractedClaim(BaseModel):
    claim: str
    claim_type: str
    related_skills: List[str]
    source_section: str
    verification_status: str

class GeminiResumeExtraction(BaseModel):
    candidate_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    professional_summary: Optional[str]
    education: List[ExtractedEducation]
    skills: List[str]
    experience: List[ExtractedExperience]
    projects: List[ExtractedProject]
    certifications: List[ExtractedCertification]
    links: List[str]
    claimed_skills: List[str]
    professional_claims: List[ExtractedClaim]

class GeminiJobExtraction(BaseModel):
    job_title: str
    required_skills: List[str]
    preferred_skills: List[str]
    minimum_experience: Optional[str]
    education_requirements: Optional[str]
    responsibilities: List[str]
    technical_requirements: List[str]
    other_requirements: List[str]

class GeminiEvidenceAnalysis(BaseModel):
    information_contained: str
    supported_skills: List[str]
    relation_to_claim: str
    is_relevant: bool
    missing_information: str

class GeminiVerificationAssessment(BaseModel):
    evidence_level: str
    evidence_used: str
    what_supports: str
    what_is_missing: str
    next_step: str

# --- API Response/Request Schemas ---

class JobBase(BaseModel):
    title: str
    company: Optional[str] = None
    description: str

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    created_at: datetime
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    minimum_experience: Optional[str] = None
    education_requirements: Optional[str] = None
    
    class Config:
        orm_mode = True
        from_attributes = True

class CandidateBase(BaseModel):
    name: str
    email: Optional[str] = None

class CandidateResponse(CandidateBase):
    id: int
    phone: Optional[str] = None
    location: Optional[str] = None
    professional_summary: Optional[str] = None
    created_at: datetime
    experience: List[dict] = []
    projects: List[dict] = []
    education: List[dict] = []
    certifications: List[dict] = []
    
    class Config:
        orm_mode = True
        from_attributes = True

class AnalysisResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    created_at: datetime
    skills_present: List[str]
    potential_skill_gaps: List[str]
    skills_requiring_verification: List[str]
    
    class Config:
        orm_mode = True
        from_attributes = True

class EvidenceCreate(BaseModel):
    claim_id: int
    evidence_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

class EvidenceResponse(BaseModel):
    id: int
    candidate_id: Optional[int]
    analysis_id: Optional[int]
    claim_id: int
    evidence_type: str
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    file_path: Optional[str]
    extracted_text: Optional[str]
    created_at: datetime
    analysis_status: str
    evidence_access_status: Optional[str] = None
    evidence_summary: Optional[str]
    supported_skills: List[str] = []
    repository_owner: Optional[str] = None
    repository_name: Optional[str] = None
    repository_url: Optional[str] = None
    primary_language: Optional[str] = None
    languages: Optional[Dict[str, Any]] = None
    topics: Optional[List[str]] = None
    readme_summary: Optional[str] = None
    repository_structure: Optional[List[str]] = None
    retrieved_at: Optional[datetime] = None
    github_access_status: Optional[str] = None
    skill_signals: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True

class ClaimResponse(BaseModel):
    id: int
    candidate_id: int
    skill_id: Optional[int]
    claim_text: str
    claim_type: str
    source_section: str
    verification_status: str
    evidence_level: Optional[str]
    evidence_access_status: Optional[str] = None
    evidence_used: Optional[str]
    what_supports: Optional[str]
    what_is_missing: Optional[str]
    next_step: Optional[str]
    evidence: List[EvidenceResponse] = []

    class Config:
        from_attributes = True

class AnalysisResultResponse(BaseModel):
    analysis: AnalysisResponse
    candidate: CandidateResponse
    job: JobResponse
    claims: List[ClaimResponse] = []
    candidate_skills: List[str] = []

# --- Phase 3 Assessment Schemas ---

class SelectedSkillPlan(BaseModel):
    skill: str
    priority: str = "High" # High, Moderate
    evidence_level_before: str = "Needs Verification"
    recommended_difficulty: str = "Intermediate" # Basic, Intermediate, Advanced
    question_count: int = 3
    rationale: str

class AssessmentPlanOutput(BaseModel):
    selected_skills: List[SelectedSkillPlan]
    planning_summary: str = ""

class GeneratedQuestionSchema(BaseModel):
    skill: str
    question_type: str # mcq, scenario, short_answer, coding
    difficulty: str # Basic, Intermediate, Advanced
    question_text: str
    options: List[str] = [] # 4 options for MCQ, empty otherwise
    correct_answer: str # Deterministic answer or solution explanation
    evaluation_criteria: Dict[str, Any] = {} # e.g. rubric or expected output
    max_score: int = 5

class AssessmentQuestionPublic(BaseModel):
    id: int
    assessment_id: int
    order_num: int
    skill: str
    question_type: str
    difficulty: str
    question_text: str
    options: List[str] = []
    max_score: int
    candidate_answer: Optional[str] = None
    
    class Config:
        from_attributes = True

class AssessmentQuestionDetail(BaseModel):
    id: int
    assessment_id: int
    order_num: int
    skill: str
    question_type: str
    difficulty: str
    question_text: str
    options: List[str] = []
    correct_answer: Optional[str] = None
    candidate_answer: Optional[str] = None
    score: Optional[float] = None
    max_score: int
    is_correct: Optional[bool] = None
    evaluation_feedback: Optional[str] = None
    rubric_breakdown: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AssessmentResponseSave(BaseModel):
    question_id: int
    candidate_answer: str

class AssessmentSubmitPayload(BaseModel):
    responses: List[AssessmentResponseSave]

class AssessmentSkillResultResponse(BaseModel):
    id: int
    skill: str
    score: float
    max_score: float
    percentage: float
    questions_count: int
    demonstration_level: str
    evidence_before_assessment: Optional[str] = None
    feedback_summary: Optional[str] = None
    questions: List[AssessmentQuestionDetail] = []

    class Config:
        from_attributes = True

class AssessmentDetailResponse(BaseModel):
    id: int
    analysis_id: int
    candidate_id: int
    candidate_name: str
    job_title: str
    job_company: Optional[str] = ""
    status: str
    selected_skills: List[Dict[str, Any]] = []
    total_score: Optional[float] = None
    total_max_score: Optional[float] = None
    overall_percentage: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    questions: List[AssessmentQuestionPublic] = []
    results: List[AssessmentSkillResultResponse] = []

# --- Phase 5A Interview Schemas ---

class InterviewResponsePayload(BaseModel):
    candidate_response: Optional[str] = None
    interviewer_notes: Optional[str] = None

class InterviewFollowUpPayload(BaseModel):
    candidate_response: Optional[str] = ""

class InterviewQuestionResponse(BaseModel):
    id: int
    analysis_id: int
    order_num: int
    skill: str
    question_type: str
    difficulty: str
    question_text: str
    source_context: Optional[str] = None
    evidence_gap: Optional[str] = None
    why_generated: Optional[str] = None
    evaluation_points: List[str] = []
    parent_question_id: Optional[int] = None
    candidate_response: Optional[str] = None
    interviewer_notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Phase GitHub Intelligence Schemas ---

class GitHubEvidenceAnalyzePayload(BaseModel):
    analysis_id: int
    claim_id: int
    repository_url: str
    description: Optional[str] = None


