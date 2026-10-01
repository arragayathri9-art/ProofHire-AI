import { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  MessageSquareText, 
  ArrowRight, 
  ArrowLeft, 
  RefreshCw, 
  ShieldCheck, 
  CheckCircle2, 
  HelpCircle, 
  AlertCircle, 
  CornerDownRight, 
  FileText, 
  Briefcase, 
  Layers, 
  Save, 
  User, 
  Sparkles, 
  PieChart, 
  Search,
  Check
} from 'lucide-react';
import CandidatePipelineHeader from '../components/CandidatePipelineHeader';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

interface InterviewQuestion {
  id: number;
  analysis_id: number;
  order_num: number;
  skill: string;
  question_type: string;
  difficulty: string;
  question_text: string;
  source_context?: string | null;
  evidence_gap?: string | null;
  why_generated?: string | null;
  evaluation_points: string[];
  parent_question_id?: number | null;
  candidate_response?: string | null;
  interviewer_notes?: string | null;
  created_at?: string | null;
}

interface SelectedSkillPlan {
  skill: string;
  evidence_level: string;
  is_required: boolean;
  is_preferred: boolean;
  assessment_percentage?: number | null;
  assessment_label?: string | null;
  claims_count?: number;
  reason: string;
  priority_weight?: number;
}

interface InterviewData {
  analysis_id: number;
  candidate_name: string;
  job_title: string;
  plan: {
    analysis_id: number;
    planning_summary: string;
    selected_skills: SelectedSkillPlan[];
  };
  questions_count: number;
  questions: InterviewQuestion[];
}

export default function InterviewIntelligence() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { activeAnalysisId, setActiveAnalysis } = useAnalysis();

  const [data, setData] = useState<InterviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [generatingFollowUpFor, setGeneratingFollowUpFor] = useState<number | null>(null);
  const [analysesList, setAnalysesList] = useState<any[]>([]);

  // Modes: 'interviewer' | 'candidate'
  const [viewMode, setViewMode] = useState<'interviewer' | 'candidate'>('interviewer');
  
  // Local edit state for responses & notes: { [questionId]: { response, notes, savingResponse, savingNotes, savedResponse, savedNotes } }
  const [inputs, setInputs] = useState<{
    [qId: number]: {
      response: string;
      notes: string;
      savingResponse?: boolean;
      savingNotes?: boolean;
      savedResponse?: boolean;
      savedNotes?: boolean;
    };
  }>({});

  const [filterSkill, setFilterSkill] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const currentId = id || activeAnalysisId;

  const fetchInterview = (analysisId: number | string) => {
    setLoading(true);
    axios.get(`${API_BASE_URL}/api/interview/${analysisId}`)
      .then(res => {
        setData(res.data);
        setLoading(false);

        // Pre-populate response and notes inputs
        const initialInputs: any = {};
        (res.data.questions || []).forEach((q: InterviewQuestion) => {
          initialInputs[q.id] = {
            response: q.candidate_response || '',
            notes: q.interviewer_notes || ''
          };
        });
        setInputs(initialInputs);

        if (res.data.candidate_name) {
          setActiveAnalysis(Number(analysisId), {
            name: res.data.candidate_name,
            jobTitle: res.data.job_title || 'Target Job',
            candidateId: res.data.candidate_id || 0
          });
        }
      })
      .catch(err => {
        console.error('Failed to fetch interview intelligence:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    if (id) {
      fetchInterview(id);
    } else if (activeAnalysisId) {
      navigate(`/interview/${activeAnalysisId}`, { replace: true });
    } else {
      // Fetch available analyses for selection
      axios.get(`${API_BASE_URL}/api/analyses`)
        .then(res => {
          setAnalysesList(res.data || []);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [id, activeAnalysisId]);

  const handleRegenerate = () => {
    if (!currentId) return;
    setRegenerating(true);
    axios.post(`${API_BASE_URL}/api/interview/generate/${currentId}`)
      .then(() => {
        fetchInterview(currentId);
        setRegenerating(false);
      })
      .catch(err => {
        console.error('Error regenerating interview:', err);
        setRegenerating(false);
      });
  };

  const handleSaveResponse = (questionId: number) => {
    const text = inputs[questionId]?.response || '';
    setInputs(prev => ({
      ...prev,
      [questionId]: { ...prev[questionId], savingResponse: true }
    }));

    axios.post(`${API_BASE_URL}/api/interview/${questionId}/response`, {
      candidate_response: text
    })
      .then(() => {
        setInputs(prev => ({
          ...prev,
          [questionId]: { ...prev[questionId], savingResponse: false, savedResponse: true }
        }));
        setTimeout(() => {
          setInputs(prev => ({
            ...prev,
            [questionId]: { ...prev[questionId], savedResponse: false }
          }));
        }, 2000);
      })
      .catch(err => {
        console.error('Save response error:', err);
        setInputs(prev => ({
          ...prev,
          [questionId]: { ...prev[questionId], savingResponse: false }
        }));
      });
  };

  const handleSaveNotes = (questionId: number) => {
    const notes = inputs[questionId]?.notes || '';
    setInputs(prev => ({
      ...prev,
      [questionId]: { ...prev[questionId], savingNotes: true }
    }));

    axios.post(`${API_BASE_URL}/api/interview/${questionId}/response`, {
      interviewer_notes: notes
    })
      .then(() => {
        setInputs(prev => ({
          ...prev,
          [questionId]: { ...prev[questionId], savingNotes: false, savedNotes: true }
        }));
        setTimeout(() => {
          setInputs(prev => ({
            ...prev,
            [questionId]: { ...prev[questionId], savedNotes: false }
          }));
        }, 2000);
      })
      .catch(err => {
        console.error('Save notes error:', err);
        setInputs(prev => ({
          ...prev,
          [questionId]: { ...prev[questionId], savingNotes: false }
        }));
      });
  };

  const handleGenerateFollowUp = (parentQuestionId: number) => {
    setGeneratingFollowUpFor(parentQuestionId);
    const existingAnswer = inputs[parentQuestionId]?.response || '';

    axios.post(`${API_BASE_URL}/api/interview/${parentQuestionId}/follow-up`, {
      candidate_response: existingAnswer
    })
      .then(res => {
        const newQ: InterviewQuestion = res.data.follow_up;
        setData(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            questions_count: prev.questions_count + 1,
            questions: [...prev.questions, newQ]
          };
        });
        setInputs(prev => ({
          ...prev,
          [newQ.id]: {
            response: '',
            notes: ''
          }
        }));
        setGeneratingFollowUpFor(null);
      })
      .catch(err => {
        console.error('Failed to generate follow-up:', err);
        setGeneratingFollowUpFor(null);
      });
  };

  // Group questions into parents and nested follow-ups
  const { rootQuestions, followUpsByParent } = useMemo(() => {
    if (!data) return { rootQuestions: [], followUpsByParent: {} };
    const roots: InterviewQuestion[] = [];
    const followUps: { [parentId: number]: InterviewQuestion[] } = {};

    data.questions.forEach(q => {
      if (q.parent_question_id) {
        if (!followUps[q.parent_question_id]) {
          followUps[q.parent_question_id] = [];
        }
        followUps[q.parent_question_id].push(q);
      } else {
        roots.push(q);
      }
    });

    return { rootQuestions: roots, followUpsByParent: followUps };
  }, [data]);

  // Filter root questions
  const filteredRootQuestions = useMemo(() => {
    let list = rootQuestions;
    if (filterSkill !== 'all') {
      list = list.filter(q => q.skill.toLowerCase() === filterSkill.toLowerCase());
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(item => 
        item.skill.toLowerCase().includes(q) ||
        item.question_text.toLowerCase().includes(q) ||
        (item.why_generated && item.why_generated.toLowerCase().includes(q)) ||
        (item.source_context && item.source_context.toLowerCase().includes(q))
      );
    }
    return list;
  }, [rootQuestions, filterSkill, searchQuery]);

  // Calculate Interview Coverage
  const interviewCoverage = useMemo(() => {
    if (!data || !data.plan?.selected_skills) return [];
    return data.plan.selected_skills.map(s => {
      const relatedCount = (data.questions || []).filter(
        q => q.skill.toLowerCase() === s.skill.toLowerCase()
      ).length;
      return {
        skill: s.skill,
        evidence_level: s.evidence_level,
        questions_count: relatedCount,
        reason: s.reason
      };
    });
  }, [data]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        <p className="text-slate-600 font-medium text-sm">Loading interview intelligence probes & evaluation criteria...</p>
      </div>
    );
  }

  // Active analysis selected but interview not yet generated
  if (currentId && !data) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-purple-50 border border-purple-200 text-purple-600 flex items-center justify-center mx-auto shadow-xs">
          <MessageSquareText className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Interview Intelligence</h2>
        <p className="text-sm text-slate-600 max-w-md mx-auto">
          Interview Intelligence has not been generated yet.
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="px-5 py-2.5 bg-purple-600 text-white rounded-xl text-xs font-bold hover:bg-purple-700 shadow-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{regenerating ? 'Generating...' : 'Generate Interview Plan'}</span>
          </button>
          <Link
            to={`/skill-profile/${currentId}`}
            className="px-4 py-2.5 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-200"
          >
            <span>Skill Profile</span>
          </Link>
        </div>
      </div>
    );
  }

  // Candidate Selection Screen if no analysis selected
  if (!currentId) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-12">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
              <MessageSquareText className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Interview Intelligence — Select Candidate</h2>
              <p className="text-slate-500 text-sm mt-0.5">Select a candidate analysis to review their targeted interview questions.</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          {analysesList.length === 0 ? (
            <div className="text-center py-10 space-y-3">
              <AlertCircle className="w-10 h-10 text-slate-400 mx-auto" />
              <p className="text-slate-600 font-medium">No candidate analyses found.</p>
              <Link
                to="/analysis/new"
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-semibold hover:bg-blue-700 shadow-sm"
              >
                <span>Start New Analysis</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {analysesList.map(a => (
                <div key={a.id} className="py-4 flex items-center justify-between hover:bg-slate-50 px-4 rounded-xl transition-colors">
                  <div>
                    <div className="flex items-center gap-2.5">
                      <h4 className="font-bold text-slate-900 text-base">{a.candidate_name}</h4>
                      <span className="text-[11px] font-mono text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                        #{a.id}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5">
                      <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                      <span>{a.job_title}</span>
                    </p>
                  </div>
                  <button 
                    onClick={() => {
                      setActiveAnalysis(a.id, {
                        name: a.candidate_name,
                        jobTitle: a.job_title,
                        candidateId: a.candidate_id
                      });
                      navigate(`/interview/${a.id}`);
                    }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                  >
                    <span>Open Interview Intelligence</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { plan, questions_count } = data;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* 1. Candidate Pipeline Header */}
      <CandidatePipelineHeader 
        analysisId={currentId} 
        candidateName={data.candidate_name} 
        jobTitle={data.job_title} 
      />

      {/* 2. Top Header & Mode Toggle */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200 flex items-center gap-1">
                <MessageSquareText className="w-3.5 h-3.5" />
                Interview Intelligence
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                Decision Support Probes
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              INTERVIEW INTELLIGENCE
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Targeted, evidence-anchored interview questions tailored to candidate claims and verification gaps.
            </p>
          </div>

          {/* Mode Switcher: Interviewer Mode vs Candidate Mode */}
          <div className="flex items-center gap-3">
            <div className="bg-slate-100 p-1 rounded-xl flex items-center gap-1 text-xs font-semibold">
              <button
                onClick={() => setViewMode('interviewer')}
                className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
                  viewMode === 'interviewer'
                    ? 'bg-white text-purple-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Interviewer Mode</span>
              </button>
              <button
                onClick={() => setViewMode('candidate')}
                className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
                  viewMode === 'candidate'
                    ? 'bg-white text-blue-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <User className="w-3.5 h-3.5" />
                <span>Candidate Mode</span>
              </button>
            </div>

            <button
              onClick={() => setShowRegenerateModal(true)}
              disabled={regenerating}
              className="px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer disabled:opacity-50"
              title="Regenerates interview questions from latest evidence gaps"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin text-purple-600' : 'text-slate-500'}`} />
              <span>{regenerating ? 'Regenerating...' : 'Regenerate'}</span>
            </button>
          </div>
        </div>

        {/* Section 2: Pipeline Provenance Indicator */}
        <div className="mt-4 pt-3 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2 text-slate-600 font-medium">
            <span className="text-slate-400 font-bold uppercase text-[10px] tracking-wider">
              Interview generated from:
            </span>
            <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md font-semibold text-[11px] border border-emerald-200">
              <CheckCircle2 className="w-3 h-3" /> Resume Analysis
            </span>
            <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md font-semibold text-[11px] border border-emerald-200">
              <CheckCircle2 className="w-3 h-3" /> Evidence Verification
            </span>
            <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md font-semibold text-[11px] border border-emerald-200">
              <CheckCircle2 className="w-3 h-3" /> Skill Assessment
            </span>
            <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md font-semibold text-[11px] border border-emerald-200">
              <CheckCircle2 className="w-3 h-3" /> Verified Skill Profile
            </span>
          </div>

          <div className="text-slate-500 text-xs font-mono">
            {questions_count} Total Questions Generated
          </div>
        </div>

        {/* Mode Notification Banner */}
        {viewMode === 'candidate' ? (
          <div className="mt-4 p-3.5 bg-blue-50/70 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-start gap-2.5">
            <User className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <strong className="font-bold">Candidate Mode Active:</strong> Only questions and candidate response inputs are displayed. Internal evidence gaps, why-generated rationales, rubrics, and interviewer notes are strictly hidden to preserve interview integrity.
            </div>
          </div>
        ) : (
          <div className="mt-4 p-3.5 bg-purple-50/60 border border-purple-200 rounded-xl text-xs text-purple-900 flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
            <div>
              <strong className="font-bold">Interviewer Mode Active:</strong> Full visibility into candidate resume claims, evidence gaps, why-generated rationales, evaluation guidance points, and separate interviewer notes.
            </div>
          </div>
        )}
      </div>

      {/* 3. Section: INTERVIEW FOCUS (Shown in Interviewer Mode) */}
      {viewMode === 'interviewer' && plan?.selected_skills && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-600" />
                INTERVIEW FOCUS
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {plan.selected_skills.length} skills require deeper verification based on role requirements and assessment gaps.
              </p>
            </div>
            <span className="text-xs font-mono text-purple-700 bg-purple-50 px-2.5 py-1 rounded-md border border-purple-200 font-bold">
              Prioritized Target Areas
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {plan?.selected_skills?.map((s: any, idx: number) => (
              <div 
                key={idx}
                className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2 hover:border-purple-200 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-extrabold text-slate-900 text-sm">{s.skill}</h4>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    s.evidence_level === 'Good Evidence' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                    s.evidence_level === 'Moderate Evidence' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' :
                    s.evidence_level === 'Limited Evidence' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                    'bg-slate-100 text-slate-700 border-slate-300'
                  }`}>
                    {s.evidence_level}
                  </span>
                </div>
                <p className="text-slate-600 text-xs leading-relaxed line-clamp-3">
                  {s.reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Section: QUESTION CARDS */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-600" />
              TARGETED INTERVIEW PROBES
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Structured questions addressing evidence gaps, production execution trade-offs, and candidate project claims.
            </p>
          </div>

          {/* Skill Filter Buttons */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs font-semibold bg-slate-100 p-1 rounded-xl">
            <button
              onClick={() => setFilterSkill('all')}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                filterSkill === 'all' 
                  ? 'bg-white text-slate-900 shadow-xs' 
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Skills ({rootQuestions.length})
            </button>
            {plan?.selected_skills?.map((s: any) => (
              <button
                key={s.skill}
                onClick={() => setFilterSkill(s.skill)}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  filterSkill.toLowerCase() === s.skill.toLowerCase()
                    ? 'bg-purple-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-purple-700'
                }`}
              >
                {s.skill}
              </button>
            ))}
          </div>
        </div>

        {/* Search bar */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            type="text"
            placeholder="Search questions by skill, keyword, or claim context..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-transparent outline-none text-slate-800 placeholder-slate-400"
          />
        </div>

        {/* Questions List */}
        <div className="space-y-6">
          {filteredRootQuestions.map((q) => {
            const followUps = followUpsByParent[q.id] || [];
            return (
              <div key={q.id} className="space-y-3">
                {/* Main Question Card */}
                <QuestionCardItem 
                  question={q}
                  viewMode={viewMode}
                  inputs={inputs}
                  setInputs={setInputs}
                  onSaveResponse={handleSaveResponse}
                  onSaveNotes={handleSaveNotes}
                  onGenerateFollowUp={handleGenerateFollowUp}
                  isGeneratingFollowUp={generatingFollowUpFor === q.id}
                />

                {/* Nested Follow-Up Questions */}
                {followUps.length > 0 && (
                  <div className="ml-6 pl-4 border-l-2 border-purple-200 space-y-3 pt-1">
                    <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-purple-600">
                      <CornerDownRight className="w-3.5 h-3.5" />
                      <span>Follow-Up Probes ({followUps.length})</span>
                    </div>
                    {followUps.map((fu, fuIdx) => (
                      <QuestionCardItem 
                        key={fu.id}
                        question={fu}
                        viewMode={viewMode}
                        inputs={inputs}
                        setInputs={setInputs}
                        onSaveResponse={handleSaveResponse}
                        onSaveNotes={handleSaveNotes}
                        onGenerateFollowUp={handleGenerateFollowUp}
                        isGeneratingFollowUp={generatingFollowUpFor === fu.id}
                        isFollowUp={true}
                        followUpIndex={fuIdx + 1}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {filteredRootQuestions.length === 0 && (
            <div className="text-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <p className="text-slate-500 text-sm">No interview questions match your current filter.</p>
            </div>
          )}
        </div>
      </div>

      {/* 9. Section: INTERVIEW COVERAGE (Shown in Interviewer Mode) */}
      {viewMode === 'interviewer' && interviewCoverage.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-base font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <PieChart className="w-4 h-4 text-blue-600" />
              INTERVIEW COVERAGE
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Breakdown of how interview time and generated probes are allocated across evidence gaps.
            </p>
          </div>

          <div className="divide-y divide-slate-100">
            {interviewCoverage.map((c, idx) => (
              <div key={idx} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900">{c.skill}</span>
                    <span className="text-slate-400 font-medium">|</span>
                    <span className="text-slate-500">Evidence before interview:</span>
                    <span className="font-semibold text-slate-700">{c.evidence_level}</span>
                  </div>
                  <p className="text-slate-500 text-[11px] mt-0.5 line-clamp-1">{c.reason}</p>
                </div>
                <div className="shrink-0 flex items-center gap-2 font-mono">
                  <span className="px-2.5 py-1 bg-purple-50 text-purple-700 border border-purple-200 font-bold rounded-lg text-xs">
                    {c.questions_count} question{c.questions_count !== 1 ? 's' : ''} generated
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 10. Section: PIPELINE INTEGRATION & GENERATE REPORT BUTTON */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Evaluation Journey</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Interview Intelligence Complete
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900">
            Proceed to ProofHire Evaluation Report
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Consolidates resume claims, external evidence, assessment scores, and interview responses into an explainable summary report.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to={`/skill-profile/${currentId}`}
            className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Skill Profile</span>
          </Link>
          <Link
            to={`/reports/${currentId}`}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-sm cursor-pointer"
          >
            <span>GENERATE PROOFHIRE REPORT</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Confirmation Modal for Regenerating */}
      {showRegenerateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Regenerate Interview Probes</h3>
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
                onClick={() => {
                  setShowRegenerateModal(false);
                  handleRegenerate();
                }}
                disabled={regenerating}
                className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-xs cursor-pointer flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
                <span>Continue</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Subcomponent: Question Card Item
interface QuestionCardItemProps {
  question: InterviewQuestion;
  viewMode: 'interviewer' | 'candidate';
  inputs: any;
  setInputs: React.Dispatch<React.SetStateAction<any>>;
  onSaveResponse: (qId: number) => void;
  onSaveNotes: (qId: number) => void;
  onGenerateFollowUp: (qId: number) => void;
  isGeneratingFollowUp: boolean;
  isFollowUp?: boolean;
  followUpIndex?: number;
}

function QuestionCardItem({
  question,
  viewMode,
  inputs,
  setInputs,
  onSaveResponse,
  onSaveNotes,
  onGenerateFollowUp,
  isGeneratingFollowUp,
  isFollowUp = false,
  followUpIndex = 1
}: QuestionCardItemProps) {
  const currentInputs = inputs[question.id] || { response: '', notes: '' };

  const getQuestionTypeBadge = (type: string) => {
    switch (type) {
      case 'Project Deep-Dive':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">Project Deep-Dive</span>;
      case 'Debugging / Problem Solving':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">Debugging / Problem Solving</span>;
      case 'Scenario':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">Scenario</span>;
      case 'Evidence Clarification':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">Evidence Clarification</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">{type}</span>;
    }
  };

  return (
    <div className={`bg-white border rounded-2xl p-5 shadow-xs transition-all ${
      isFollowUp ? 'border-purple-200 bg-purple-50/20' : 'border-slate-200 hover:border-slate-300'
    }`}>
      {/* Top Metadata */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-3.5">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
            isFollowUp ? 'bg-purple-100 text-purple-800' : 'bg-slate-100 text-slate-800'
          }`}>
            {isFollowUp ? `Follow-Up #${followUpIndex}` : `Question #${question.order_num}`}
          </span>
          <span className="text-xs font-extrabold text-slate-900 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
            Skill: {question.skill}
          </span>
          {viewMode === 'interviewer' && getQuestionTypeBadge(question.question_type)}
          {viewMode === 'interviewer' && (
            <span className="text-[10px] font-semibold text-slate-500 uppercase">
              {question.difficulty}
            </span>
          )}
        </div>

        {/* Follow-up button in Interviewer Mode */}
        {viewMode === 'interviewer' && !isFollowUp && (
          <button
            onClick={() => onGenerateFollowUp(question.id)}
            disabled={isGeneratingFollowUp}
            className="px-3 py-1 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50"
            title="Generates a targeted follow-up question related to this skill"
          >
            <Sparkles className={`w-3 h-3 ${isGeneratingFollowUp ? 'animate-spin' : ''}`} />
            <span>{isGeneratingFollowUp ? 'Generating...' : '+ Generate Follow-Up'}</span>
          </button>
        )}
      </div>

      {/* Question Text */}
      <div className="space-y-1 mb-4">
        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Question:
        </p>
        <p className="text-slate-900 text-sm md:text-base font-semibold leading-relaxed">
          {question.question_text}
        </p>
      </div>

      {/* INTERVIEWER ONLY SECTION: Why This Question & Evaluation Points */}
      {viewMode === 'interviewer' && (
        <div className="space-y-3 mb-4 pt-3 border-t border-slate-100">
          {/* Why This Question */}
          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1.5 text-xs">
            <div className="flex items-center gap-1.5 font-bold text-slate-800 text-xs">
              <HelpCircle className="w-3.5 h-3.5 text-blue-600" />
              <span>WHY THIS QUESTION?</span>
              {question.evidence_gap && (
                <span className="ml-auto text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded">
                  Evidence Gap: {question.evidence_gap}
                </span>
              )}
            </div>
            <p className="text-slate-600 leading-relaxed text-[11px]">
              {question.why_generated}
            </p>
            {question.source_context && (
              <div className="pt-1.5 border-t border-slate-200/60 text-[11px] text-slate-500 flex items-start gap-1.5">
                <FileText className="w-3 h-3 text-slate-400 shrink-0 mt-0.5" />
                <span className="italic">{question.source_context}</span>
              </div>
            )}
          </div>

          {/* Suggested Evaluation Points */}
          {question.evaluation_points && question.evaluation_points.length > 0 && (
            <div className="bg-purple-50/50 p-3.5 rounded-xl border border-purple-200 space-y-1.5 text-xs">
              <span className="font-bold text-purple-900 text-[11px] uppercase tracking-wider flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-purple-600" />
                SUGGESTED EVALUATION POINTS (Interviewer Guidance)
              </span>
              <ul className="list-disc list-inside space-y-1 text-slate-700 text-[11px] pl-1">
                {question.evaluation_points.map((pt, idx) => (
                  <li key={idx} className="leading-relaxed">{pt}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Response and Notes Section */}
      <div className="space-y-4 pt-3 border-t border-slate-100">
        {/* 1. Candidate Response */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <label className="font-bold text-slate-700 text-xs flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-blue-600" />
              <span>Candidate Response</span>
            </label>
            <button
              onClick={() => onSaveResponse(question.id)}
              disabled={currentInputs.savingResponse}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer disabled:opacity-50"
            >
              {currentInputs.savedResponse ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-600 font-bold">Saved!</span>
                </>
              ) : (
                <>
                  <Save className="w-3 h-3" />
                  <span>{currentInputs.savingResponse ? 'Saving...' : 'Save Response'}</span>
                </>
              )}
            </button>
          </div>
          <textarea
            rows={viewMode === 'candidate' ? 4 : 2}
            placeholder="Type or transcribe candidate's response to this question..."
            value={currentInputs.response}
            onChange={(e) => {
              const val = e.target.value;
              setInputs((prev: any) => ({
                ...prev,
                [question.id]: { ...prev[question.id], response: val }
              }));
            }}
            className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-blue-500 focus:outline-none transition-all placeholder-slate-400"
          />
        </div>

        {/* 2. Interviewer Notes (INTERVIEWER MODE ONLY) */}
        {viewMode === 'interviewer' && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <label className="font-bold text-slate-700 text-xs flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-purple-600" />
                <span>Interviewer Notes & Observations</span>
              </label>
              <button
                onClick={() => onSaveNotes(question.id)}
                disabled={currentInputs.savingNotes}
                className="text-xs font-semibold text-purple-600 hover:text-purple-700 flex items-center gap-1 cursor-pointer disabled:opacity-50"
              >
                {currentInputs.savedNotes ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-600 font-bold">Saved!</span>
                  </>
                ) : (
                  <>
                    <Save className="w-3 h-3" />
                    <span>{currentInputs.savingNotes ? 'Saving...' : 'Save Notes'}</span>
                  </>
                )}
              </button>
            </div>
            <textarea
              rows={2}
              placeholder="Record private evaluation notes, key strengths, or observed technical gaps..."
              value={currentInputs.notes}
              onChange={(e) => {
                const val = e.target.value;
                setInputs((prev: any) => ({
                  ...prev,
                  [question.id]: { ...prev[question.id], notes: val }
                }));
              }}
              className="w-full text-xs p-3 rounded-xl border border-purple-200 bg-purple-50/20 focus:bg-white focus:border-purple-500 focus:outline-none transition-all placeholder-slate-400"
            />
          </div>
        )}
      </div>
    </div>
  );
}
