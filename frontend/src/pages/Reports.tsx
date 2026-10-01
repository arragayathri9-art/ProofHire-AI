import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  FileBarChart, 
  ArrowLeft, 
  Printer, 
  Download, 
  RefreshCw, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  BrainCircuit, 
  MessageSquareText, 
  ExternalLink, 
  Briefcase, 
  Layers, 
  ChevronRight, 
  Calendar, 
  Building
} from 'lucide-react';
import CandidatePipelineHeader from '../components/CandidatePipelineHeader';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

interface ReportData {
  analysis_id: number;
  header: {
    title: string;
    subtitle: string;
    candidate_name: string;
    candidate_email: string;
    candidate_location: string;
    target_job: string;
    company: string;
    analysis_id: number;
    report_generated_date: string;
  };
  executive_summary: {
    summary_text: string;
    metrics: {
      total_skills_analyzed: number;
      well_supported_count: number;
      needs_further_verification_count: number;
      strong_evidence: number;
      good_evidence: number;
      moderate_evidence: number;
      limited_evidence: number;
      needs_verification: number;
      total_claims_recorded: number;
      evidence_sources_tracked: number;
      assessment_completed: boolean;
      assessment_overall_score: number | null;
      interview_probes_generated: number;
    };
  };
  evidence_journey: Array<{
    step: number;
    name: string;
    status: string;
    summary: string;
  }>;
  resume_analysis: {
    filename: string;
    skills_identified: string[];
    projects: any[];
    education: any[];
    certifications: any[];
    professional_claims_count: number;
    potential_skill_gaps: string[];
  };
  evidence_verification: Array<{
    id: number;
    claim_text: string;
    source_section: string;
    verification_status: string;
    evidence_level: string;
    evidence_access_status: string;
    evidence_used: string;
    what_supports: string;
    what_is_missing: string;
  }>;
  skill_assessment: {
    status: string;
    overall_percentage: number | null;
    total_score: number | null;
    total_max_score: number | null;
    results: Array<{
      skill: string;
      score: number;
      max_score: number;
      percentage: number;
      demonstration_level: string;
      evidence_before: string;
      feedback: string;
    }>;
  };
  skill_matrix: Array<{
    skill: string;
    resume: string;
    evidence: string;
    assessment: string;
    evidence_level: string;
    job_group: string;
    explanation: string;
    next_verification_step: string | null;
  }>;
  well_supported_skills: Array<{
    skill: string;
    evidence_level: string;
    summary: string;
  }>;
  needs_further_verification_skills: Array<{
    skill: string;
    evidence_level: string;
    next_step: string | null;
    summary: string;
  }>;
  needs_verification_notice: string;
  interview_intelligence: {
    focus_skills: any[];
    questions: Array<{
      id: number;
      order_num: number;
      skill: string;
      question_type: string;
      difficulty: string;
      question_text: string;
      source_context: string | null;
      why_generated: string | null;
      candidate_response: string | null;
      has_response: boolean;
      is_follow_up: boolean;
    }>;
    questions_count: number;
  };
  disclaimer: string;
}

export default function Reports() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { activeAnalysisId, setActiveAnalysis } = useAnalysis();

  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [analysesList, setAnalysesList] = useState<any[]>([]);

  const currentId = id || activeAnalysisId;

  const fetchReport = (analysisId: number | string) => {
    setLoading(true);
    axios.get(`${API_BASE_URL}/api/reports/${analysisId}`)
      .then(res => {
        setReport(res.data);
        setLoading(false);
        if (res.data.header?.candidate_name) {
          setActiveAnalysis(Number(analysisId), {
            name: res.data.header.candidate_name,
            jobTitle: res.data.header.target_job,
            candidateId: res.data.header.analysis_id
          });
        }
      })
      .catch(err => {
        console.error('Failed to load report:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    if (id) {
      fetchReport(id);
    } else if (activeAnalysisId) {
      navigate(`/reports/${activeAnalysisId}`, { replace: true });
    } else {
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

  const handleRefresh = () => {
    if (!currentId) return;
    setRefreshing(true);
    axios.post(`${API_BASE_URL}/api/reports/${currentId}/refresh`)
      .then(res => {
        setReport(res.data);
        setRefreshing(false);
      })
      .catch(err => {
        console.error('Refresh report error:', err);
        setRefreshing(false);
      });
  };

  const handlePrint = () => {
    window.print();
  };

  const getEvidenceLevelBadge = (level: string) => {
    switch (level) {
      case 'Strong Evidence':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">Strong Evidence</span>;
      case 'Good Evidence':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-300">Good Evidence</span>;
      case 'Moderate Evidence':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-100 text-indigo-800 border border-indigo-300">Moderate Evidence</span>;
      case 'Limited Evidence':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-300">Limited Evidence</span>;
      case 'Needs Verification':
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-300">Needs Verification</span>;
    }
  };

  const getAccessStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === 'retrieved') {
      return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Retrieved & Inspected</span>;
    }
    if (s === 'submitted_only') {
      return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">Submitted Only</span>;
    }
    return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">Retrieval Failed</span>;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        <p className="text-slate-600 font-medium text-sm">Aggregating multi-source evidence dossier...</p>
      </div>
    );
  }

  // Candidate Selection View
  if (!currentId || !report) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-12">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
              <FileBarChart className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Verification Reports — Select Candidate</h2>
              <p className="text-slate-500 text-sm mt-0.5">Select a candidate analysis session to view their full ProofHire Evidence Report.</p>
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
                <ChevronRight className="w-4 h-4" />
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
                      navigate(`/reports/${a.id}`);
                    }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                  >
                    <span>View Evidence Report</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  const { header, executive_summary, evidence_journey, resume_analysis, evidence_verification, skill_assessment, skill_matrix, well_supported_skills, needs_further_verification_skills, interview_intelligence, disclaimer } = report;

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16 print:p-0 print:space-y-6 print:max-w-none text-slate-900">
      {/* Print CSS Styles */}
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          body { background: white !important; color: black !important; }
          aside, nav, .no-print, header, button { display: none !important; }
          .print-break-inside-avoid { break-inside: avoid; page-break-inside: avoid; }
          .shadow-sm, .shadow-xs, .shadow-md { box-shadow: none !important; }
          .border { border-color: #cbd5e1 !important; }
          main { padding: 0 !important; overflow: visible !important; }
        }
      `}} />

      {/* Top Candidate Pipeline Header (Hidden during Print) */}
      <div className="no-print">
        <CandidatePipelineHeader 
          analysisId={currentId} 
          candidateName={header.candidate_name} 
          jobTitle={header.target_job} 
        />
      </div>

      {/* Action Bar (Hidden during Print) */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2">
          <Link
            to={`/interview/${currentId}`}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Interview Intelligence</span>
          </Link>
          <span className="text-slate-300">|</span>
          <span className="text-xs text-slate-500 font-medium">Session Snapshot: #{header.analysis_id}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer disabled:opacity-50"
            title="Refreshes aggregated report from latest stored records"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-blue-600' : 'text-slate-500'}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Report Data'}</span>
          </button>
          <button
            onClick={handlePrint}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer"
            title="Print or Save as PDF"
          >
            <Printer className="w-3.5 h-3.5 text-slate-500" />
            <span>Print Report</span>
          </button>
          <button
            onClick={handlePrint}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm cursor-pointer"
            title="Export clean PDF format"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* 2. REPORT HEADER */}
      <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm space-y-6 print:border-b-2 print:border-slate-800 print:rounded-none print:p-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 border-b border-slate-100 pb-6 print:pb-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-extrabold bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                ProofHire.ai Verified Dossier
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 font-mono">
                ID #{header.analysis_id}
              </span>
            </div>
            <h1 className="text-3xl font-black text-slate-900 tracking-tight">
              {header.title}
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              {header.subtitle}
            </p>
          </div>

          <div className="text-right shrink-0 space-y-1 text-xs text-slate-500">
            <p className="flex items-center justify-end gap-1.5 font-semibold text-slate-700">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>{header.report_generated_date}</span>
            </p>
            <p className="flex items-center justify-end gap-1.5">
              <Building className="w-3.5 h-3.5 text-slate-400" />
              <span>{header.company}</span>
            </p>
          </div>
        </div>

        {/* Candidate & Target Role Summary Card */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50/70 p-4 rounded-xl border border-slate-200 print:bg-transparent">
          <div className="space-y-1">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Candidate Information</p>
            <h2 className="text-lg font-black text-slate-900">{header.candidate_name}</h2>
            <p className="text-xs text-slate-600">{header.candidate_email} • {header.candidate_location}</p>
          </div>
          <div className="space-y-1 md:border-l md:border-slate-200 md:pl-4">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Target Role</p>
            <h3 className="text-lg font-black text-slate-900">{header.target_job}</h3>
            <p className="text-xs text-slate-600">Company: {header.company}</p>
          </div>
        </div>
      </div>

      {/* 3. EXECUTIVE SUMMARY */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5 print:rounded-none print-break-inside-avoid">
        <div className="border-b border-slate-100 pb-3">
          <h2 className="text-base font-extrabold text-slate-900 uppercase tracking-tight flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            Executive Summary
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Objective synthesis of multi-source verification records. Strictly factual decision-support without automated rankings.
          </p>
        </div>

        <p className="text-xs md:text-sm text-slate-700 leading-relaxed bg-slate-50/80 p-4 rounded-xl border border-slate-200 font-sans">
          {executive_summary.summary_text}
        </p>

        {/* Factual Metrics Snapshot */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl p-3 text-center">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Skills Evaluated</p>
            <p className="text-xl font-extrabold text-slate-900 mt-1">{executive_summary.metrics.total_skills_analyzed}</p>
          </div>
          <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-3 text-center">
            <p className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider">Well Supported</p>
            <p className="text-xl font-extrabold text-emerald-800 mt-1">{executive_summary.metrics.well_supported_count}</p>
          </div>
          <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-3 text-center">
            <p className="text-[10px] font-bold text-amber-700 uppercase tracking-wider">Needs More Proof</p>
            <p className="text-xl font-extrabold text-amber-800 mt-1">{executive_summary.metrics.needs_further_verification_count}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-3 text-center">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Resume Claims</p>
            <p className="text-xl font-extrabold text-slate-900 mt-1">{executive_summary.metrics.total_claims_recorded}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-3 text-center">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Assessment Score</p>
            <p className="text-xl font-extrabold text-blue-600 mt-1 font-mono">
              {executive_summary.metrics.assessment_overall_score !== null 
                ? `${executive_summary.metrics.assessment_overall_score.toFixed(1)}%` 
                : 'N/A'}
            </p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-3 text-center">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Interview Probes</p>
            <p className="text-xl font-extrabold text-purple-700 mt-1">{executive_summary.metrics.interview_probes_generated}</p>
          </div>
        </div>
      </div>

      {/* 10. EVIDENCE JOURNEY */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4 print:rounded-none print-break-inside-avoid">
        <div className="border-b border-slate-100 pb-3">
          <h2 className="text-base font-extrabold text-slate-900 uppercase tracking-tight flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-600" />
            PROOFHIRE EVIDENCE JOURNEY
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Chronological progression and verification completion state across all pipeline stages.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {evidence_journey.map((step) => (
            <div key={step.step} className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-[11px] font-bold mb-1">
                  <span className="text-slate-400">Stage {step.step}</span>
                  <span className="text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" /> {step.status}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-900">{step.name}</h4>
                <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                  {step.summary}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 11. WELL-SUPPORTED JOB SKILLS vs SKILLS NEEDING FURTHER VERIFICATION */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 print-break-inside-avoid">
        {/* Well Supported */}
        <div className="bg-white border border-emerald-200 rounded-2xl p-6 shadow-sm space-y-4 print:rounded-none">
          <div className="flex items-center justify-between border-b border-emerald-100 pb-3">
            <h3 className="text-base font-extrabold text-emerald-900 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              WELL-SUPPORTED JOB SKILLS
            </h3>
            <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full text-xs font-bold font-mono">
              {well_supported_skills.length}
            </span>
          </div>

          {well_supported_skills.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-4">No skills currently reach Strong or Good Evidence thresholds.</p>
          ) : (
            <div className="space-y-3">
              {well_supported_skills.map((item, idx) => (
                <div key={idx} className="bg-emerald-50/40 border border-emerald-200/80 rounded-xl p-3.5 space-y-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-extrabold text-emerald-950 text-sm">{item.skill}</h4>
                    {getEvidenceLevelBadge(item.evidence_level)}
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">{item.summary}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Needs Further Verification */}
        <div className="bg-white border border-amber-200 rounded-2xl p-6 shadow-sm space-y-4 print:rounded-none">
          <div className="flex items-center justify-between border-b border-amber-100 pb-3">
            <h3 className="text-base font-extrabold text-amber-900 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              SKILLS NEEDING FURTHER VERIFICATION
            </h3>
            <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full text-xs font-bold font-mono">
              {needs_further_verification_skills.length}
            </span>
          </div>

          <div className="p-2.5 bg-amber-50 rounded-xl border border-amber-200 text-[11px] text-amber-900 leading-relaxed">
            <strong>Standard Evaluation Notice:</strong> {report.needs_verification_notice}
          </div>

          <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
            {needs_further_verification_skills.map((item, idx) => (
              <div key={idx} className="bg-amber-50/30 border border-amber-200/70 rounded-xl p-3.5 space-y-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-extrabold text-slate-900 text-sm">{item.skill}</h4>
                  {getEvidenceLevelBadge(item.evidence_level)}
                </div>
                {item.next_step && (
                  <p className="text-[11px] text-amber-800 font-medium">
                    &rarr; {item.next_step}
                  </p>
                )}
                <p className="text-[10px] text-slate-500 leading-relaxed">{item.summary}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 8. SKILL EVIDENCE MATRIX */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4 print:rounded-none print-break-inside-avoid">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 uppercase tracking-tight flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              SKILL EVIDENCE MATRIX
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Empirical evidence triangulation across Resume, Artifacts, and Technical Assessment.
            </p>
          </div>
          <Link
            to={`/skill-profile/${currentId}`}
            className="no-print text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 self-start sm:self-auto"
          >
            <span>View Skill Proof</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-3">Skill</th>
                <th className="py-3 px-3">Resume Claim</th>
                <th className="py-3 px-3">Supporting Evidence</th>
                <th className="py-3 px-3">Assessment Result</th>
                <th className="py-3 px-3">Evidence Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans">
              {skill_matrix.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-3 font-bold text-slate-900">{row.skill}</td>
                  <td className="py-3 px-3 text-slate-700">{row.resume}</td>
                  <td className="py-3 px-3 text-slate-700">{row.evidence}</td>
                  <td className="py-3 px-3 text-slate-700 font-mono">{row.assessment}</td>
                  <td className="py-3 px-3">{getEvidenceLevelBadge(row.evidence_level)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. RESUME ANALYSIS (Phase 1) */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4 print:rounded-none print-break-inside-avoid">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 uppercase tracking-tight flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              1. Resume Analysis
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Extracted claims, documented projects, and identified skill proficiencies.
            </p>
          </div>
          <Link
            to={`/analysis/result/${currentId}`}
            className="no-print text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <span>View Resume Analysis</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>

        {/* Identified Skills Tag Cloud */}
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
            Identified Skills ({resume_analysis.skills_identified.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {resume_analysis.skills_identified.map((s, idx) => (
              <span key={idx} className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium border border-slate-200">
                {s}
              </span>
            ))}
          </div>
        </div>

        {/* Projects */}
        {resume_analysis.projects.length > 0 && (
          <div className="pt-2">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              Candidate Projects Recorded ({resume_analysis.projects.length})
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {resume_analysis.projects.map((p, idx) => (
                <div key={idx} className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1 text-xs">
                  <h4 className="font-extrabold text-slate-900 text-xs">{p.project_name || `Project #${idx+1}`}</h4>
                  <p className="text-slate-600 text-[11px] leading-relaxed line-clamp-3">{p.description}</p>
                  {p.technologies && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {p.technologies.map((t: string, tIdx: number) => (
                        <span key={tIdx} className="text-[10px] bg-white border border-slate-200 px-1.5 py-0.5 rounded text-slate-600">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 5. EVIDENCE VERIFICATION (Phase 2) */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4 print:rounded-none print-break-inside-avoid">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 uppercase tracking-tight flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              2. Evidence Verification
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Inspection status of external claims, URLs, and submitted proof artifacts.
            </p>
          </div>
          <Link
            to={`/evidence/${currentId}`}
            className="no-print text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <span>View Evidence Center</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>

        <div className="space-y-3">
          {evidence_verification.map((c) => (
            <div key={c.id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Source: {c.source_section}
                  </span>
                  <h4 className="font-bold text-slate-900 text-xs mt-0.5 leading-relaxed">&ldquo;{c.claim_text}&rdquo;</h4>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {getAccessStatusBadge(c.evidence_access_status)}
                  {getEvidenceLevelBadge(c.evidence_level)}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t border-slate-200/60 text-[11px]">
                <div className="text-slate-600">
                  <span className="font-semibold text-slate-800">Supports:</span> {c.what_supports}
                </div>
                <div className="text-slate-600">
                  <span className="font-semibold text-slate-800">Missing:</span> {c.what_is_missing}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 6. SKILL ASSESSMENT (Phase 3) */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4 print:rounded-none print-break-inside-avoid">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 uppercase tracking-tight flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-blue-600" />
              3. Skill Assessment Performance
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Empirical technical evaluation test scores and standardized demonstration levels.
            </p>
          </div>
          <Link
            to={`/assessment/${currentId}`}
            className="no-print text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <span>View Skill Assessment</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>

        {skill_assessment.results.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-2">No standardized technical assessment completed for this session.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {skill_assessment.results.map((res, idx) => (
              <div key={idx} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <h4 className="font-extrabold text-slate-900 text-sm">{res.skill}</h4>
                  <span className="text-blue-600 font-black font-mono text-sm">{res.percentage.toFixed(1)}%</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500">
                  <span>Score: {res.score} / {res.max_score} pts</span>
                  <span className="font-semibold text-slate-800">{res.demonstration_level}</span>
                </div>
                <p className="text-[11px] text-slate-600 pt-1 border-t border-slate-200/60 leading-relaxed">
                  {res.feedback}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 9. INTERVIEW INTELLIGENCE (Phase 5) */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4 print:rounded-none print-break-inside-avoid">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 uppercase tracking-tight flex items-center gap-2">
              <MessageSquareText className="w-4 h-4 text-purple-600" />
              4. Interview Intelligence Probes
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Evidence-anchored questions addressing remaining verification gaps.
            </p>
          </div>
          <Link
            to={`/interview/${currentId}`}
            className="no-print text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <span>View Interview Probes</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>

        {interview_intelligence.questions.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-2">No interview questions generated yet.</p>
        ) : (
          <div className="space-y-3">
            {interview_intelligence.questions.map((q) => (
              <div key={q.id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-slate-200 text-slate-800 rounded text-[10px] font-bold font-mono">
                      Q#{q.order_num}
                    </span>
                    <span className="font-extrabold text-slate-900">{q.skill}</span>
                    <span className="text-[10px] bg-purple-50 text-purple-700 border border-purple-200 px-1.5 py-0.5 rounded font-bold">
                      {q.question_type}
                    </span>
                  </div>
                </div>

                <p className="text-slate-900 font-semibold text-xs leading-relaxed">
                  {q.question_text}
                </p>

                {q.why_generated && (
                  <p className="text-[11px] text-slate-500 italic pt-1 border-t border-slate-200/60">
                    Why Generated: {q.why_generated}
                  </p>
                )}

                {q.candidate_response && (
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200 text-[11px] text-slate-700">
                    <span className="font-bold text-slate-900 block mb-0.5">Candidate Response:</span>
                    {q.candidate_response}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 15. REPORT DISCLAIMER */}
      <div className="bg-slate-100 border border-slate-200 rounded-2xl p-6 text-center space-y-2 print:rounded-none print:border-t-2 print:border-slate-800 print:bg-transparent">
        <p className="text-xs font-semibold text-slate-800">
          ProofHire Evidence Decision-Support Disclaimer
        </p>
        <p className="text-[11px] text-slate-600 max-w-3xl mx-auto leading-relaxed">
          &ldquo;{disclaimer}&rdquo;
        </p>
        <p className="text-[10px] text-slate-400 font-mono pt-1">
          ProofHire AI &bull; Session #{header.analysis_id} &bull; Generated: {header.report_generated_date}
        </p>
      </div>
    </div>
  );
}
