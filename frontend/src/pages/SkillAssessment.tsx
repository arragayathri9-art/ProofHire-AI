import { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Sparkles, 
  ArrowRight, 
  ArrowLeft, 
  BrainCircuit, 
  CheckCircle2, 
  AlertCircle,
  Code2,
  FileText,
  Lightbulb,
  Check,
  RotateCcw,
  Send,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Award,
  Layers,
  Clock,
  ListFilter
} from 'lucide-react';
import CandidatePipelineHeader from '../components/CandidatePipelineHeader';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

interface Question {
  id: number;
  assessment_id: number;
  order_num: number;
  skill: string;
  question_type: 'mcq' | 'scenario' | 'short_answer' | 'coding';
  difficulty: 'Basic' | 'Intermediate' | 'Advanced';
  question_text: string;
  options?: string[];
  max_score: number;
  candidate_answer?: string;
  correct_answer?: string;
  score?: number;
  is_correct?: boolean;
  evaluation_feedback?: string;
  rubric_breakdown?: Record<string, any>;
}

interface SkillResult {
  id: number;
  skill: string;
  score: number;
  max_score: number;
  percentage: number;
  questions_count: number;
  demonstration_level: string;
  evidence_before_assessment?: string;
  feedback_summary?: string;
  questions: Question[];
}

interface AssessmentData {
  id?: number;
  analysis_id: number;
  candidate_id: number;
  candidate_name: string;
  job_title: string;
  job_company?: string;
  status: 'not_generated' | 'ready' | 'in_progress' | 'completed';
  selected_skills?: Array<{
    skill: string;
    priority: string;
    evidence_level_before: string;
    recommended_difficulty: string;
    question_count: number;
    rationale: string;
  }>;
  total_score?: number;
  total_max_score?: number;
  overall_percentage?: number;
  created_at?: string;
  completed_at?: string;
  questions: Question[];
  results: SkillResult[];
  candidate_skills?: string[];
}

export default function SkillAssessment() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { activeAnalysisId, setActiveAnalysis } = useAnalysis();

  const currentId = id || activeAnalysisId;

  const [assessment, setAssessment] = useState<AssessmentData | null>(null);
  const [analysesList, setAnalysesList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Active quiz state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [expandedSkills, setExpandedSkills] = useState<Record<string, boolean>>({});
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);

  // Load assessment data
  const loadAssessment = async () => {
    if (!currentId) {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/analyses`);
        setAnalysesList(res.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/assessments/analysis/${currentId}`);
      setAssessment(res.data);
      
      if (res.data.candidate_name) {
        setActiveAnalysis(Number(currentId), {
          name: res.data.candidate_name,
          jobTitle: res.data.job_title || 'Target Job',
          candidateId: res.data.candidate_id
        });
      }

      // Populate already saved answers if any
      const existingAnswers: Record<number, string> = {};
      if (res.data.questions) {
        res.data.questions.forEach((q: Question) => {
          if (q.candidate_answer) {
            existingAnswers[q.id] = q.candidate_answer;
          }
        });
      }
      setAnswers(existingAnswers);

      // Expand all skill details by default on completed view
      if (res.data.status === 'completed' && res.data.results) {
        const exp: Record<string, boolean> = {};
        res.data.results.forEach((r: SkillResult) => {
          exp[r.skill] = true;
        });
        setExpandedSkills(exp);
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Failed to load assessment data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssessment();
  }, [currentId]);

  // Handle Generate Assessment
  const handleGenerate = async (regenerate = false) => {
    if (!currentId) return;
    setIsGenerating(true);
    setErrorMsg(null);
    setShowRegenerateModal(false);
    try {
      await axios.post(`${API_BASE_URL}/api/assessments/generate/${currentId}?regenerate=${regenerate}`);
      await loadAssessment();
      setCurrentQuestionIndex(0);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Failed to generate assessment. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle Answer Change
  const handleAnswerChange = (questionId: number, value: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  // Save Progress on Question change
  const saveCurrentAnswer = async (questionId: number, answerVal: string) => {
    if (!assessment?.id) return;
    try {
      await axios.post(`${API_BASE_URL}/api/assessments/${assessment.id}/save-progress`, {
        question_id: questionId,
        candidate_answer: answerVal || ''
      });
    } catch (err) {
      console.error('Auto-save progress error:', err);
    }
  };

  const handleNext = () => {
    if (!assessment?.questions) return;
    const currentQ = assessment.questions[currentQuestionIndex];
    if (currentQ) {
      saveCurrentAnswer(currentQ.id, answers[currentQ.id] || '');
    }
    if (currentQuestionIndex < assessment.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (!assessment?.questions) return;
    const currentQ = assessment.questions[currentQuestionIndex];
    if (currentQ) {
      saveCurrentAnswer(currentQ.id, answers[currentQ.id] || '');
    }
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  // Submit Assessment
  const handleSubmit = async () => {
    if (!assessment?.id || !assessment?.questions) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    setShowSubmitModal(false);

    try {
      const payloadResponses = assessment.questions.map(q => ({
        question_id: q.id,
        candidate_answer: answers[q.id] || ''
      }));

      await axios.post(`${API_BASE_URL}/api/assessments/${assessment.id}/submit`, {
        responses: payloadResponses
      });

      await loadAssessment();
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Failed to submit assessment evaluation.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleSkillDetails = (skill: string) => {
    setExpandedSkills(prev => ({
      ...prev,
      [skill]: !prev[skill]
    }));
  };

  // Calculate answered count
  const answeredCount = useMemo(() => {
    if (!assessment?.questions) return 0;
    return assessment.questions.filter(q => (answers[q.id] || '').trim().length > 0).length;
  }, [answers, assessment?.questions]);

  // Loading skeleton
  if (loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6 py-8">
        <div className="animate-pulse bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <div className="h-6 bg-slate-200 rounded w-1/3"></div>
          <div className="h-4 bg-slate-100 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  // 1. Candidate Selection Screen (When no active analysis ID)
  if (!currentId && analysesList.length > 0) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-12">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 text-blue-600 flex items-center justify-center font-bold">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Skill Assessment — Select Candidate</h2>
              <p className="text-slate-500 text-xs">Choose a candidate analysis to formulate or review personalized technical assessments.</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 divide-y divide-slate-100 overflow-hidden">
          {analysesList.map(a => (
            <div key={a.id} className="p-5 flex items-center justify-between hover:bg-slate-50/80 transition-colors">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <p className="font-bold text-slate-800 text-sm">{a.candidate_name}</p>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold border border-slate-200">
                    Analysis #{a.id}
                  </span>
                  {a.assessment_status === 'completed' && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      Assessment Completed
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500">
                  Target Role: <strong className="text-slate-700 font-medium">{a.job_title}</strong> {a.job_company ? `at ${a.job_company}` : ''}
                </p>
                <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1">
                  <span>{a.claims_count} Resume Claims</span>
                  <span>•</span>
                  <span>{a.evidence_count} Supporting Evidence</span>
                  <span>•</span>
                  <span>Stage: <strong className="text-slate-600">{a.current_stage || 'Evidence Verification'}</strong></span>
                </div>
              </div>
              <button 
                onClick={() => navigate(`/assessment/${a.id}`)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <span>{a.assessment_status === 'completed' ? 'View Results' : 'Open Assessment'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const status = assessment?.status || 'not_generated';
  const questions = assessment?.questions || [];
  const currentQuestion = questions[currentQuestionIndex];
  const results = assessment?.results || [];

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      {/* Pipeline Navigation Header */}
      <CandidatePipelineHeader 
        analysisId={currentId || undefined} 
        candidateName={assessment?.candidate_name} 
        jobTitle={assessment?.job_title} 
      />

      {/* Header & Provenance Banner */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
                Technical Assessment
              </span>
              <h1 className="text-2xl font-black text-slate-900 tracking-tight">ProofHire Skill Assessment</h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Candidate: <strong className="text-slate-800 font-semibold">{assessment?.candidate_name}</strong>
              <span className="mx-2 text-slate-300">|</span>
              Target Job: <strong className="text-slate-800 font-semibold">{assessment?.job_title}</strong> {assessment?.job_company ? `(${assessment.job_company})` : ''}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 text-xs font-bold rounded-full border flex items-center gap-1.5 ${
              status === 'completed'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : status === 'in_progress'
                ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                : status === 'ready'
                ? 'bg-blue-50 text-blue-700 border-blue-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}>
              {status === 'completed' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
              {status === 'in_progress' && <Clock className="w-3.5 h-3.5 text-indigo-600 animate-spin" />}
              <span>
                Status: {status === 'completed' ? 'Completed' : status === 'in_progress' ? 'In Progress' : status === 'ready' ? 'Ready' : 'Not Generated'}
              </span>
            </span>

            {status === 'completed' && (
              <button
                onClick={() => setShowRegenerateModal(true)}
                className="px-3 py-1 text-xs font-semibold text-slate-600 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors flex items-center gap-1 cursor-pointer"
                title="Regenerate Assessment"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Regenerate</span>
              </button>
            )}
          </div>
        </div>

        {/* Provenance Checklist */}
        <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center gap-3 sm:gap-6 text-xs text-slate-600 bg-slate-50/70 p-3 rounded-xl border border-slate-200/60">
          <span className="font-semibold text-slate-500 text-[11px] uppercase tracking-wider">Assessment generated from:</span>
          <div className="flex items-center gap-1.5 font-medium text-slate-700">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Resume Analysis</span>
          </div>
          <div className="flex items-center gap-1.5 font-medium text-slate-700">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Job Requirements</span>
          </div>
          <div className="flex items-center gap-1.5 font-medium text-slate-700">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Evidence Verification</span>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* 2. NOT GENERATED STATE */}
      {status === 'not_generated' && (
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-100 text-blue-600 flex items-center justify-center mx-auto shadow-xs">
            <BrainCircuit className="w-8 h-8" />
          </div>

          <div className="max-w-xl mx-auto space-y-2">
            <h2 className="text-2xl font-black text-slate-900">Personalized Skill Assessment</h2>
            <p className="text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-200 py-1 px-3 rounded-full inline-block">
              Skill assessment has not been generated yet.
            </p>
            <p className="text-slate-600 text-xs sm:text-sm leading-relaxed mt-1">
              ProofHire will synthesize the candidate's verified evidence levels, resume claims, and target job requirements to generate a personalized technical evaluation.
            </p>
          </div>

          {/* Key Target Skills preview */}
          {assessment?.candidate_skills && assessment.candidate_skills.length > 0 && (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl max-w-lg mx-auto text-left space-y-2">
              <p className="text-[11px] font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                <span>Target Candidate Skills Pool</span>
              </p>
              <div className="flex flex-wrap gap-1.5">
                {assessment.candidate_skills.slice(0, 8).map((s, idx) => (
                  <span key={idx} className="px-2.5 py-1 bg-white border border-slate-200 rounded-md text-xs font-semibold text-slate-700 shadow-2xs">
                    {s}
                  </span>
                ))}
                {assessment.candidate_skills.length > 8 && (
                  <span className="px-2 py-1 text-xs text-slate-400 font-medium">+{assessment.candidate_skills.length - 8} more</span>
                )}
              </div>
            </div>
          )}

          <div className="pt-4 flex justify-center gap-4">
            <button
              onClick={() => navigate(`/evidence/${currentId}`)}
              className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Evidence Center</span>
            </button>
            <button
              onClick={() => handleGenerate(false)}
              disabled={isGenerating}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold rounded-xl text-xs transition-all shadow-sm flex items-center gap-2 cursor-pointer"
            >
              {isGenerating ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  <span>Planning & Generating Assessment...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Personalized Assessment</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* 3. ACTIVE ASSESSMENT STATE (Ready or In Progress) */}
      {(status === 'ready' || status === 'in_progress') && currentQuestion && (
        <div className="space-y-6">
          {/* Assessment Progress & Question Pills Bar */}
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Candidate Assessment Progress</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-lg font-black text-slate-900">
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </span>
                  <span className="text-xs text-slate-400 font-medium">
                    ({answeredCount} of {questions.length} answered)
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowSubmitModal(true)}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Assessment</span>
                </button>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
              ></div>
            </div>

            {/* Question Quick Jump Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto py-1">
              {questions.map((q, idx) => {
                const isCurrent = idx === currentQuestionIndex;
                const isAnswered = (answers[q.id] || '').trim().length > 0;
                return (
                  <button
                    key={q.id}
                    onClick={() => {
                      saveCurrentAnswer(currentQuestion.id, answers[currentQuestion.id] || '');
                      setCurrentQuestionIndex(idx);
                    }}
                    className={`w-8 h-8 rounded-lg text-xs font-bold flex items-center justify-center shrink-0 transition-all cursor-pointer ${
                      isCurrent
                        ? 'bg-blue-600 text-white ring-2 ring-blue-300 shadow-xs'
                        : isAnswered
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200 border border-slate-200'
                    }`}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Current Question Card */}
          <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 space-y-6">
            {/* Meta Tags */}
            <div className="flex flex-wrap items-center gap-2 pb-4 border-b border-slate-100">
              {/* Skill Tag */}
              <span className="px-3 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg text-xs font-bold flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" />
                <span>Skill: {currentQuestion.skill}</span>
              </span>

              {/* Difficulty Tag */}
              <span className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${
                currentQuestion.difficulty === 'Advanced'
                  ? 'bg-purple-50 text-purple-700 border-purple-200'
                  : currentQuestion.difficulty === 'Intermediate'
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
              }`}>
                Difficulty: {currentQuestion.difficulty}
              </span>

              {/* Type Tag */}
              <span className="px-2.5 py-1 bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5">
                {currentQuestion.question_type === 'mcq' && <ListFilter className="w-3.5 h-3.5 text-slate-500" />}
                {currentQuestion.question_type === 'scenario' && <Lightbulb className="w-3.5 h-3.5 text-amber-500" />}
                {currentQuestion.question_type === 'short_answer' && <FileText className="w-3.5 h-3.5 text-blue-500" />}
                {currentQuestion.question_type === 'coding' && <Code2 className="w-3.5 h-3.5 text-emerald-500" />}
                <span className="capitalize">{currentQuestion.question_type.replace('_', ' ')} Question</span>
              </span>

              <span className="ml-auto text-xs text-slate-400 font-medium">
                Max Score: {currentQuestion.max_score} pts
              </span>
            </div>

            {/* Question Text */}
            <div className="space-y-3">
              <h3 className="text-base sm:text-lg font-bold text-slate-900 leading-relaxed whitespace-pre-wrap">
                {currentQuestion.question_text}
              </h3>
            </div>

            {/* Interactive Inputs based on Question Type */}
            <div className="pt-2">
              {/* 1. MCQ OPTIONS */}
              {currentQuestion.question_type === 'mcq' && currentQuestion.options && (
                <div className="space-y-2.5">
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Select the correct option:</p>
                  {currentQuestion.options.map((opt, idx) => {
                    const optKey = opt.trim().charAt(0).toUpperCase();
                    const isSelected = answers[currentQuestion.id] === opt || answers[currentQuestion.id] === optKey;
                    return (
                      <div
                        key={idx}
                        onClick={() => handleAnswerChange(currentQuestion.id, optKey)}
                        className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-3 ${
                          isSelected
                            ? 'bg-blue-50/70 border-blue-500 ring-1 ring-blue-500 shadow-xs'
                            : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                        }`}
                      >
                        <div className={`w-5 h-5 rounded-full border flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                          isSelected ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-300 bg-white'
                        }`}>
                          {isSelected && <div className="w-2 h-2 rounded-full bg-white"></div>}
                        </div>
                        <span className={`text-xs sm:text-sm leading-relaxed ${isSelected ? 'font-bold text-blue-900' : 'text-slate-800'}`}>
                          {opt}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* 2. SCENARIO / SHORT ANSWER TEXTAREA */}
              {(currentQuestion.question_type === 'scenario' || currentQuestion.question_type === 'short_answer') && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Candidate Explanation / Technical Response:</label>
                    <span className="text-[11px] text-slate-400">
                      {(answers[currentQuestion.id] || '').length} characters
                    </span>
                  </div>
                  <textarea
                    rows={6}
                    value={answers[currentQuestion.id] || ''}
                    onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                    placeholder="Provide your technical explanation, architectural approach, and rationale here..."
                    className="w-full p-4 rounded-xl border border-slate-200 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent leading-relaxed bg-white shadow-2xs font-sans"
                  />
                  <p className="text-[11px] text-slate-400">
                    Evaluation will be performed against a predefined rubric measuring technical correctness, relevance, reasoning, and completeness.
                  </p>
                </div>
              )}

              {/* 3. CODING / OUTPUT QUESTION */}
              {currentQuestion.question_type === 'coding' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                      <Code2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Code / Output Implementation Box:</span>
                    </label>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {(answers[currentQuestion.id] || '').split('\n').length} lines
                    </span>
                  </div>
                  <div className="relative rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-sm">
                    <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
                      <span>Code Editor / Output Terminal</span>
                      <span>UTF-8</span>
                    </div>
                    <textarea
                      rows={8}
                      value={answers[currentQuestion.id] || ''}
                      onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                      placeholder="# Enter your code solution or exact predicted output here&#10;def solution():&#10;    pass"
                      className="w-full p-4 font-mono text-xs sm:text-sm text-emerald-400 bg-slate-950 focus:outline-none leading-relaxed resize-y selection:bg-emerald-900"
                      spellCheck={false}
                    />
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Deterministic checks will compare outputs and test case requirements before rubric evaluation.
                  </p>
                </div>
              )}
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between pt-6 border-t border-slate-100">
              <button
                onClick={handlePrev}
                disabled={currentQuestionIndex === 0}
                className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous Question</span>
              </button>

              <div className="flex items-center gap-2">
                {currentQuestionIndex < questions.length - 1 ? (
                  <button
                    onClick={handleNext}
                    className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
                  >
                    <span>Save & Next Question</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      saveCurrentAnswer(currentQuestion.id, answers[currentQuestion.id] || '');
                      setShowSubmitModal(true);
                    }}
                    className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Review & Submit Assessment</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. COMPLETED RESULTS PAGE */}
      {status === 'completed' && (
        <div className="space-y-6">
          {/* Main Results Summary Card */}
          <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full flex items-center gap-1 w-fit mb-1.5">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  Evaluation Completed
                </span>
                <h2 className="text-2xl font-black text-slate-900 tracking-tight">SKILL ASSESSMENT RESULTS</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Standardized mathematical scores computed from candidate responses against deterministic test cases and predefined rubrics.
                </p>
              </div>

              {/* Total Score Badge */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center sm:text-right shrink-0">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Overall Assessment Score</p>
                <div className="flex items-baseline gap-1 justify-center sm:justify-end mt-0.5">
                  <span className="text-3xl font-black text-slate-900">
                    {assessment?.overall_percentage?.toFixed(0)}%
                  </span>
                  <span className="text-xs text-slate-500 font-semibold">
                    ({assessment?.total_score} / {assessment?.total_max_score} pts)
                  </span>
                </div>
              </div>
            </div>

            {/* Assessment Planning Context */}
            {assessment?.selected_skills && assessment.selected_skills.length > 0 && (
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <p className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>Assessment Planning Agent Rationale</span>
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  {assessment.selected_skills.map((plan, idx) => (
                    <div key={idx} className="p-3 bg-white rounded-lg border border-slate-200 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800">{plan.skill}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold border border-blue-200">
                          Priority: {plan.priority}
                        </span>
                      </div>
                      <p className="text-slate-500 text-[11px] leading-relaxed">{plan.rationale}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skill-by-Skill Result Cards */}
            <div className="space-y-4 pt-2">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Award className="w-4 h-4 text-blue-600" />
                <span>Skill Demonstration Breakdown</span>
              </h3>

              <div className="space-y-4">
                {results.map((res) => {
                  const isExpanded = expandedSkills[res.skill] ?? true;
                  const pct = Math.round(res.percentage);

                  return (
                    <div key={res.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs">
                      {/* Skill Card Header */}
                      <div className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50/50">
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2">
                            <h4 className="text-lg font-bold text-slate-900">{res.skill}</h4>
                            <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-white border border-slate-200 text-slate-700 shadow-2xs">
                              {res.score} / {res.max_score} pts
                            </span>
                          </div>

                          <div className="flex flex-wrap items-center gap-3 text-xs">
                            <span className="text-slate-500">
                              Questions: <strong className="text-slate-700">{res.questions_count}</strong>
                            </span>
                            <span className="text-slate-300">•</span>
                            <span className="text-slate-500">
                              Evidence before assessment: <strong className="text-slate-700">{res.evidence_before_assessment || 'Needs Verification'}</strong>
                            </span>
                          </div>

                          {/* Demonstration Level Badge (Neutral Language Rule) */}
                          <div className="pt-1">
                            <span className={`px-2.5 py-0.5 rounded-md text-xs font-bold border inline-flex items-center gap-1 ${
                              pct >= 80
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                                : pct >= 65
                                ? 'bg-blue-50 text-blue-800 border-blue-300'
                                : pct >= 40
                                ? 'bg-amber-50 text-amber-800 border-amber-300'
                                : 'bg-slate-100 text-slate-700 border-slate-300'
                            }`}>
                              <CheckCircle2 className="w-3 h-3" />
                              <span>{res.demonstration_level}</span>
                            </span>
                          </div>
                        </div>

                        {/* Percentage and Expand toggle */}
                        <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-3">
                          <div className="text-right">
                            <span className="text-2xl font-black text-slate-900">{pct}%</span>
                          </div>

                          <button
                            onClick={() => toggleSkillDetails(res.skill)}
                            className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-xs font-semibold text-slate-700 transition-colors flex items-center gap-1 cursor-pointer"
                          >
                            <span>{isExpanded ? 'Hide Details' : 'View Details'}</span>
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </div>

                      {/* Detailed Question Review (Expanded) */}
                      {isExpanded && (
                        <div className="p-5 border-t border-slate-200 divide-y divide-slate-100 space-y-4">
                          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">Evaluated Question Breakdown</p>
                          {res.questions.map((q, idx) => (
                            <div key={q.id} className="pt-4 first:pt-0 space-y-2.5">
                              <div className="flex items-center justify-between gap-2">
                                <span className="text-xs font-bold text-slate-700">
                                  Q{idx + 1}. [{q.question_type.toUpperCase()}] ({q.difficulty})
                                </span>
                                <span className={`text-xs font-bold px-2 py-0.5 rounded border ${
                                  q.is_correct
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                    : (q.score || 0) > 0
                                    ? 'bg-blue-50 text-blue-700 border-blue-200'
                                    : 'bg-rose-50 text-rose-700 border-rose-200'
                                }`}>
                                  Score: {q.score} / {q.max_score} pts
                                </span>
                              </div>

                              <p className="text-xs font-medium text-slate-800 whitespace-pre-wrap">{q.question_text}</p>

                              {/* Candidate Answer Box */}
                              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1">
                                <span className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">Candidate Answer:</span>
                                <p className="font-mono text-slate-800 whitespace-pre-wrap">
                                  {q.candidate_answer ? q.candidate_answer : <span className="italic text-slate-400">No response submitted.</span>}
                                </p>
                              </div>

                              {/* Correct Answer / Reference */}
                              {q.correct_answer && (
                                <div className="p-3 rounded-lg bg-blue-50/50 border border-blue-100 text-xs space-y-1">
                                  <span className="font-bold text-blue-800 uppercase tracking-wider text-[10px]">Reference / Correct Answer:</span>
                                  <p className="font-mono text-blue-900 whitespace-pre-wrap">{q.correct_answer}</p>
                                </div>
                              )}

                              {/* Evaluation Explanation */}
                              {q.evaluation_feedback && (
                                <div className="p-3 rounded-lg bg-emerald-50/40 border border-emerald-100 text-xs space-y-1">
                                  <span className="font-bold text-emerald-800 uppercase tracking-wider text-[10px]">Evaluation Rationale:</span>
                                  <p className="text-emerald-900 leading-relaxed">{q.evaluation_feedback}</p>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Evidence Center Integration Notice (Section 12) */}
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div className="space-y-0.5 text-xs text-emerald-900">
                <p className="font-bold">Registered as a Verified Evidence Source</p>
                <p className="text-emerald-700 leading-relaxed">
                  These skill assessment results have been added as verified evidence records alongside resume claims and project repository data, directly preparing the pipeline for Verified Skill Profile.
                </p>
              </div>
            </div>

            {/* Action Footer */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-slate-100">
              <button
                onClick={() => navigate(`/evidence/${currentId}`)}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to Evidence Center</span>
              </button>

              <button
                onClick={() => navigate(`/skill-profile/${currentId}`)}
                className="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Continue to Verified Skill Profile</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Submitting */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Submit Skill Assessment</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              You have answered <strong>{answeredCount}</strong> of <strong>{questions.length}</strong> questions. 
              {answeredCount < questions.length && (
                <span className="block mt-1 text-amber-600 font-semibold">
                  Note: {questions.length - answeredCount} questions have not been answered. Unanswered questions will receive 0 points.
                </span>
              )}
            </p>
            <p className="text-xs text-slate-500">
              Upon submission, your responses will be objectively evaluated against deterministic criteria and stored evaluation rubrics.
            </p>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowSubmitModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
              >
                Continue Answering
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-xs cursor-pointer flex items-center gap-1.5"
              >
                {isSubmitting ? (
                  <>
                    <Clock className="w-3.5 h-3.5 animate-spin" />
                    <span>Evaluating...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    <span>Confirm & Submit</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Regenerating */}
      {showRegenerateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Regenerate Assessment</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              This will replace/recompute the current generated output. Continue?
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowRegenerateModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => handleGenerate(true)}
                disabled={isGenerating}
                className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-xs cursor-pointer flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Continue</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
