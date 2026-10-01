import { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Award, 
  ArrowRight, 
  ArrowLeft, 
  RefreshCw, 
  ShieldCheck, 
  CheckCircle2, 
  HelpCircle, 
  AlertCircle, 
  ExternalLink, 
  FileText, 
  Code, 
  Layers, 
  X, 
  BrainCircuit, 
  GitBranch, 
  Search, 
  Briefcase, 
  Info,
  Check,
  AlertTriangle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import CandidatePipelineHeader from '../components/CandidatePipelineHeader';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

interface SkillItem {
  id: number;
  skill_name: string;
  is_required: boolean;
  is_preferred: boolean;
  resume_claim_present: boolean;
  claim_status?: 'Claimed' | 'Not Claimed';
  github_evidence?: 'Retrieved' | 'None';
  assessment_status?: 'Passed' | 'Partial' | 'Needs Improvement' | 'Not Tested';
  evidence_strength?: 'Strong' | 'Moderate' | 'Limited' | 'Unverified';
  proof_sources?: string[];
  github_signals?: any[];
  claims_count: number;
  evidence_count: number;
  retrieved_evidence_count: number;
  assessment_percentage: number | null;
  assessment_label: string;
  evidence_level: 'Strong Evidence' | 'Good Evidence' | 'Moderate Evidence' | 'Limited Evidence' | 'Needs Verification';
  job_group: 'Well Supported' | 'Partially Supported' | 'Needs Further Verification' | 'Not Demonstrated Yet';
  explanation: string;
  next_verification_step: string | null;
  sources_breakdown: {
    resume_claims: any[];
    projects: any[];
    certificates: any[];
    github_urls: any[];
    github_signals?: any[];
    supporting_documents: any[];
    assessment: any | null;
  };
  graph_data: {
    skill: string;
    nodes: any[];
    edges: any[];
  };
}

interface ProfileResponse {
  analysis_id: number;
  candidate_id: number;
  candidate_name: string;
  job_id: number;
  job_title: string;
  job_company: string;
  profile_status: string;
  pipeline_position: {
    resume_analysis: string;
    evidence_verification: string;
    skill_assessment: string;
    verified_skill_profile: string;
    interview_intelligence: string;
  };
  banner_message: string;
  summary: {
    total_skills: number;
    strong_evidence_count: number;
    good_evidence_count: number;
    moderate_evidence_count: number;
    limited_evidence_count: number;
    needs_verification_count: number;
    not_demonstrated_count: number;
  };
  job_skill_groups: {
    [key: string]: SkillItem[];
  };
  skills: SkillItem[];
  disclaimer: string;
}

export default function SkillProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { activeAnalysisId, setActiveAnalysis } = useAnalysis();

  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [recomputing, setRecomputing] = useState(false);
  const [showRecomputeModal, setShowRecomputeModal] = useState(false);
  const [analysesList, setAnalysesList] = useState<any[]>([]);
  const [selectedGraphSkill, setSelectedGraphSkill] = useState<SkillItem | null>(null);
  const [selectedGraphNode, setSelectedGraphNode] = useState<any | null>(null);
  const [activeGroupTab, setActiveGroupTab] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const currentId = id || activeAnalysisId;

  const fetchProfile = (analysisId: number | string) => {
    setLoading(true);
    axios.get(`${API_BASE_URL}/api/skill-profile/${analysisId}`)
      .then(res => {
        setProfile(res.data);
        setLoading(false);
        if (res.data.candidate_name) {
          setActiveAnalysis(Number(analysisId), {
            name: res.data.candidate_name,
            jobTitle: res.data.job_title || 'Target Job',
            candidateId: res.data.candidate_id
          });
        }
      })
      .catch(err => {
        console.error('Error fetching skill profile:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    if (id) {
      fetchProfile(id);
    } else if (activeAnalysisId) {
      navigate(`/skill-profile/${activeAnalysisId}`, { replace: true });
    } else {
      // No active ID: fetch available analyses
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

  const handleRecompute = () => {
    if (!currentId) return;
    setRecomputing(true);
    axios.post(`${API_BASE_URL}/api/skill-profile/${currentId}/recompute`)
      .then(res => {
        setProfile(res.data);
        setRecomputing(false);
      })
      .catch(err => {
        console.error('Recomputation error:', err);
        setRecomputing(false);
      });
  };

  // Helper colors for Evidence Level badges
  const getEvidenceLevelBadge = (level: string) => {
    switch (level) {
      case 'Strong Evidence':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Strong Evidence
          </span>
        );
      case 'Good Evidence':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
            Good Evidence
          </span>
        );
      case 'Moderate Evidence':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800 border border-indigo-300">
            <Info className="w-3.5 h-3.5 text-indigo-600" />
            Moderate Evidence
          </span>
        );
      case 'Limited Evidence':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            Limited Evidence
          </span>
        );
      case 'Needs Verification':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-300">
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
            Needs Verification
          </span>
        );
    }
  };

  const [openExplanations, setOpenExplanations] = useState<Record<string, boolean>>({});

  const toggleExplanation = (skillName: string) => {
    setOpenExplanations(prev => ({
      ...prev,
      [skillName]: prev[skillName] === undefined ? false : !prev[skillName]
    }));
  };

  const isExplanationOpen = (skillName: string) => {
    return openExplanations[skillName] !== false; // default open for transparency
  };

  const getStrengthBadge = (strength?: string) => {
    const s = strength || 'Unverified';
    if (s === 'Strong') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-300 shadow-2xs">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          Strong
        </span>
      );
    }
    if (s === 'Moderate' || s === 'Good') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-300 shadow-2xs">
          <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
          Moderate
        </span>
      );
    }
    if (s === 'Limited') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-300 shadow-2xs">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
          Limited
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-300 shadow-2xs">
        <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
        Unverified
      </span>
    );
  };

  // Access status pill
  const getAccessStatusBadge = (status?: string) => {
    if (!status) return null;
    const clean = status.toLowerCase();
    if (clean === 'retrieved') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          Retrieved & Inspected
        </span>
      );
    }
    if (clean === 'submitted_only') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
          Submitted Only
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
        Retrieval Failed
      </span>
    );
  };

  // Filter skills by search query and active tab
  const filteredSkills = useMemo(() => {
    if (!profile) return [];
    let list = profile.skills;
    if (activeGroupTab !== 'all') {
      list = list.filter(s => s.job_group === activeGroupTab);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(s => 
        s.skill_name.toLowerCase().includes(q) ||
        s.explanation.toLowerCase().includes(q) ||
        s.evidence_level.toLowerCase().includes(q)
      );
    }
    return list;
  }, [profile, activeGroupTab, searchQuery]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        <p className="text-slate-600 font-medium text-sm">Aggregating multi-source evidence and generating skill profile...</p>
      </div>
    );
  }

  // If active analysis exists but profile is not generated or accessible
  if (currentId && !profile) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mx-auto shadow-xs">
          <Award className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Verified Skill Profile</h2>
        <p className="text-sm text-slate-600 max-w-md mx-auto">
          Complete the required earlier stages to generate the skill profile.
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <Link
            to={`/assessment/${currentId}`}
            className="px-5 py-2.5 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 shadow-xs flex items-center gap-1.5"
          >
            <span>Go to Skill Assessment</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <Link
            to={`/evidence/${currentId}`}
            className="px-4 py-2.5 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-200"
          >
            <span>Evidence Center</span>
          </Link>
        </div>
      </div>
    );
  }

  // 1. If no active analysis, display candidate selection screen
  if (!currentId) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-12">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Verified Skill Profile — Select Candidate</h2>
              <p className="text-slate-500 text-sm mt-0.5">Select a candidate analysis to review their multi-source verified skill profile.</p>
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
                      navigate(`/skill-profile/${a.id}`);
                    }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition-all shadow-xs flex items-center gap-1.5"
                  >
                    <span>Open Skill Profile</span>
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

  if (!profile) return null;

  const { summary } = profile;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* 2. Top Candidate Pipeline Header */}
      <CandidatePipelineHeader 
        analysisId={currentId} 
        candidateName={profile.candidate_name} 
        jobTitle={profile.job_title} 
      />

      {/* 3. Hero Header & Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Verified Skill Profile
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                Decision Support Active
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Verified Skill Profile & Evidence Graph
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-3xl leading-relaxed">
              {profile.banner_message}
            </p>
          </div>

          <div className="flex items-center gap-2.5 shrink-0">
            <button
              onClick={() => setShowRecomputeModal(true)}
              disabled={recomputing}
              className="px-4 py-2.5 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-xs cursor-pointer disabled:opacity-50"
              title="Recalculates deterministic evidence level rules from stored data"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${recomputing ? 'animate-spin text-blue-600' : 'text-slate-500'}`} />
              <span>{recomputing ? 'Recalculating...' : 'Recompute Skill Profile'}</span>
            </button>
            <Link
              to={`/interview/${currentId}`}
              className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
            >
              <span>Next: Interview Intelligence</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Top Factual Summary Counts - Strictly Non-Ranking */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-5">
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Skills Analyzed</p>
            <p className="text-2xl font-extrabold text-slate-900 mt-1">{summary.total_skills}</p>
          </div>
          <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-3 text-center">
            <p className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Strong Evidence</p>
            <p className="text-2xl font-extrabold text-emerald-800 mt-1">{summary.strong_evidence_count}</p>
          </div>
          <div className="bg-blue-50/60 border border-blue-200 rounded-xl p-3 text-center">
            <p className="text-[11px] font-bold text-blue-700 uppercase tracking-wider">Good Evidence</p>
            <p className="text-2xl font-extrabold text-blue-800 mt-1">{summary.good_evidence_count}</p>
          </div>
          <div className="bg-indigo-50/60 border border-indigo-200 rounded-xl p-3 text-center">
            <p className="text-[11px] font-bold text-indigo-700 uppercase tracking-wider">Moderate Evidence</p>
            <p className="text-2xl font-extrabold text-indigo-800 mt-1">{summary.moderate_evidence_count}</p>
          </div>
          <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-3 text-center">
            <p className="text-[11px] font-bold text-amber-700 uppercase tracking-wider">Limited Evidence</p>
            <p className="text-2xl font-extrabold text-amber-800 mt-1">{summary.limited_evidence_count}</p>
          </div>
          <div className="bg-slate-100/70 border border-slate-200 rounded-xl p-3 text-center">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Needs Verification</p>
            <p className="text-2xl font-extrabold text-slate-700 mt-1">{summary.needs_verification_count}</p>
          </div>
        </div>

        {/* Guardrail Disclaimer Alert */}
        <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-2.5 text-xs text-slate-600">
          <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="font-semibold text-slate-800">Deterministic Decision Support:</strong> ProofHire synthesizes documented evidence without predicting personality, assigning subjective candidate scores, or asserting absolute truth claims. Assessment labels strictly reflect demonstrated performance on the administered evaluation.
          </p>
        </div>
      </div>

      {/* 4. Section: JOB-RELATED SKILL EVIDENCE (Job Skill Gap View) */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-600" />
              JOB-RELATED SKILL EVIDENCE
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Categorized according to empirical multi-source evidence depth and assessment performance.
            </p>
          </div>

          {/* Group Filter Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs font-semibold bg-slate-100 p-1 rounded-xl">
            <button
              onClick={() => setActiveGroupTab('all')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeGroupTab === 'all' 
                  ? 'bg-white text-slate-900 shadow-xs' 
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Skills ({profile.skills.length})
            </button>
            <button
              onClick={() => setActiveGroupTab('Well Supported')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeGroupTab === 'Well Supported' 
                  ? 'bg-emerald-600 text-white shadow-xs' 
                  : 'text-slate-600 hover:text-emerald-700'
              }`}
            >
              Well Supported ({profile.job_skill_groups['Well Supported']?.length || 0})
            </button>
            <button
              onClick={() => setActiveGroupTab('Partially Supported')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeGroupTab === 'Partially Supported' 
                  ? 'bg-indigo-600 text-white shadow-xs' 
                  : 'text-slate-600 hover:text-indigo-700'
              }`}
            >
              Partially Supported ({profile.job_skill_groups['Partially Supported']?.length || 0})
            </button>
            <button
              onClick={() => setActiveGroupTab('Needs Further Verification')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeGroupTab === 'Needs Further Verification' 
                  ? 'bg-amber-600 text-white shadow-xs' 
                  : 'text-slate-600 hover:text-amber-700'
              }`}
            >
              Needs Further Verification ({profile.job_skill_groups['Needs Further Verification']?.length || 0})
            </button>
            <button
              onClick={() => setActiveGroupTab('Not Demonstrated Yet')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeGroupTab === 'Not Demonstrated Yet' 
                  ? 'bg-slate-700 text-white shadow-xs' 
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Not Demonstrated Yet ({profile.job_skill_groups['Not Demonstrated Yet']?.length || 0})
            </button>
          </div>
        </div>

        {/* Section 10 Disclaimer */}
        <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-3.5 flex items-start gap-2.5 text-xs text-amber-900">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <strong className="font-bold">Important Evaluation Standard:</strong>{' '}
            <span>
              &ldquo;Not Demonstrated Yet&rdquo; means ProofHire currently lacks sufficient documented demonstration in submitted materials and assessments. It does <strong>NOT</strong> mean the candidate does not possess the skill.
            </span>
          </div>
        </div>

        {/* Search bar */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            type="text"
            placeholder="Search skills, evidence notes, or explanation keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-transparent outline-none text-slate-800 placeholder-slate-400"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="text-slate-400 hover:text-slate-600">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* 5. Skill Profile Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredSkills.map(skill => {
            const strengthVal = skill.evidence_strength || (
              skill.evidence_level?.includes('Strong') ? 'Strong' :
              skill.evidence_level?.includes('Moderate') ? 'Moderate' :
              skill.evidence_level?.includes('Good') ? 'Moderate' :
              skill.evidence_level?.includes('Limited') ? 'Limited' : 'Unverified'
            );

            const claimVal = skill.claim_status || (skill.resume_claim_present ? 'Claimed' : 'Not Claimed');
            const githubVal = skill.github_evidence || (
              (skill.github_signals && skill.github_signals.length > 0) ? 'Retrieved' : 'None'
            );
            const assessVal = skill.assessment_status || (
              skill.assessment_percentage !== null
                ? (skill.assessment_percentage >= 70 ? 'Passed' : skill.assessment_percentage >= 50 ? 'Partial' : 'Needs Improvement')
                : 'Not Tested'
            );

            return (
              <div 
                key={skill.id || skill.skill_name}
                className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:border-blue-300 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3.5">
                  {/* Header: Skill Name & Evidence Strength Badge */}
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-extrabold text-slate-900 tracking-tight">
                          {skill.skill_name}
                        </h3>
                        {skill.is_required && (
                          <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-bold rounded">
                            Required
                          </span>
                        )}
                        {skill.is_preferred && (
                          <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 border border-slate-200 text-[10px] font-bold rounded">
                            Preferred
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 font-medium mt-0.5">
                        Group: <span className="text-slate-700 font-semibold">{skill.job_group}</span>
                      </p>
                    </div>
                    <div>
                      {getStrengthBadge(strengthVal)}
                    </div>
                  </div>

                  {/* 2. Deterministic Skill Proof Card Matrix */}
                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50/80 p-3 rounded-xl border border-slate-200/70">
                    {/* Claim Status */}
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        Claim Status
                      </span>
                      <div className="flex items-center gap-1 font-semibold">
                        {claimVal === 'Claimed' ? (
                          <span className="text-emerald-700 flex items-center gap-1 text-xs">
                            <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                            Claimed
                          </span>
                        ) : (
                          <span className="text-slate-500 flex items-center gap-1 text-xs">
                            <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            Not Claimed
                          </span>
                        )}
                      </div>
                    </div>

                    {/* GitHub Evidence */}
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        GitHub Evidence
                      </span>
                      <div className="flex items-center gap-1 font-semibold">
                        {githubVal === 'Retrieved' ? (
                          <span className="text-indigo-700 flex items-center gap-1 text-xs font-bold">
                            <Check className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                            Retrieved
                          </span>
                        ) : (
                          <span className="text-slate-500 flex items-center gap-1 text-xs">
                            <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            None
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Assessment */}
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        Assessment
                      </span>
                      <div className="flex items-center gap-1 font-semibold text-xs">
                        {assessVal === 'Passed' && (
                          <span className="text-emerald-700 flex items-center gap-1">
                            <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" /> Passed
                          </span>
                        )}
                        {assessVal === 'Partial' && (
                          <span className="text-amber-700 flex items-center gap-1">
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" /> Partial
                          </span>
                        )}
                        {assessVal === 'Needs Improvement' && (
                          <span className="text-rose-700 flex items-center gap-1">
                            <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" /> Needs Improvement
                          </span>
                        )}
                        {assessVal === 'Not Tested' && (
                          <span className="text-slate-500 flex items-center gap-1">
                            <X className="w-3.5 h-3.5 text-slate-400 shrink-0" /> Not Tested
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Evidence Strength */}
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        Evidence Strength
                      </span>
                      <div className="flex items-center gap-1 font-bold text-xs">
                        <span className={
                          strengthVal === 'Strong' ? 'text-emerald-700' :
                          strengthVal === 'Moderate' ? 'text-blue-700' :
                          strengthVal === 'Limited' ? 'text-amber-700' : 'text-slate-600'
                        }>
                          {strengthVal}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 3. Proof Sources Section */}
                  <div className="bg-slate-50/90 border border-slate-200 rounded-xl p-3 text-xs space-y-1.5">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                      Proof Sources
                    </span>
                    <div className="space-y-1 font-mono text-[11px]">
                      {skill.proof_sources && skill.proof_sources.length > 0 ? (
                        skill.proof_sources.map((src, sIdx) => {
                          const isStrengthLine = src.startsWith('Evidence Strength:');
                          const isNegative = src.startsWith('✗');
                          return (
                            <div 
                              key={sIdx}
                              className={`flex items-start gap-1.5 ${
                                isStrengthLine 
                                  ? 'font-bold font-sans pt-1 border-t border-slate-200/80 text-slate-900 text-xs' 
                                  : isNegative 
                                    ? 'text-slate-400 font-sans' 
                                    : 'text-slate-800'
                              }`}
                            >
                              <span>{src}</span>
                            </div>
                          );
                        })
                      ) : (
                        <div className="text-slate-500 italic font-sans text-xs">
                          {claimVal === 'Claimed' ? '✓ Resume claim' : '✗ No resume claim'}<br />
                          {githubVal === 'Retrieved' ? '✓ GitHub evidence retrieved' : '✗ No GitHub repository evidence'}<br />
                          {assessVal !== 'Not Tested' ? `✓ Assessment: ${assessVal}` : '✗ Assessment not tested'}<br />
                          <span className="font-bold pt-1 block text-slate-900">Evidence Strength: {strengthVal}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 6. Explainability: 'Why this skill rating?' */}
                  <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
                    <button
                      type="button"
                      onClick={() => toggleExplanation(skill.skill_name)}
                      className="w-full px-3 py-2 bg-slate-50/80 hover:bg-slate-100 flex items-center justify-between text-left text-xs font-semibold text-slate-700 transition-colors cursor-pointer"
                    >
                      <span className="flex items-center gap-1.5 text-blue-700 font-bold">
                        <HelpCircle className="w-3.5 h-3.5 text-blue-600" />
                        Why this skill rating?
                      </span>
                      {isExplanationOpen(skill.skill_name) ? (
                        <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </button>

                    {isExplanationOpen(skill.skill_name) && (
                      <div className="p-3 text-[11px] text-slate-600 leading-relaxed border-t border-slate-100 bg-white">
                        <p>{skill.explanation}</p>
                      </div>
                    )}
                  </div>

                  {/* Practical Next Step if Needs Verification */}
                  {skill.next_verification_step && (
                    <div className="text-xs bg-amber-50/50 border border-amber-200 rounded-xl p-2.5 space-y-0.5">
                      <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider flex items-center gap-1">
                        <HelpCircle className="w-3 h-3 text-amber-600" />
                        Next Verification Action
                      </span>
                      <p className="text-slate-700 text-[11px] leading-relaxed">
                        &rarr; {skill.next_verification_step}
                      </p>
                    </div>
                  )}
                </div>

                {/* View Skill Proof Action */}
                <div className="pt-3.5 mt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 font-medium">
                    {skill.graph_data?.nodes?.length || 1} connected evidence nodes
                  </span>
                  <button
                    onClick={() => {
                      setSelectedGraphSkill(skill);
                      setSelectedGraphNode(skill.graph_data?.nodes?.[0] || null);
                    }}
                    className="px-3.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <GitBranch className="w-3.5 h-3.5 text-blue-600" />
                    <span>View Skill Proof</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {filteredSkills.length === 0 && (
          <div className="text-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-200">
            <p className="text-slate-500 text-sm">No skills found matching your filter criteria.</p>
          </div>
        )}
      </div>

      {/* 6. Section 15: Pipeline Step Completion & Connection to Phase 5 */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Evaluation Journey</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Profile Verified
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900">
            Proceed to Interview Intelligence
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Use verified skill evidence and identified verification gaps to structure objective interview questions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to={`/assessment/${currentId}`}
            className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Skill Assessment</span>
          </Link>
          <Link
            to={`/interview/${currentId}`}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-sm"
          >
            <span>Continue to Interview Intelligence</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* 7. Interactive Skill Proof Graph Modal */}
      {selectedGraphSkill && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
                  <GitBranch className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-extrabold text-slate-900 text-lg">
                      Skill Proof Graph &mdash; {selectedGraphSkill.skill_name}
                    </h3>
                    {getEvidenceLevelBadge(selectedGraphSkill.evidence_level)}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Deterministic visual connection between target skill and empirical stored evidence.
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setSelectedGraphSkill(null);
                  setSelectedGraphNode(null);
                }}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body: Interactive Node-Edge Graph & Details Drawer */}
            <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Visual Graph Viewport (Tree View) */}
              <div className="lg:col-span-2 bg-slate-900 rounded-2xl p-6 text-white flex flex-col justify-between relative overflow-hidden shadow-inner min-h-[380px]">
                {/* Background Grid Pattern */}
                <div className="absolute inset-0 bg-[radial-gradient(#334155_1px,transparent_1px)] [background-size:16px_16px] opacity-40"></div>

                {/* Graph Title Watermark */}
                <div className="relative z-10 flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-3">
                  <span className="font-mono">GRAPH ENGINE: STORED_EVIDENCE_ONLY</span>
                  <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded text-[10px]">
                    {selectedGraphSkill.graph_data.nodes.length} Stored Nodes
                  </span>
                </div>

                {/* Interactive Hierarchical Tree Layout */}
                <div className="relative z-10 my-auto py-4 flex flex-col items-center space-y-3 w-full">
                  {/* Extract nodes by type */}
                  {(() => {
                    const candNode = selectedGraphSkill.graph_data.nodes.find(n => n.type === 'Candidate');
                    const skillNode = selectedGraphSkill.graph_data.nodes.find(n => n.type === 'Skill');
                    const claimNodes = selectedGraphSkill.graph_data.nodes.filter(n => n.type === 'Resume Claim');
                    const repoNodes = selectedGraphSkill.graph_data.nodes.filter(n => n.type === 'GitHub Repository');
                    const signalNodes = selectedGraphSkill.graph_data.nodes.filter(n => n.type === 'GitHub Signal');
                    const assessNode = selectedGraphSkill.graph_data.nodes.find(n => n.type === 'Skill Assessment');
                    const scoreNode = selectedGraphSkill.graph_data.nodes.find(n => n.type === 'Assessment Score');
                    const otherNodes = selectedGraphSkill.graph_data.nodes.filter(n => ['Project', 'Supporting Document', 'Certificate'].includes(n.type));

                    return (
                      <>
                        {/* 1. Candidate Node (Top) */}
                        <div
                          onClick={() => setSelectedGraphNode(candNode || selectedGraphSkill.graph_data.nodes[0])}
                          className={`cursor-pointer px-5 py-2 rounded-xl border transition-all flex items-center gap-2.5 shadow-md ${
                            selectedGraphNode?.id === candNode?.id
                              ? 'bg-slate-800 border-white text-white scale-105 ring-2 ring-blue-500/50'
                              : 'bg-slate-900/90 border-slate-700 text-slate-200 hover:border-slate-500'
                          }`}
                        >
                          <Briefcase className="w-4 h-4 text-blue-400" />
                          <div className="text-left">
                            <p className="text-[9px] uppercase font-bold text-slate-400">Candidate</p>
                            <p className="font-extrabold text-xs tracking-tight">{candNode?.label || profile.candidate_name || 'Candidate'}</p>
                          </div>
                        </div>

                        {/* Downward Connector */}
                        <div className="flex flex-col items-center -my-1 text-slate-500 text-xs">
                          <div className="w-0.5 h-2.5 bg-slate-700"></div>
                          <span>↓</span>
                        </div>

                        {/* 2. Target Skill Node (Middle) */}
                        <div 
                          onClick={() => setSelectedGraphNode(skillNode || selectedGraphSkill.graph_data.nodes[0])}
                          className={`cursor-pointer px-6 py-2.5 rounded-2xl border-2 transition-all shadow-lg flex items-center gap-3 ${
                            (selectedGraphNode?.id === skillNode?.id || selectedGraphNode?.id === 'skill_root')
                              ? 'bg-blue-600 border-white text-white scale-105 shadow-blue-500/25 ring-2 ring-blue-400/40'
                              : 'bg-slate-800 border-blue-400 text-white hover:border-white'
                          }`}
                        >
                          <Award className="w-5 h-5 text-blue-300" />
                          <div>
                            <p className="text-[10px] uppercase font-bold text-blue-200">Target Skill</p>
                            <h4 className="font-extrabold text-base tracking-tight">{selectedGraphSkill.skill_name}</h4>
                          </div>
                        </div>

                        {/* Connector down to branches */}
                        <div className="w-0.5 h-3 bg-slate-700"></div>

                        {/* 3. Three Branches: Resume Claim | GitHub Repository (-> Signal) | Skill Assessment (-> Score) */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full max-w-2xl text-left">
                          {/* Branch A: Resume Claim */}
                          <div className="flex flex-col items-center space-y-2">
                            <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                              ├── Resume Claim
                            </div>
                            {claimNodes.length > 0 ? (
                              claimNodes.map(cNode => {
                                const isSelected = selectedGraphNode?.id === cNode.id;
                                return (
                                  <div
                                    key={cNode.id}
                                    onClick={() => setSelectedGraphNode(cNode)}
                                    className={`w-full cursor-pointer px-3 py-2 rounded-xl border transition-all text-xs flex items-center gap-2 ${
                                      isSelected
                                        ? 'bg-slate-800 border-white text-white scale-105 shadow-md'
                                        : 'bg-slate-900/90 border-emerald-500/70 text-slate-200 hover:bg-slate-800'
                                    }`}
                                  >
                                    <FileText className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                                    <div className="overflow-hidden">
                                      <p className="font-semibold truncate">{cNode.label}</p>
                                      <p className="text-[10px] text-emerald-400/80">{cNode.status}</p>
                                    </div>
                                  </div>
                                );
                              })
                            ) : (
                              <div className="text-[11px] text-slate-500 italic">No claim detected</div>
                            )}
                          </div>

                          {/* Branch B: GitHub Repository & Signals */}
                          <div className="flex flex-col items-center space-y-2">
                            <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                              ├── GitHub Repository
                            </div>
                            {repoNodes.length > 0 ? (
                              repoNodes.map(rNode => {
                                const isSelected = selectedGraphNode?.id === rNode.id;
                                return (
                                  <div key={rNode.id} className="w-full space-y-1.5 flex flex-col items-center">
                                    <div
                                      onClick={() => setSelectedGraphNode(rNode)}
                                      className={`w-full cursor-pointer px-3 py-2 rounded-xl border transition-all text-xs flex items-center gap-2 ${
                                        isSelected
                                          ? 'bg-slate-800 border-white text-white scale-105 shadow-md'
                                          : 'bg-slate-900/90 border-indigo-500/70 text-slate-200 hover:bg-slate-800'
                                      }`}
                                    >
                                      <Code className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                                      <div className="overflow-hidden">
                                        <p className="font-semibold truncate">{rNode.label}</p>
                                        <p className="text-[10px] text-indigo-400/80">{rNode.status}</p>
                                      </div>
                                    </div>

                                    {/* Connected Detected Signals */}
                                    {signalNodes.length > 0 && (
                                      <div className="w-full pl-2.5 border-l-2 border-slate-700 space-y-1 flex flex-col items-start">
                                        <span className="text-[9px] font-mono text-slate-400">└── signals:</span>
                                        {signalNodes.map(sNode => {
                                          const isSigSelected = selectedGraphNode?.id === sNode.id;
                                          return (
                                            <div
                                              key={sNode.id}
                                              onClick={() => setSelectedGraphNode(sNode)}
                                              className={`w-full cursor-pointer px-2 py-1 rounded-lg border transition-all text-[11px] flex items-center gap-1.5 ${
                                                isSigSelected
                                                  ? 'bg-slate-800 border-cyan-400 text-white shadow-xs'
                                                  : 'bg-slate-950/80 border-cyan-500/40 text-cyan-200 hover:bg-slate-800'
                                              }`}
                                            >
                                              <CheckCircle2 className="w-3 h-3 text-cyan-400 shrink-0" />
                                              <span className="truncate">{sNode.label}</span>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    )}
                                  </div>
                                );
                              })
                            ) : (
                              <div className="text-[11px] text-slate-500 italic">No repository evidence</div>
                            )}
                          </div>

                          {/* Branch C: Skill Assessment & Score */}
                          <div className="flex flex-col items-center space-y-2">
                            <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                              └── Skill Assessment
                            </div>
                            {assessNode ? (
                              <div className="w-full space-y-1.5 flex flex-col items-center">
                                <div
                                  onClick={() => setSelectedGraphNode(assessNode)}
                                  className={`w-full cursor-pointer px-3 py-2 rounded-xl border transition-all text-xs flex items-center gap-2 ${
                                    selectedGraphNode?.id === assessNode.id
                                      ? 'bg-slate-800 border-white text-white scale-105 shadow-md'
                                      : 'bg-slate-900/90 border-purple-500/70 text-slate-200 hover:bg-slate-800'
                                  }`}
                                >
                                  <BrainCircuit className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                                  <div className="overflow-hidden">
                                    <p className="font-semibold truncate">{assessNode.label}</p>
                                    <p className="text-[10px] text-purple-400/80">{assessNode.status}</p>
                                  </div>
                                </div>

                                {scoreNode && (
                                  <div className="w-full pl-2.5 border-l-2 border-slate-700 flex flex-col items-start">
                                    <span className="text-[9px] font-mono text-slate-400 mb-0.5">└── score:</span>
                                    <div
                                      onClick={() => setSelectedGraphNode(scoreNode)}
                                      className={`w-full cursor-pointer px-2 py-1 rounded-lg border transition-all text-[11px] flex items-center gap-1.5 ${
                                        selectedGraphNode?.id === scoreNode.id
                                          ? 'bg-slate-800 border-emerald-400 text-white shadow-xs'
                                          : 'bg-slate-950/80 border-emerald-500/40 text-emerald-200 hover:bg-slate-800'
                                      }`}
                                    >
                                      <Award className="w-3 h-3 text-emerald-400 shrink-0" />
                                      <span className="font-bold font-mono">{scoreNode.label}</span>
                                    </div>
                                  </div>
                                )}
                              </div>
                            ) : (
                              <div className="text-[11px] text-slate-500 italic">Not tested</div>
                            )}
                          </div>
                        </div>

                        {/* Optional other nodes (Projects, Certs, Docs) */}
                        {otherNodes.length > 0 && (
                          <div className="pt-2 flex flex-wrap items-center justify-center gap-2 max-w-xl">
                            {otherNodes.map(oNode => {
                              const isSelected = selectedGraphNode?.id === oNode.id;
                              return (
                                <div
                                  key={oNode.id}
                                  onClick={() => setSelectedGraphNode(oNode)}
                                  className={`cursor-pointer px-3 py-1.5 rounded-lg border transition-all text-[11px] flex items-center gap-1.5 ${
                                    isSelected
                                      ? 'bg-slate-800 border-white text-white shadow-xs'
                                      : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800'
                                  }`}
                                >
                                  {oNode.type === 'Project' && <Code className="w-3 h-3 text-blue-400" />}
                                  {oNode.type === 'Certificate' && <Award className="w-3 h-3 text-amber-400" />}
                                  {oNode.type === 'Supporting Document' && <Layers className="w-3 h-3 text-slate-400" />}
                                  <span className="truncate max-w-[120px]">{oNode.label}</span>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>

                {/* Footer hint */}
                <div className="relative z-10 text-[11px] text-slate-400 flex items-center justify-between border-t border-slate-800 pt-3">
                  <span>Click any node to inspect evidence attributes</span>
                  <span className="text-slate-500 font-mono">Real DB Records</span>
                </div>
              </div>

              {/* Right Side: Selected Node Inspector Drawer */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 flex flex-col justify-between space-y-4">
                <div className="space-y-4">
                  <div className="border-b border-slate-200 pb-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Node Details
                    </span>
                    <h4 className="text-base font-extrabold text-slate-900 mt-1">
                      {selectedGraphNode ? selectedGraphNode.label : selectedGraphSkill.skill_name}
                    </h4>
                    <p className="text-xs text-slate-500 font-mono mt-0.5">
                      Type: {selectedGraphNode?.type || 'Skill Root'}
                    </p>
                  </div>

                  {selectedGraphNode ? (
                    <div className="space-y-3 text-xs">
                      {selectedGraphNode.evidence_access_status && (
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                            Access Status
                          </p>
                          {getAccessStatusBadge(selectedGraphNode.evidence_access_status)}
                        </div>
                      )}

                      {selectedGraphNode.percentage !== undefined && (
                        <div className="bg-white p-3 rounded-xl border border-slate-200 space-y-1">
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            Demonstrated Performance
                          </p>
                          <p className="text-lg font-black text-blue-600 font-mono">
                            {selectedGraphNode.percentage.toFixed(1)}%
                          </p>
                          <p className="text-[11px] font-medium text-slate-700">
                            {selectedGraphNode.demonstration_level}
                          </p>
                          <p className="text-[10px] text-slate-400">
                            Points: {selectedGraphNode.score} / {selectedGraphNode.max_score}
                          </p>
                        </div>
                      )}

                      {selectedGraphNode.title && (
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                            Recorded Content
                          </p>
                          <p className="text-slate-700 text-xs bg-white p-3 rounded-xl border border-slate-200 leading-relaxed font-sans">
                            {selectedGraphNode.title}
                          </p>
                        </div>
                      )}

                      {selectedGraphNode.source_section && (
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">
                            Source Document Section
                          </p>
                          <span className="text-slate-600 font-medium">
                            {selectedGraphNode.source_section}
                          </span>
                        </div>
                      )}

                      {selectedGraphNode.url && (
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                            Verified Source URL
                          </p>
                          <a 
                            href={selectedGraphNode.url} 
                            target="_blank" 
                            rel="noreferrer" 
                            className="text-blue-600 hover:underline flex items-center gap-1 font-mono break-all text-[11px]"
                          >
                            <span>{selectedGraphNode.url}</span>
                            <ExternalLink className="w-3 h-3 shrink-0" />
                          </a>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">Select any node on the graph to inspect stored evidence facts.</p>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-200 text-[11px] text-slate-400 flex items-center justify-between">
                  <span>Decision Support Node</span>
                  <button
                    onClick={() => {
                      setSelectedGraphSkill(null);
                      setSelectedGraphNode(null);
                    }}
                    className="text-blue-600 font-semibold hover:underline"
                  >
                    Close Inspector
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Confirmation Modal for Recomputing */}
      {showRecomputeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Recompute Skill Profile</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              This will replace/recompute the current generated output. Continue?
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowRecomputeModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowRecomputeModal(false);
                  handleRecompute();
                }}
                disabled={recomputing}
                className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-xs cursor-pointer flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${recomputing ? 'animate-spin' : ''}`} />
                <span>Continue</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
