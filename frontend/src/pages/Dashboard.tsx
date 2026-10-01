import { useEffect, useState } from 'react';
import { Users, Briefcase, FileSearch, ArrowRight, ShieldCheck, PlusCircle, Sparkles } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

export default function Dashboard() {
  const [stats, setStats] = useState({ candidates: 0, jobs: 0, analyses: 0 });
  const [recentAnalyses, setRecentAnalyses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { activeAnalysisId, activeCandidate, setActiveAnalysis } = useAnalysis();
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE_URL}/api/candidates`).catch(() => ({ data: [] })),
      axios.get(`${API_BASE_URL}/api/jobs`).catch(() => ({ data: [] })),
      axios.get(`${API_BASE_URL}/api/analyses`).catch(() => ({ data: [] }))
    ]).then(([candRes, jobsRes, analysesRes]) => {
      setStats({
        candidates: candRes.data.length || 0,
        jobs: jobsRes.data.length || 0,
        analyses: analysesRes.data.length || 0,
      });
      setRecentAnalyses(analysesRes.data || []);
      setLoading(false);
    }).catch(err => {
      console.error('Error loading dashboard stats:', err);
      setLoading(false);
    });
  }, []);

  const handleContinueAnalysis = (analysis: any) => {
    setActiveAnalysis(analysis.id, {
      name: analysis.candidate_name,
      jobTitle: analysis.job_title,
      candidateId: analysis.candidate_id,
      currentStage: analysis.current_stage,
      continueRoute: analysis.continue_route
    });
    // Automatically open the correct stage for this analysis
    const targetRoute = analysis.continue_route || `/analysis/result/${analysis.id}`;
    navigate(targetRoute);
  };

  // Determine stage states for active candidate
  const getDashboardStageState = (stageKey: string): 'Completed' | 'Current' | 'Pending' => {
    if (!activeAnalysisId || !activeCandidate) return 'Pending';
    const stages = activeCandidate.pipelineStages;
    if (stages && (stages as any)[stageKey]) {
      const val = (stages as any)[stageKey];
      if (val === 'completed') return 'Completed';
      if (val === 'current') return 'Current';
      return 'Pending';
    }
    const current = activeCandidate.currentStage || 'Resume Analysis';
    if (stageKey === 'resume') return 'Completed';
    if (stageKey === 'evidence') return current === 'Resume Analysis' ? 'Current' : 'Completed';
    if (stageKey === 'assessment') {
      if (current === 'Skill Assessment') return 'Current';
      if (current === 'Verified Skill Profile' || current === 'Interview Intelligence') return 'Completed';
      return 'Pending';
    }
    if (stageKey === 'profile') {
      if (current === 'Verified Skill Profile') return 'Current';
      if (current === 'Interview Intelligence') return 'Completed';
      return 'Pending';
    }
    if (stageKey === 'interview') {
      return current === 'Interview Intelligence' ? 'Current' : 'Pending';
    }
    return 'Pending';
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Hero Welcome */}
      <div className="bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-700 text-white p-8 rounded-2xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/30 text-blue-100 text-xs font-semibold mb-3 border border-blue-400/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Evidence-Based Hiring Intelligence</span>
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight">ProofHire AI Command Center</h2>
          <p className="text-blue-100 mt-2 max-w-xl text-sm leading-relaxed">
            Verify candidate professional claims with autonomous multi-source evidence extraction, standardized technical assessments, and explainable skill verification.
          </p>
        </div>
        <div className="shrink-0">
          <Link 
            to="/analysis/new" 
            className="inline-flex items-center gap-2 px-6 py-3.5 bg-white text-blue-700 hover:bg-blue-50 font-bold rounded-xl text-sm shadow-md transition-all hover:shadow-lg active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Start New Analysis</span>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Candidates Analyzed" 
          value={loading ? "..." : stats.candidates} 
          subtitle="Profile & skill extractions"
          icon={<Users className="w-6 h-6 text-blue-600" />} 
          link="/candidates"
        />
        <StatCard 
          title="Active Jobs" 
          value={loading ? "..." : stats.jobs} 
          subtitle="Target role specifications"
          icon={<Briefcase className="w-6 h-6 text-indigo-600" />} 
          link="/jobs"
        />
        <StatCard 
          title="Analyses Run" 
          value={loading ? "..." : stats.analyses} 
          subtitle="Verification pipelines tracked"
          icon={<FileSearch className="w-6 h-6 text-emerald-600" />} 
          link="/candidates"
        />
      </div>

      {/* ProofHire Pipeline Visual */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between mb-6 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-lg font-bold text-slate-800">ProofHire Verification Pipeline</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {activeAnalysisId && activeCandidate 
                ? `Active Pipeline Progress for ${activeCandidate.name} (#${activeAnalysisId})` 
                : '5-Stage Explainable Verification Architecture'}
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
            5 Stages
          </span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <PipelineCard 
            step="1" 
            name="Resume Analysis" 
            desc="Extract skills, projects, and professional claims"
            state={getDashboardStageState('resume')}
            link={activeAnalysisId ? `/analysis/result/${activeAnalysisId}` : undefined}
          />
          <PipelineCard 
            step="2" 
            name="Evidence Verification" 
            desc="Inspect GitHub, URLs, and PDFs with integrity guardrails"
            state={getDashboardStageState('evidence')}
            link={activeAnalysisId ? `/evidence/${activeAnalysisId}` : undefined}
          />
          <PipelineCard 
            step="3" 
            name="Skill Assessment" 
            desc="Dynamic personalized technical assessment"
            state={getDashboardStageState('assessment')}
            link={activeAnalysisId && getDashboardStageState('assessment') !== 'Pending' ? `/assessment/${activeAnalysisId}` : undefined}
          />
          <PipelineCard 
            step="4" 
            name="Verified Skill Profile" 
            desc="Explainable multi-source skill proof matrix"
            state={getDashboardStageState('profile')}
            link={activeAnalysisId && getDashboardStageState('profile') !== 'Pending' ? `/skill-profile/${activeAnalysisId}` : undefined}
          />
          <PipelineCard 
            step="5" 
            name="Interview Intelligence" 
            desc="Evidence-anchored probes targeting verification gaps"
            state={getDashboardStageState('interview')}
            link={activeAnalysisId && getDashboardStageState('interview') !== 'Pending' ? `/interview/${activeAnalysisId}` : undefined}
          />
        </div>
      </div>

      {/* Recent Analyses List */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between mb-5 border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-xl font-bold text-slate-800">Recent Analyses</h3>
            <p className="text-xs text-slate-500 mt-0.5">Pick up verification where you left off</p>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {recentAnalyses.length} Total Sessions
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-400 text-sm flex items-center justify-center gap-2">
            <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span>Loading recent candidate analyses...</span>
          </div>
        ) : recentAnalyses.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-sm">
            <p className="font-semibold text-slate-700">No candidate analyses found yet.</p>
            <p className="text-xs mt-1 text-slate-400">Upload a resume and job description to get started.</p>
            <Link 
              to="/analysis/new" 
              className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Start New Analysis</span>
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recentAnalyses.map((item: any) => (
              <div 
                key={item.id} 
                className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50/80 p-3 rounded-xl transition-colors"
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-11 h-11 rounded-xl bg-blue-50 border border-blue-100 text-blue-700 flex items-center justify-center font-bold text-base shadow-xs shrink-0">
                    {item.candidate_name ? item.candidate_name.charAt(0).toUpperCase() : 'C'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-slate-900 text-base">{item.candidate_name}</h4>
                      <span className="text-xs text-slate-400 font-mono">#{item.id}</span>
                    </div>
                    <p className="text-xs text-slate-500 font-medium mt-0.5 flex items-center gap-2">
                      <span className="text-slate-700 font-semibold">{item.job_title}</span>
                      {item.job_company && (
                        <>
                          <span className="text-slate-300">•</span>
                          <span>{item.job_company}</span>
                        </>
                      )}
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-5">
                  <div className="text-left sm:text-right">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Stage</span>
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-md mt-0.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                      <span>{item.current_stage || 'Resume Analysis'}</span>
                    </span>
                  </div>

                  <div className="text-left sm:text-right hidden sm:block">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Last Updated</span>
                    <span className="text-xs text-slate-600 font-medium">
                      {item.last_updated || 'Recently'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleContinueAnalysis(item)}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-xs transition-all shadow-xs flex items-center gap-1.5 active:scale-95 cursor-pointer"
                    >
                      <span>Continue</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle, icon, link }: any) {
  return (
    <Link to={link} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all group">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        <div className="p-2.5 rounded-xl bg-slate-50 group-hover:bg-blue-50 transition-colors">
          {icon}
        </div>
      </div>
      <p className="text-3xl font-extrabold text-slate-900 tracking-tight">{value}</p>
      <p className="text-xs text-slate-400 mt-1 font-medium">{subtitle}</p>
    </Link>
  );
}

function PipelineCard({ step, name, desc, state = 'Pending', link }: any) {
  const isCompleted = state === 'Completed';
  const isCurrent = state === 'Current';
  const isPending = state === 'Pending';

  const cardContent = (
    <div className={`p-4 rounded-xl border text-xs flex flex-col justify-between transition-all h-full ${
      isCurrent 
        ? 'bg-blue-50/70 border-blue-300 shadow-xs ring-1 ring-blue-300/40 text-slate-800' 
        : isCompleted 
        ? 'bg-emerald-50/50 border-emerald-200 text-slate-800 hover:bg-emerald-50' 
        : 'bg-slate-50 border-slate-200 text-slate-400'
    } ${link ? 'cursor-pointer hover:border-blue-300 hover:shadow-xs' : ''}`}>
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-[11px] ${
            isCurrent ? 'bg-blue-600 text-white' : isCompleted ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-500'
          }`}>
            {step}
          </span>
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
            isCurrent 
              ? 'bg-blue-600 text-white' 
              : isCompleted 
              ? 'bg-emerald-100 text-emerald-700' 
              : 'bg-slate-200 text-slate-500'
          }`}>
            {state}
          </span>
        </div>
        <p className={`font-bold mt-1 ${isPending ? 'text-slate-500' : 'text-slate-900'}`}>{name}</p>
        <p className="text-slate-500 text-xs mt-1 leading-snug">{desc}</p>
      </div>
    </div>
  );

  if (link && !isPending) {
    return <Link to={link}>{cardContent}</Link>;
  }

  return cardContent;
}
