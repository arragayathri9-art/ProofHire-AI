import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { User, Mail, Phone, MapPin, Briefcase, FileText, ShieldCheck, BrainCircuit, ArrowRight, ArrowLeft } from 'lucide-react';
import CandidatePipelineHeader from '../components/CandidatePipelineHeader';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

export default function CandidateDetail() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { setActiveAnalysis } = useAnalysis();
  const navigate = useNavigate();

  useEffect(() => {
    if (id) {
      axios.get(`${API_BASE_URL}/api/candidates/${id}`)
        .then(res => {
          setData(res.data);
          setLoading(false);
          if (res.data.latest_analysis_id) {
            setActiveAnalysis(res.data.latest_analysis_id, {
              name: res.data.candidate.name,
              jobTitle: res.data.job?.title || 'Target Job',
              candidateId: res.data.candidate.id
            });
          }
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [id]);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading candidate profile...</div>;
  if (!data || !data.candidate) return <div className="p-8 text-center text-red-500">Candidate not found.</div>;

  const { candidate, resume, skills, claims, latest_analysis_id, job } = data;

  const handleOpenEvidence = () => {
    if (latest_analysis_id) {
      setActiveAnalysis(latest_analysis_id, {
        name: candidate.name,
        jobTitle: job?.title || 'Target Job',
        candidateId: candidate.id
      });
      navigate(`/evidence/${latest_analysis_id}`);
    }
  };

  const handleOpenAssessment = () => {
    if (latest_analysis_id) {
      setActiveAnalysis(latest_analysis_id, {
        name: candidate.name,
        jobTitle: job?.title || 'Target Job',
        candidateId: candidate.id
      });
      navigate(`/assessment/${latest_analysis_id}`);
    }
  };

  const handleOpenAnalysis = () => {
    if (latest_analysis_id) {
      setActiveAnalysis(latest_analysis_id, {
        name: candidate.name,
        jobTitle: job?.title || 'Target Job',
        candidateId: candidate.id
      });
      navigate(`/analysis/result/${latest_analysis_id}`);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Back navigation */}
      <div>
        <Link to="/candidates" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-600 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Candidates</span>
        </Link>
      </div>

      {latest_analysis_id && (
        <CandidatePipelineHeader 
          analysisId={latest_analysis_id} 
          candidateName={candidate.name} 
          jobTitle={job?.title} 
        />
      )}

      {/* Header Profile Card */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-blue-600 text-white flex items-center justify-center font-bold text-2xl shadow-sm">
            {candidate.name ? candidate.name.charAt(0).toUpperCase() : <User />}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-slate-900">{candidate.name}</h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                Candidate #{candidate.id}
              </span>
            </div>
            <div className="flex flex-wrap gap-4 text-xs text-slate-500 mt-2">
              {candidate.email && (
                <span className="flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-slate-400" />
                  <span>{candidate.email}</span>
                </span>
              )}
              {candidate.phone && (
                <span className="flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5 text-slate-400" />
                  <span>{candidate.phone}</span>
                </span>
              )}
              {candidate.location && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  <span>{candidate.location}</span>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Quick Action Navigation */}
        <div className="flex flex-wrap gap-3">
          {latest_analysis_id && (
            <>
              <button
                onClick={handleOpenAssessment}
                className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-xs shadow-sm flex items-center gap-2 transition-all cursor-pointer"
              >
                <BrainCircuit className="w-4 h-4" />
                <span>Skill Assessment</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={handleOpenEvidence}
                className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition-all flex items-center gap-2 cursor-pointer"
              >
                <ShieldCheck className="w-4 h-4 text-slate-500" />
                <span>Evidence Center</span>
              </button>
              <button
                onClick={handleOpenAnalysis}
                className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition-all flex items-center gap-2 cursor-pointer"
              >
                <FileText className="w-4 h-4 text-slate-500" />
                <span>Preliminary Analysis</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Grid: Resume info + Skills & Projects */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left Column: Summary & Skills */}
        <div className="md:col-span-1 space-y-6">
          {/* Professional Summary */}
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-2">Professional Summary</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              {candidate.professional_summary || "Extracted from candidate resume profile."}
            </p>
          </div>

          {/* Extracted Skills */}
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-3">Extracted Skills ({skills.length})</h3>
            <div className="flex flex-wrap gap-1.5">
              {skills.map((s: string, idx: number) => (
                <span key={idx} className="px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg text-xs font-medium">
                  {s}
                </span>
              ))}
            </div>
          </div>

          {/* Verification & Profile Status */}
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Pipeline Status</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-slate-100">
                <span className="text-slate-500">Resume Extraction</span>
                <span className="text-emerald-700 font-semibold">✓ Complete</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-100">
                <span className="text-slate-500">Evidence Verification</span>
                <span className="text-emerald-700 font-semibold">{claims.length > 0 ? '✓ Active' : 'Pending'}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-100">
                <span className="text-slate-500">Skill Assessment</span>
                {latest_analysis_id ? (
                  <Link to={`/assessment/${latest_analysis_id}`} className="text-blue-600 font-semibold hover:underline flex items-center gap-1">
                    <span>Active Assessment</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                ) : (
                  <span className="text-slate-400">Next Phase</span>
                )}
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-500">Skill Profile</span>
                <span className="text-slate-400">Pending</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Claims & Projects */}
        <div className="md:col-span-2 space-y-6">
          {/* Professional Claims */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Extracted Claims & Evidence</h3>
                <p className="text-xs text-slate-500">Extracted claims and their current verification standing</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-100 text-slate-700">
                {claims.length} Claims
              </span>
            </div>

            {claims.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">No specific claims extracted for this candidate.</p>
            ) : (
              <div className="space-y-4">
                {claims.map((claim: any) => (
                  <div key={claim.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                    <div className="flex items-start justify-between gap-4">
                      <p className="text-sm font-semibold text-slate-800 leading-snug">"{claim.claim_text}"</p>
                      <span className="shrink-0 text-xs px-2.5 py-0.5 rounded-full font-semibold border bg-white border-slate-300 text-slate-700">
                        {claim.evidence_level || 'Needs Verification'}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-1">
                      <span>Source: <strong className="text-slate-700 font-medium">{claim.source_section}</strong></span>
                      <span>•</span>
                      <span>Evidence Items: <strong className="text-slate-700 font-medium">{claim.evidence ? claim.evidence.length : 0}</strong></span>
                      {claim.evidence_access_status && (
                        <>
                          <span>•</span>
                          <span className="text-blue-700 font-mono">[{claim.evidence_access_status}]</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Projects */}
          {candidate.projects && candidate.projects.length > 0 && (
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <h3 className="text-base font-bold text-slate-900 mb-4 border-b border-slate-100 pb-3">
                Extracted Projects ({candidate.projects.length})
              </h3>
              <div className="space-y-4">
                {candidate.projects.map((proj: any, i: number) => (
                  <div key={i} className="border-l-2 border-blue-500 pl-3 py-1">
                    <h4 className="font-bold text-slate-800 text-sm">{proj.project_name}</h4>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">{proj.description}</p>
                    {proj.technologies && proj.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {proj.technologies.map((t: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded">
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

          {/* Resume Upload File details */}
          {resume && (
            <div className="bg-white p-4 rounded-xl border border-slate-200 text-xs flex items-center justify-between text-slate-500">
              <span className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-slate-400" />
                <span>Uploaded Source File: <strong className="text-slate-700">{resume.filename}</strong></span>
              </span>
              <span>Uploaded: {new Date(resume.uploaded_at).toLocaleDateString()}</span>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
