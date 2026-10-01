import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Globe, 
  FileText, 
  Clock,
  ArrowRight,
  User,
  PlusCircle,
  GitBranch,
  Code,
  Layers,
  ExternalLink,
  BookOpen,
  Award
} from 'lucide-react';
import CandidatePipelineHeader from '../components/CandidatePipelineHeader';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

export default function EvidenceCenter() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { activeAnalysisId, setActiveAnalysis } = useAnalysis();

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analysesList, setAnalysesList] = useState<any[]>([]);
  const [activeClaimId, setActiveClaimId] = useState<number | null>(null);
  const [evidenceType, setEvidenceType] = useState('github');
  const [description, setDescription] = useState('');
  const [url, setUrl] = useState('');
  const [autoInspect, setAutoInspect] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Certificate upload state (Phase 7A)
  const [certFile, setCertFile] = useState<File | null>(null);
  const [certName, setCertName] = useState('');
  const [certIssuer, setCertIssuer] = useState('');
  const [certCredentialId, setCertCredentialId] = useState('');
  const [certCredentialUrl, setCertCredentialUrl] = useState('');
  const [certTargetClaimId, setCertTargetClaimId] = useState<number | null>(null);
  const [certUploading, setCertUploading] = useState(false);
  const [certError, setCertError] = useState<string | null>(null);
  const [certSuccess, setCertSuccess] = useState<string | null>(null);
  const [isCertSectionOpen, setIsCertSectionOpen] = useState(false);

  useEffect(() => {
    if (id) {
      loadData(id);
    } else {
      // If no id in route, check if we have activeAnalysisId
      if (activeAnalysisId) {
        navigate(`/evidence/${activeAnalysisId}`, { replace: true });
      } else {
        // Fetch analyses list for selection
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
    }
  }, [id, activeAnalysisId, navigate]);

  const loadData = (analysisId: string | number) => {
    setLoading(true);
    axios.get(`${API_BASE_URL}/api/analyses/${analysisId}`)
      .then(res => {
        setData(res.data);
        setLoading(false);
        if (res.data.candidate) {
          setActiveAnalysis(Number(analysisId), {
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
  };

  const handleSelectAnalysis = (analysis: any) => {
    setActiveAnalysis(analysis.id, {
      name: analysis.candidate_name,
      jobTitle: analysis.job_title,
      candidateId: analysis.candidate_id
    });
    navigate(`/evidence/${analysis.id}`);
  };

  const handleUpload = async (claimId: number) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('claim_id', claimId.toString());
    formData.append('evidence_type', evidenceType);
    formData.append('description', description);
    formData.append('url', url);
    formData.append('auto_inspect', autoInspect ? 'true' : 'false');
    if (file) {
      formData.append('file', file);
    }

    try {
      await axios.post(`${API_BASE_URL}/api/evidence`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (id) loadData(id);
      setActiveClaimId(null);
      setDescription('');
      setUrl('');
      setFile(null);
      setAutoInspect(true);
      setUploadError(null);
    } catch (err: any) {
      console.error(err);
      const raw = err.response?.data?.detail || err.message || '';
      if (raw.includes('503') || raw.toLowerCase().includes('unavailable')) {
        setUploadError('AI service is temporarily busy. Please try again.');
      } else {
        setUploadError('Failed to process evidence. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyzeGitHub = async (claimId: number) => {
    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setUploadError('Please enter a GitHub repository URL (e.g., https://github.com/owner/repository).');
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      await axios.post(`${API_BASE_URL}/api/evidence/github`, {
        analysis_id: Number(id),
        claim_id: claimId,
        repository_url: trimmedUrl,
        description: description.trim() || undefined
      });
      if (id) loadData(id);
      setActiveClaimId(null);
      setUrl('');
      setDescription('');
      setUploadError(null);
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail;
      const status = err.response?.status;
      if (status === 404) {
        setUploadError(detail || 'Repository not found on GitHub or is private. ProofHire can only inspect public repositories.');
      } else if (status === 429) {
        setUploadError(detail || 'GitHub API rate limit reached. Please wait a few moments or verify your GITHUB_TOKEN.');
      } else if (status === 400) {
        setUploadError(detail || 'Invalid GitHub repository URL. Must be in the format: https://github.com/owner/repository');
      } else if (status === 502) {
        setUploadError(detail || 'Network error connecting to GitHub API. Please check your internet connection.');
      } else {
        setUploadError(detail || 'Failed to inspect GitHub repository. Please check the URL and try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  const formatLanguages = (langs: Record<string, number> | null | undefined) => {
    if (!langs || typeof langs !== 'object' || Object.keys(langs).length === 0) {
      return [];
    }
    const totalBytes = Object.values(langs).reduce((acc, bytes) => acc + (bytes || 0), 0);
    if (totalBytes === 0) return [];
    
    return Object.entries(langs)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, bytes]) => ({
        name,
        percentage: ((bytes / totalBytes) * 100).toFixed(1),
        bytes
      }));
  };

  const renderAccessStatusBadge = (status: string | null | undefined, isSmall = false) => {
    const sizeClasses = isSmall ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';
    
    if (status === 'retrieved') {
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 ${sizeClasses}`}>
          <CheckCircle2 className={isSmall ? "w-3 h-3" : "w-3.5 h-3.5"} />
          <span>retrieved</span>
        </span>
      );
    }
    if (status === 'retrieval_failed') {
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 ${sizeClasses}`}>
          <XCircle className={isSmall ? "w-3 h-3" : "w-3.5 h-3.5"} />
          <span>retrieval_failed</span>
        </span>
      );
    }
    if (status === 'submitted_only') {
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 ${sizeClasses}`}>
          <AlertTriangle className={isSmall ? "w-3 h-3" : "w-3.5 h-3.5"} />
          <span>submitted_only</span>
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 ${sizeClasses}`}>
        <Clock className={isSmall ? "w-3 h-3" : "w-3.5 h-3.5"} />
        <span>none</span>
      </span>
    );
  };

  const renderVerificationStatusBadge = (status: string | null | undefined) => {
    const s = (status || 'DOCUMENT EXTRACTED').toUpperCase();
    if (s === 'CREDENTIAL URL VERIFIED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>CREDENTIAL URL VERIFIED</span>
        </span>
      );
    }
    if (s === 'DOCUMENT EXTRACTED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
          <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
          <span>DOCUMENT EXTRACTED</span>
        </span>
      );
    }
    if (s === 'SUBMITTED ONLY') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
          <span>SUBMITTED ONLY</span>
        </span>
      );
    }
    if (s === 'VERIFICATION FAILED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          <XCircle className="w-3.5 h-3.5 text-rose-600" />
          <span>VERIFICATION FAILED</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
        <Clock className="w-3.5 h-3.5 text-slate-500" />
        <span>VERIFICATION UNAVAILABLE</span>
      </span>
    );
  };

  const handleCertificateUpload = async (claimIdOverride?: number | null) => {
    if (!certFile) {
      setCertError('Please select a certificate file (PDF, PNG, JPG, or JPEG).');
      return;
    }
    setCertUploading(true);
    setCertError(null);
    setCertSuccess(null);

    const formData = new FormData();
    formData.append('analysis_id', String(id));
    const targetClaim = claimIdOverride !== undefined ? claimIdOverride : certTargetClaimId;
    if (targetClaim) {
      formData.append('claim_id', String(targetClaim));
    }
    formData.append('file', certFile);
    if (certName.trim()) formData.append('certificate_name', certName.trim());
    if (certIssuer.trim()) formData.append('issuer', certIssuer.trim());
    if (certCredentialId.trim()) formData.append('credential_id', certCredentialId.trim());
    if (certCredentialUrl.trim()) formData.append('credential_url', certCredentialUrl.trim());

    try {
      const res = await axios.post(`${API_BASE_URL}/api/evidence/certificate`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const returnedCert = res.data.evidence?.certificate_name || res.data.extracted_fields?.certificate_name || 'Certificate';
      setCertSuccess(`"${returnedCert}" extracted successfully! Status: ${res.data.evidence?.verification_status || 'DOCUMENT EXTRACTED'}`);
      setCertFile(null);
      setCertName('');
      setCertIssuer('');
      setCertCredentialId('');
      setCertCredentialUrl('');
      setCertTargetClaimId(null);
      if (id) loadData(id);
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail;
      setCertError(detail || 'Failed to extract certificate document. Please check file format and try again.');
    } finally {
      setCertUploading(false);
    }
  };

  const renderEvidenceLevelBadge = (level: string | null | undefined) => {
    const effectiveLevel = level || 'Needs Verification';
    let colorClass = 'bg-slate-100 text-slate-700 border-slate-200';
    
    if (effectiveLevel === 'Strong Evidence') {
      colorClass = 'bg-emerald-100 text-emerald-800 border-emerald-300';
    } else if (effectiveLevel === 'Good Evidence') {
      colorClass = 'bg-blue-100 text-blue-800 border-blue-300';
    } else if (effectiveLevel === 'Moderate Evidence') {
      colorClass = 'bg-cyan-100 text-cyan-800 border-cyan-300';
    } else if (effectiveLevel === 'Limited Evidence') {
      colorClass = 'bg-amber-100 text-amber-800 border-amber-300';
    } else if (effectiveLevel === 'Needs Verification') {
      colorClass = 'bg-amber-50 text-amber-800 border-amber-300';
    }

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold border ${colorClass}`}>
        {effectiveLevel}
      </span>
    );
  };

  // If no id was passed and we need the selection view
  if (!id) {
    return (
      <div className="max-w-5xl mx-auto space-y-6 pb-12">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Evidence Center</h2>
              <p className="text-slate-500 text-sm mt-0.5">Select a candidate analysis to inspect evidence and verify claims.</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-base font-bold text-slate-900 mb-4 border-b border-slate-100 pb-3">
            Available Candidate Analyses
          </h3>

          {loading ? (
            <div className="py-12 text-center text-slate-400 text-sm">Loading analyses...</div>
          ) : analysesList.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm">
              <p className="font-semibold text-slate-700">No candidate analyses found.</p>
              <p className="text-xs text-slate-400 mt-1">Start a new analysis first to generate professional claims.</p>
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
              {analysesList.map((analysis: any) => (
                <div 
                  key={analysis.id}
                  className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50 p-3 rounded-xl transition-colors"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-700 font-bold flex items-center justify-center border border-blue-100">
                      {analysis.candidate_name ? analysis.candidate_name.charAt(0).toUpperCase() : <User />}
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 text-sm">{analysis.candidate_name}</h4>
                      <p className="text-xs text-slate-500 font-medium">
                        Target Role: <strong className="text-slate-700">{analysis.job_title}</strong>
                        {analysis.job_company && ` (${analysis.job_company})`}
                      </p>
                      <span className="text-xs text-slate-400 mt-0.5 block">
                        {analysis.claims_count} claims • {analysis.evidence_count} evidence sources submitted
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleSelectAnalysis(analysis)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-xs transition-colors flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
                  >
                    <span>Open Evidence Center</span>
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

  if (loading) return <div className="p-8 text-center text-slate-500">Loading evidence center...</div>;
  if (!data) return <div className="p-8 text-center text-red-500">Analysis not found.</div>;

  const { candidate, job, claims } = data;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Pipeline Navigation Header */}
      <CandidatePipelineHeader 
        analysisId={id} 
        candidateName={candidate.name} 
        jobTitle={job.title} 
      />

      {/* Verification Summary */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between mb-4 border-b pb-3">
          <div>
            <h3 className="text-xl font-semibold text-slate-800">Verification Summary</h3>
            <p className="text-xs text-slate-500 mt-0.5">Overview of claims and their evidence verification standing</p>
          </div>
          <span className="text-xs text-slate-500 font-medium">{claims.length} Claims Tracked</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th className="pb-3 pr-4">Claim</th>
                <th className="pb-3 px-4">Evidence Sources</th>
                <th className="pb-3 px-4">Evidence Access Status</th>
                <th className="pb-3 px-4">Evidence Level</th>
                <th className="pb-3 pl-4">Verification Status</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((claim: any) => {
                const count = claim.evidence ? claim.evidence.length : 0;
                return (
                  <tr key={claim.id} className="border-b border-slate-100 last:border-0 text-sm hover:bg-slate-50 transition-colors">
                    <td className="py-4 pr-4 text-slate-800 font-medium max-w-xs truncate" title={claim.claim_text}>
                      "{claim.claim_text}"
                    </td>
                    <td className="py-4 px-4 text-slate-600">
                      <span className="font-semibold text-slate-700">{count}</span> {count === 1 ? 'Source' : 'Sources'}
                    </td>
                    <td className="py-4 px-4">
                      {renderAccessStatusBadge(claim.evidence_access_status, true)}
                    </td>
                    <td className="py-4 px-4">
                      {renderEvidenceLevelBadge(claim.evidence_level)}
                    </td>
                    <td className="py-4 pl-4 text-slate-600 capitalize text-xs">
                      {claim.verification_status.replace('_', ' ')}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Claim-Evidence Mapping */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <h3 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Claim-Evidence Mapping</h3>
        <div className="space-y-6">
          {claims.map((claim: any) => (
            <div key={claim.id} className="pl-4 border-l-2 border-slate-300">
              <div className="flex items-center gap-2 mb-2">
                <p className="font-semibold text-slate-800">"{claim.claim_text}"</p>
                {renderEvidenceLevelBadge(claim.evidence_level)}
              </div>
              <div className="space-y-2 pl-4 text-sm">
                <div className="text-slate-600 flex items-center gap-2">
                  <span>+-- Resume Source: {claim.source_section}</span>
                </div>
                {claim.evidence && claim.evidence.map((ev: any) => (
                  <div key={ev.id} className="text-slate-700 flex flex-wrap items-center gap-2">
                    <span>
                      +-- {ev.evidence_type === 'github' ? `GitHub Repository: ${ev.repository_owner ? `${ev.repository_owner}/${ev.repository_name}` : (ev.repository_name || ev.url)}` : ev.evidence_type === 'pdf' ? 'Supporting PDF Document' : ev.evidence_type === 'url' ? 'External URL Link' : 'Submitted Text'}
                      {ev.evidence_type !== 'github' && ev.url ? ` (${ev.url})` : ''}
                    </span>
                    {renderAccessStatusBadge(ev.evidence_access_status, true)}
                  </div>
                ))}
                <div className="text-slate-400 flex items-center gap-1 text-xs">
                  <span>+-- Skill Assessment (pending)</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* PHASE 7A: Add Certificate / Credential Section */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 border border-amber-200 flex items-center justify-center font-bold">
              <Award className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-800">Add Certificate / Credential</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Submit candidate certificates and credentials (PDF, PNG, JPG/JPEG) for automated document extraction and skill mapping.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsCertSectionOpen(!isCertSectionOpen)}
            className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer self-start sm:self-auto"
          >
            {isCertSectionOpen ? 'Hide Upload Form' : '+ New Certificate Upload'}
          </button>
        </div>

        {/* Certificate Upload Form */}
        {(isCertSectionOpen || (data.evidence && data.evidence.filter((e: any) => e.evidence_type === 'certificate').length === 0)) && (
          <div className="bg-slate-50/80 rounded-xl p-5 border border-slate-200 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* File input (Required) */}
              <div className="md:col-span-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-amber-600" />
                  <span>Certificate File (PDF, PNG, JPG/JPEG) *</span>
                </label>
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,image/png,image/jpeg,application/pdf"
                  onChange={e => {
                    setCertFile(e.target.files ? e.target.files[0] : null);
                    setCertError(null);
                  }}
                  className="w-full text-sm text-slate-600 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-amber-600 file:text-white hover:file:bg-amber-700 cursor-pointer bg-white p-2 rounded-xl border border-slate-300"
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  Supported formats: PDF, PNG, JPG, JPEG. ProofHire extracts candidate name, issuer, dates, credential IDs, and skills.
                </p>
              </div>

              {/* Optional Certificate Name */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Certificate Name <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={certName}
                  onChange={e => setCertName(e.target.value)}
                  placeholder="e.g., Google Data Analytics Professional Certificate"
                  className="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-amber-500 focus:outline-none"
                />
              </div>

              {/* Optional Issuing Organization */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Issuing Organization <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={certIssuer}
                  onChange={e => setCertIssuer(e.target.value)}
                  placeholder="e.g., Google, Coursera, AWS, Meta"
                  className="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-amber-500 focus:outline-none"
                />
              </div>

              {/* Optional Credential ID */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Credential ID <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={certCredentialId}
                  onChange={e => setCertCredentialId(e.target.value)}
                  placeholder="e.g., GCC-89304-2023"
                  className="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-amber-500 focus:outline-none"
                />
              </div>

              {/* Optional Credential URL */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Credential URL <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  type="url"
                  value={certCredentialUrl}
                  onChange={e => setCertCredentialUrl(e.target.value)}
                  placeholder="e.g., https://coursera.org/verify/..."
                  className="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-amber-500 focus:outline-none"
                />
              </div>

              {/* Associate with claim (optional) */}
              {claims.length > 0 && (
                <div className="md:col-span-2">
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Connect to Candidate Claim <span className="text-slate-400 font-normal">(Optional - auto-matches by skill if unselected)</span>
                  </label>
                  <select
                    value={certTargetClaimId || ''}
                    onChange={e => setCertTargetClaimId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-amber-500 focus:outline-none"
                  >
                    <option value="">Auto-match to relevant skill claims automatically</option>
                    {claims.map((c: any) => (
                      <option key={c.id} value={c.id}>
                        Claim #{c.id}: "{c.claim_text.slice(0, 70)}..."
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {certError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
                <XCircle className="w-4 h-4 shrink-0 text-rose-600" />
                <span>{certError}</span>
              </div>
            )}

            {certSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                <span>{certSuccess}</span>
              </div>
            )}

            <div className="flex items-center gap-3 pt-1">
              <button
                type="button"
                onClick={() => handleCertificateUpload()}
                disabled={certUploading || !certFile}
                className="px-5 py-2.5 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-300 text-white font-semibold rounded-lg text-xs transition-colors flex items-center gap-2 cursor-pointer shadow-xs"
              >
                {certUploading ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Extracting & Analyzing Certificate...</span>
                  </>
                ) : (
                  <>
                    <Award className="w-3.5 h-3.5" />
                    <span>Extract & Save Certificate Evidence</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Existing Uploaded Certificates for Candidate */}
        {data.evidence && data.evidence.filter((e: any) => e.evidence_type === 'certificate').length > 0 && (
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-amber-600" />
              <span>Extracted Certificate Evidence ({data.evidence.filter((e: any) => e.evidence_type === 'certificate').length})</span>
            </h4>
            <div className="grid grid-cols-1 gap-3">
              {data.evidence.filter((e: any) => e.evidence_type === 'certificate').map((certEv: any) => (
                <div key={certEv.id} className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3 shadow-2xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-2.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-600 border border-amber-200 flex items-center justify-center font-bold">
                        <Award className="w-4 h-4 text-amber-600" />
                      </div>
                      <div>
                        <h5 className="font-bold text-slate-800 text-xs sm:text-sm">{certEv.certificate_name || certEv.title}</h5>
                        <p className="text-[11px] text-slate-500">Issuer: <strong className="text-slate-700">{certEv.issuer || 'Issuing Authority'}</strong></p>
                      </div>
                    </div>
                    {renderVerificationStatusBadge(certEv.verification_status)}
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs bg-white p-3 rounded-lg border border-slate-200">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Candidate</span>
                      <span className="font-semibold text-slate-700 text-[11px]">{certEv.certificate_candidate_name || candidate?.name || 'Candidate'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Issue Date</span>
                      <span className="font-semibold text-slate-700 text-[11px]">{certEv.issue_date || 'Not stated'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Credential ID</span>
                      <span className="font-mono text-slate-700 text-[11px] truncate block">{certEv.credential_id || 'Not specified'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Verification URL</span>
                      {certEv.credential_url ? (
                        <a href={certEv.credential_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline flex items-center gap-1 font-mono text-[11px] truncate">
                          <span>{certEv.credential_url}</span>
                          <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                        </a>
                      ) : (
                        <span className="text-slate-400 text-[11px]">None provided</span>
                      )}
                    </div>
                  </div>

                  {certEv.supported_skills && certEv.supported_skills.length > 0 && (
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[11px] font-bold text-slate-600">Skills Detected:</span>
                      {certEv.supported_skills.map((sk: string, sIdx: number) => (
                        <span key={sIdx} className="px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-800 text-[11px] font-medium rounded">
                          {sk}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="p-2.5 bg-amber-50/70 border border-amber-200/80 rounded-lg text-[11px] text-amber-800">
                    <span className="font-bold">Fraud / Integrity Notice:</span> {certEv.evidence_summary || 'Document extracted and fields parsed. Uploading a certificate confirms document extraction and inspection, but does not constitute institutional authentic issuance verification unless independently confirmed via a verified credential authority URL.'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Claims Requiring Verification */}
      <div className="flex items-center justify-between pt-4">
        <div>
          <h3 className="text-2xl font-bold text-slate-800">Claims Requiring Verification</h3>
          <p className="text-slate-500 text-sm mt-0.5">Independently inspect candidate evidence and maintain strict evidence integrity.</p>
        </div>
      </div>

      <div className="space-y-6">
        {claims.length === 0 ? (
          <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-3 shadow-xs">
            <ShieldCheck className="w-10 h-10 text-slate-300 mx-auto" />
            <p className="font-semibold text-slate-800 text-base">No supporting evidence has been submitted yet.</p>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Professional claims extracted from the candidate's resume can be backed with code repositories, live URLs, or verification PDFs.
            </p>
            <button 
              onClick={() => navigate(`/assessment/${id}`)}
              className="mt-4 inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all shadow-xs cursor-pointer"
            >
              <span>Advance to Skill Assessment</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          claims.map((claim: any) => {
          const hasUninspectedUrl = claim.evidence && claim.evidence.some(
            (e: any) => e.evidence_type === 'url' && e.evidence_access_status !== 'retrieved'
          );

          return (
            <div key={claim.id} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">Claim:</p>
                  <p className="font-semibold text-slate-900 mb-4 text-base">"{claim.claim_text}"</p>
                  
                  <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Source Section:</p>
                      <p className="font-medium text-slate-700">{claim.source_section}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Verification Status:</p>
                      <p className="font-medium text-amber-700 capitalize">{claim.verification_status.replace('_', ' ')}</p>
                    </div>
                  </div>

                  {activeClaimId !== claim.id && (
                    <button 
                      onClick={() => {
                        setActiveClaimId(claim.id);
                        setEvidenceType('github');
                        setUrl('');
                        setDescription('');
                        setUploadError(null);
                      }}
                      className="px-4 py-2 bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 font-medium rounded-lg text-sm transition-colors flex items-center gap-1.5 cursor-pointer"
                    >
                      <span>+ Add Supporting Evidence</span>
                    </button>
                  )}
                </div>

                {/* Evidence Analysis Display */}
                <div>
                  <div className="bg-slate-50 p-5 rounded-xl border border-slate-200 text-sm space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
                      <p className="font-bold text-slate-800 text-sm tracking-wide">Evidence Analysis</p>
                      {renderEvidenceLevelBadge(claim.evidence_level)}
                    </div>

                    {/* Prominent Evidence Access Status field */}
                    <div className="flex items-center justify-between bg-white px-3 py-2 rounded-lg border border-slate-200">
                      <span className="font-medium text-slate-700 text-xs uppercase tracking-wide">Evidence Access Status:</span>
                      {renderAccessStatusBadge(claim.evidence_access_status)}
                    </div>

                    {/* Uninspected URL notice when applicable */}
                    {(hasUninspectedUrl || claim.evidence_access_status === 'submitted_only' || claim.evidence_access_status === 'retrieval_failed') && (
                      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold">Evidence Integrity Notice:</span> A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.
                        </div>
                      </div>
                    )}

                    <div>
                      <span className="font-semibold text-slate-700">Evidence Used:</span>
                      <p className="text-slate-600 mt-0.5">{claim.evidence_used || 'Resume claim only (no additional evidence submitted)'}</p>
                    </div>

                    <div>
                      <span className="font-semibold text-slate-700">What Supports the Claim:</span>
                      <p className="text-slate-600 mt-0.5">{claim.what_supports || `Stated in candidate resume under ${claim.source_section}.`}</p>
                    </div>

                    <div>
                      <span className="font-semibold text-slate-700">What Is Still Missing:</span>
                      <p className="text-slate-600 mt-0.5">{claim.what_is_missing || 'No additional supporting evidence has been provided yet.'}</p>
                    </div>

                    <div>
                      <span className="font-semibold text-slate-700">Next Verification Step:</span>
                      <p className="text-slate-600 mt-0.5">{claim.next_step || 'Submit supporting evidence (code repository, deployment URL, or documentation) to begin verification.'}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Supporting Evidence Items (GitHub Evidence Card & Other Evidence) */}
              {claim.evidence && claim.evidence.length > 0 && (
                <div className="mt-6 pt-5 border-t border-slate-200 space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-blue-600" />
                      <span>Verified Supporting Evidence ({claim.evidence.length})</span>
                    </h4>
                    <span className="text-xs text-slate-400">Inspected by ProofHire Evidence Intelligence</span>
                  </div>

                  {claim.evidence.map((ev: any) => {
                    const isGitHub = ev.evidence_type === 'github' || Boolean(ev.repository_name);
                    const isRetrieved = ev.evidence_access_status === 'retrieved';
                    const langsList = formatLanguages(ev.languages);

                    if (isGitHub) {
                      return (
                        <div key={ev.id} className="bg-slate-50/70 border border-slate-200 rounded-xl p-5 space-y-4 shadow-xs">
                          {/* Card Header */}
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold shadow-xs">
                                <GitBranch className="w-5 h-5 text-blue-400" />
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="text-[11px] font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                                    RETRIEVED EVIDENCE
                                  </span>
                                  <span className="text-xs text-slate-400">• GitHub REST API</span>
                                </div>
                                <div className="flex items-center gap-2 mt-0.5">
                                  <h5 className="font-bold text-slate-900 text-base">
                                    {ev.repository_owner ? `${ev.repository_owner}/${ev.repository_name}` : (ev.repository_name || ev.title || 'GitHub Repository')}
                                  </h5>
                                  {ev.url && (
                                    <a 
                                      href={ev.url} 
                                      target="_blank" 
                                      rel="noreferrer" 
                                      className="text-slate-400 hover:text-blue-600 transition-colors inline-flex items-center"
                                      title="Open repository in new tab"
                                    >
                                      <ExternalLink className="w-3.5 h-3.5" />
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>

                            <div>
                              {isRetrieved ? (
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-300 shadow-2xs">
                                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                  <span>✓ Retrieved from GitHub</span>
                                </span>
                              ) : (
                                renderAccessStatusBadge(ev.evidence_access_status)
                              )}
                            </div>
                          </div>

                          {/* Description */}
                          <p className="text-sm text-slate-700 font-normal leading-relaxed">
                            {ev.description || "Public repository retrieved from GitHub"}
                          </p>

                          {/* Metadata Grid */}
                          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 bg-white p-3.5 rounded-lg border border-slate-200 text-xs">
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Repository Name</span>
                              <span className="font-semibold text-slate-800 truncate block mt-0.5">
                                {ev.repository_name || 'N/A'}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Owner</span>
                              <span className="font-semibold text-slate-800 truncate block mt-0.5">
                                {ev.repository_owner || 'N/A'}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Primary Language</span>
                              <span className="font-semibold text-blue-700 flex items-center gap-1.5 mt-0.5">
                                <span className="w-2 h-2 rounded-full bg-blue-600 inline-block"></span>
                                {ev.primary_language || 'Not specified'}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Default Branch</span>
                              <span className="font-mono text-slate-700 block mt-0.5 font-medium">
                                {ev.default_branch || 'main'}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">README Status</span>
                              <span className="font-semibold text-emerald-700 block mt-0.5">
                                {ev.readme_summary && ev.readme_summary !== 'README unavailable.' ? 'Available (Indexed)' : 'README unavailable'}
                              </span>
                            </div>
                          </div>

                          {/* Languages Detected */}
                          {langsList.length > 0 && (
                            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                              <span className="font-bold text-slate-600">Languages Detected:</span>
                              {langsList.map((lang) => (
                                <span 
                                  key={lang.name}
                                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 font-medium shadow-2xs"
                                >
                                  <span>{lang.name}</span>
                                  <span className="text-slate-400 text-[11px]">({lang.percentage}%)</span>
                                </span>
                              ))}
                            </div>
                          )}

                          {/* Section: DETECTED SKILL SIGNALS */}
                          <div className="space-y-2 pt-2">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                                <Code className="w-3.5 h-3.5 text-blue-600" />
                                <span>DETECTED SKILL SIGNALS</span>
                              </span>
                              <span className="text-[11px] text-slate-400">Derived from real retrieved repository files</span>
                            </div>

                            {ev.skill_signals && ev.skill_signals.length > 0 ? (
                              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                                {ev.skill_signals.map((sig: any, sIdx: number) => (
                                  <div 
                                    key={sIdx} 
                                    className="p-3 bg-white rounded-lg border border-slate-200 shadow-2xs flex flex-col justify-between"
                                  >
                                    <div className="flex items-center justify-between">
                                      <span className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                                        <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                                        {sig.skill}
                                      </span>
                                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">
                                        {sig.confidence || 'High'}
                                      </span>
                                    </div>
                                    <p className="text-[11px] text-slate-500 mt-1.5 line-clamp-2 leading-relaxed" title={sig.source}>
                                      {sig.source}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs text-slate-500 italic p-3 bg-white rounded-lg border border-slate-200">
                                No framework-specific skill signals detected in retrieved repository files.
                              </div>
                            )}
                          </div>

                          {/* Section: EVIDENCE CONNECTION */}
                          <div className="bg-blue-50/40 p-4 rounded-xl border border-blue-100 space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold uppercase tracking-wider text-blue-900 flex items-center gap-1.5">
                                <Layers className="w-3.5 h-3.5 text-blue-600" />
                                <span>EVIDENCE CONNECTION</span>
                              </span>
                              <span className="text-[10px] text-blue-600 font-semibold uppercase">Deterministic Verification Flow</span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-4 gap-2 relative">
                              {/* Step 1: Claim Being Verified */}
                              <div className="bg-white p-3 rounded-lg border border-blue-200 text-xs flex flex-col justify-between shadow-2xs">
                                <div>
                                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">1. Claim Being Verified</span>
                                  <p className="font-medium text-slate-800 line-clamp-3 italic" title={claim.claim_text}>
                                    "{claim.claim_text}"
                                  </p>
                                </div>
                                <span className="text-[10px] text-slate-400 mt-2 block">Source: {claim.source_section}</span>
                              </div>

                              {/* Step 2: GitHub Repository */}
                              <div className="bg-white p-3 rounded-lg border border-blue-200 text-xs flex flex-col justify-between shadow-2xs">
                                <div>
                                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">2. GitHub Repository</span>
                                  <p className="font-bold text-blue-700 truncate mt-1">
                                    {ev.repository_owner}/{ev.repository_name || 'repo'}
                                  </p>
                                  <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">
                                    {ev.primary_language || 'Codebase'} ({ev.default_branch || 'main'})
                                  </p>
                                </div>
                                <span className="text-[10px] text-emerald-600 font-bold mt-2 block">✓ Public GitHub Data</span>
                              </div>

                              {/* Step 3: Detected Signals */}
                              <div className="bg-white p-3 rounded-lg border border-blue-200 text-xs flex flex-col justify-between shadow-2xs">
                                <div>
                                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">3. Detected Signals</span>
                                  <p className="font-semibold text-slate-800 mt-1 line-clamp-2">
                                    {ev.skill_signals && ev.skill_signals.length > 0 
                                      ? ev.skill_signals.map((s: any) => s.skill).join(', ') 
                                      : (ev.primary_language || 'Source Code')}
                                  </p>
                                </div>
                                <span className="text-[10px] text-slate-500 mt-2 block">Extracted from repository files</span>
                              </div>

                              {/* Step 4: Related Skill */}
                              <div className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white p-3 rounded-lg text-xs flex flex-col justify-between shadow-2xs">
                                <div>
                                  <span className="text-[10px] uppercase font-bold text-blue-200 block mb-1">4. Related Skill</span>
                                  <p className="font-bold text-white text-sm mt-1">
                                    {claim.skill?.skill_name || (ev.skill_signals && ev.skill_signals[0]?.skill) || 'Technical Skill'}
                                  </p>
                                </div>
                                <div className="mt-2 pt-2 border-t border-blue-500/50 flex items-center justify-between text-[11px]">
                                  <span className="text-blue-100">Standing:</span>
                                  <span className="font-bold text-white">{claim.evidence_level || 'Verified'}</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Optional README Summary excerpt */}
                          {ev.readme_summary && ev.readme_summary !== 'README unavailable.' && (
                            <div className="bg-white p-3.5 rounded-lg border border-slate-200 text-xs space-y-1.5">
                              <span className="font-bold text-slate-700 flex items-center gap-1.5">
                                <BookOpen className="w-3.5 h-3.5 text-slate-500" />
                                <span>README Excerpt Preview</span>
                              </span>
                              <pre className="text-slate-600 text-[11px] whitespace-pre-wrap font-sans bg-slate-50 p-2.5 rounded border border-slate-100 max-h-32 overflow-y-auto leading-relaxed">
                                {ev.readme_summary}
                              </pre>
                            </div>
                          )}
                        </div>
                      );
                    }

                    // Certificate Evidence Card
                    if (ev.evidence_type === 'certificate') {
                      const skillsList = ev.supported_skills || [];
                      return (
                        <div key={ev.id} className="bg-slate-50/80 border border-slate-200 rounded-xl p-5 space-y-4 shadow-2xs">
                          {/* Card Header */}
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 border border-amber-200 flex items-center justify-center font-bold shadow-2xs">
                                <Award className="w-5 h-5 text-amber-600" />
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <h5 className="font-bold text-slate-900 text-sm">{ev.certificate_name || ev.title || 'Certificate'}</h5>
                                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                                    {ev.issuer || 'Issuing Authority'}
                                  </span>
                                </div>
                                <p className="text-xs text-slate-500 mt-0.5">
                                  Candidate on Credential: <strong className="text-slate-700">{ev.certificate_candidate_name || candidate?.name || 'Candidate'}</strong>
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {renderVerificationStatusBadge(ev.verification_status)}
                            </div>
                          </div>

                          {/* Grid of Extracted Fields */}
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white p-3.5 rounded-xl border border-slate-200 text-xs">
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Certificate</span>
                              <span className="font-semibold text-slate-800 line-clamp-1 mt-0.5" title={ev.certificate_name || ev.title}>
                                {ev.certificate_name || ev.title || 'N/A'}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Issuer</span>
                              <span className="font-semibold text-slate-800 line-clamp-1 mt-0.5" title={ev.issuer}>
                                {ev.issuer || 'Unknown Issuer'}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Issue Date</span>
                              <span className="font-semibold text-slate-800 mt-0.5 block">
                                {ev.issue_date || 'Not stated'}
                                {ev.expiry_date && <span className="text-[10px] text-slate-400 block font-normal">Exp: {ev.expiry_date}</span>}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Credential ID</span>
                              <span className="font-mono text-xs text-slate-700 mt-0.5 block truncate" title={ev.credential_id || 'None'}>
                                {ev.credential_id || 'Not specified'}
                              </span>
                            </div>
                          </div>

                          {/* Skills Detected */}
                          {skillsList.length > 0 && (
                            <div className="space-y-1.5">
                              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                                <Layers className="w-3.5 h-3.5 text-blue-600" />
                                <span>Skills Detected:</span>
                              </span>
                              <div className="flex flex-wrap gap-1.5">
                                {skillsList.map((sk: string, sIdx: number) => (
                                  <span key={sIdx} className="px-2.5 py-1 bg-blue-50 border border-blue-200 text-blue-800 text-xs font-medium rounded-md">
                                    {sk}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Credential URL if present */}
                          {ev.credential_url && (
                            <div className="flex items-center gap-2 text-xs bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                              <span className="font-semibold text-slate-600">Verification URL:</span>
                              <a href={ev.credential_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline flex items-center gap-1 font-mono truncate">
                                <span>{ev.credential_url}</span>
                                <ExternalLink className="w-3 h-3 shrink-0" />
                              </a>
                            </div>
                          )}

                          {/* Fraud / Integrity Notice */}
                          <div className="p-3 bg-amber-50/70 border border-amber-200/80 rounded-lg text-xs space-y-1">
                            <div className="flex items-center gap-1.5 text-amber-900 font-bold">
                              <ShieldCheck className="w-3.5 h-3.5 text-amber-700" />
                              <span>Fraud / Integrity Rule:</span>
                            </div>
                            <p className="text-amber-800 text-[11px] leading-relaxed">
                              {ev.evidence_summary || 'Document extracted and fields parsed. Uploading a certificate confirms document extraction and inspection, but does not constitute institutional authentic issuance verification unless independently confirmed via a verified credential authority URL.'}
                            </p>
                          </div>
                        </div>
                      );
                    }

                    // Non-GitHub evidence card (URL, Document, Text)
                    return (
                      <div key={ev.id} className="bg-slate-50/70 border border-slate-200 rounded-xl p-4 space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-800">
                              {ev.evidence_type === 'pdf' ? 'Supporting PDF Document' : ev.evidence_type === 'url' ? 'External URL Link' : 'Submitted Text'}
                            </span>
                            {ev.url && (
                              <a href={ev.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline flex items-center gap-1 font-mono">
                                <span>{ev.url}</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                          {renderAccessStatusBadge(ev.evidence_access_status)}
                        </div>
                        {ev.description && (
                          <p className="text-slate-600 italic">"{ev.description}"</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Upload Form */}
              {activeClaimId === claim.id && (
                <div className="mt-6 p-5 bg-blue-50/50 border border-blue-200 rounded-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-slate-800 text-base">Add Supporting Evidence</h4>
                      <p className="text-xs text-slate-500 mt-0.5">Connect public GitHub repositories, documents, or project URLs for independent verification.</p>
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 bg-white border border-slate-200 rounded-md text-slate-600 shadow-2xs">
                      Claim #{claim.id}
                    </span>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-1">Evidence Type</label>
                      <select 
                        value={evidenceType} 
                        onChange={e => {
                          setEvidenceType(e.target.value);
                          setUploadError(null);
                        }}
                        className="w-full p-2.5 border border-slate-300 rounded-lg bg-white text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
                      >
                        <option value="github">GitHub Repository</option>
                        <option value="certificate">Certificate / Credential</option>
                        <option value="url">Project URL</option>
                        <option value="pdf">Document</option>
                        <option value="text">Other Evidence</option>
                      </select>
                    </div>

                    {/* Certificate input */}
                    {evidenceType === 'certificate' && (
                      <div className="space-y-3 bg-white p-4 rounded-xl border border-slate-200">
                        <div>
                          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1 flex items-center gap-1.5">
                            <Award className="w-4 h-4 text-amber-600" />
                            <span>Certificate File (PDF, PNG, JPG/JPEG) *</span>
                          </label>
                          <input 
                            type="file" 
                            accept=".pdf,.png,.jpg,.jpeg,image/png,image/jpeg,application/pdf"
                            onChange={e => {
                              setCertFile(e.target.files ? e.target.files[0] : null);
                              setUploadError(null);
                            }}
                            className="w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-amber-50 file:text-amber-800 hover:file:bg-amber-100 cursor-pointer"
                          />
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                          <div>
                            <label className="block text-xs font-semibold text-slate-700 mb-1">
                              Certificate Name <span className="text-slate-400 font-normal">(Optional)</span>
                            </label>
                            <input 
                              type="text" 
                              value={certName} 
                              onChange={e => setCertName(e.target.value)}
                              placeholder="e.g., Google Data Analytics"
                              className="w-full p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-slate-700 mb-1">
                              Issuing Organization <span className="text-slate-400 font-normal">(Optional)</span>
                            </label>
                            <input 
                              type="text" 
                              value={certIssuer} 
                              onChange={e => setCertIssuer(e.target.value)}
                              placeholder="e.g., Google, Coursera, AWS"
                              className="w-full p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-slate-700 mb-1">
                              Credential ID <span className="text-slate-400 font-normal">(Optional)</span>
                            </label>
                            <input 
                              type="text" 
                              value={certCredentialId} 
                              onChange={e => setCertCredentialId(e.target.value)}
                              placeholder="e.g., GCC-98213"
                              className="w-full p-2 border border-slate-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-slate-700 mb-1">
                              Credential URL <span className="text-slate-400 font-normal">(Optional)</span>
                            </label>
                            <input 
                              type="url" 
                              value={certCredentialUrl} 
                              onChange={e => setCertCredentialUrl(e.target.value)}
                              placeholder="e.g., https://coursera.org/verify/..."
                              className="w-full p-2 border border-slate-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                          </div>
                        </div>
                      </div>
                    )}

                    {/* GitHub Repository input */}
                    {evidenceType === 'github' && (
                      <div className="space-y-3 bg-white p-4 rounded-xl border border-slate-200">
                        <div>
                          <label className="block text-sm font-semibold text-slate-800 mb-1 flex items-center gap-1.5">
                            <GitBranch className="w-4 h-4 text-blue-600" />
                            <span>GitHub Repository URL</span>
                          </label>
                          <input 
                            type="url" 
                            value={url} 
                            onChange={e => setUrl(e.target.value)}
                            placeholder="https://github.com/owner/repository"
                            className="w-full p-2.5 border border-slate-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                            ProofHire directly queries the official GitHub REST API to retrieve repository metadata, language distribution, file tree structure, and README.
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Project URL input */}
                    {evidenceType === 'url' && (
                      <div className="space-y-3 bg-white p-3.5 rounded-lg border border-slate-200">
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-1.5">
                            <Globe className="w-4 h-4 text-blue-600" />
                            <span>Project URL</span>
                          </label>
                          <input 
                            type="url" 
                            value={url} 
                            onChange={e => setUrl(e.target.value)}
                            placeholder="https://example.com or live deployment"
                            className="w-full p-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div className="flex items-start gap-2 pt-1">
                          <input 
                            type="checkbox" 
                            id={`inspect-${claim.id}`}
                            checked={autoInspect}
                            onChange={e => setAutoInspect(e.target.checked)}
                            className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                          />
                          <label htmlFor={`inspect-${claim.id}`} className="text-xs text-slate-600 cursor-pointer">
                            <span className="font-semibold text-slate-800">Attempt automated inspection and content retrieval</span>
                            <br />
                            When checked, ProofHire will fetch and inspect the page content (<span className="text-emerald-700 font-mono">retrieved</span>). If unchecked, the URL will be logged as user-provided supporting reference only (<span className="text-amber-700 font-mono">submitted_only</span>).
                          </label>
                        </div>
                      </div>
                    )}

                    {/* Document input */}
                    {evidenceType === 'pdf' && (
                      <div className="bg-white p-3.5 rounded-lg border border-slate-200">
                        <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-1.5">
                          <FileText className="w-4 h-4 text-blue-600" />
                          <span>Document (PDF)</span>
                        </label>
                        <input 
                          type="file" 
                          accept="application/pdf"
                          onChange={e => setFile(e.target.files ? e.target.files[0] : null)}
                          className="w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
                        />
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-1">
                        {evidenceType === 'github' ? 'Additional Notes / Context (Optional)' : 'Description / Context'}
                      </label>
                      <textarea 
                        value={description}
                        onChange={e => setDescription(e.target.value)}
                        placeholder="Provide details on how this evidence supports the claim..."
                        className="w-full p-2.5 border border-slate-300 rounded-lg text-sm h-20 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    {uploadError && (
                      <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center justify-between gap-3 shadow-2xs">
                        <div className="flex items-center gap-2">
                          <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                          <span className="font-medium">{uploadError}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            if (evidenceType === 'github') {
                              handleAnalyzeGitHub(claim.id);
                            } else if (evidenceType === 'certificate') {
                              handleCertificateUpload(claim.id);
                            } else {
                              handleUpload(claim.id);
                            }
                          }}
                          className="px-2.5 py-1 bg-rose-600 text-white rounded text-xs font-semibold hover:bg-rose-700 cursor-pointer shrink-0"
                        >
                          Try Again
                        </button>
                      </div>
                    )}

                    <div className="flex gap-3 pt-2">
                      {evidenceType === 'github' ? (
                        <button 
                          onClick={() => handleAnalyzeGitHub(claim.id)}
                          disabled={uploading}
                          className="px-5 py-2.5 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300 font-semibold rounded-lg text-sm transition-colors shadow-sm flex items-center gap-2 cursor-pointer"
                        >
                          {uploading ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              <span>Analyzing Repository via GitHub API...</span>
                            </>
                          ) : (
                            <>
                              <GitBranch className="w-4 h-4" />
                              <span>Analyze Repository</span>
                            </>
                          )}
                        </button>
                      ) : evidenceType === 'certificate' ? (
                        <button 
                          onClick={() => handleCertificateUpload(claim.id)}
                          disabled={certUploading || !certFile}
                          className="px-5 py-2.5 bg-amber-600 text-white hover:bg-amber-700 disabled:bg-amber-300 font-semibold rounded-lg text-sm transition-colors shadow-sm flex items-center gap-2 cursor-pointer"
                        >
                          {certUploading ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              <span>Extracting & Analyzing Certificate...</span>
                            </>
                          ) : (
                            <>
                              <Award className="w-4 h-4" />
                              <span>Extract Certificate</span>
                            </>
                          )}
                        </button>
                      ) : (
                        <button 
                          onClick={() => handleUpload(claim.id)}
                          disabled={uploading}
                          className="px-5 py-2.5 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300 font-semibold rounded-lg text-sm transition-colors shadow-sm flex items-center gap-2 cursor-pointer"
                        >
                          {uploading ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              <span>Inspecting & Processing Evidence...</span>
                            </>
                          ) : 'Submit Evidence'}
                        </button>
                      )}
                      <button 
                        onClick={() => {
                          setActiveClaimId(null);
                          setUploadError(null);
                          setUrl('');
                          setDescription('');
                        }}
                        className="px-4 py-2.5 bg-slate-200 text-slate-700 hover:bg-slate-300 font-medium rounded-lg text-sm transition-colors cursor-pointer"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })
      )}
      </div>

      {/* Prepare for Phase 3: Continue to Skill Assessment */}
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 mt-8 text-center space-y-4">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Evidence Verification Complete</span>
          </span>
          <h3 className="text-xl font-bold text-slate-900 mt-2">Ready for Next Stage: Personalized Skill Assessment</h3>
          <p className="text-slate-500 text-xs max-w-md mx-auto mt-1">
            Advance to generate tailored evaluation questions based on the candidate's verified skills and supporting claims.
          </p>
        </div>

        <div>
          <button 
            onClick={() => navigate(`/assessment/${id}`)}
            className="inline-flex items-center gap-2 px-6 py-3.5 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 shadow-sm hover:shadow-md transition-all active:scale-95 cursor-pointer text-sm"
          >
            <span>Continue to Skill Assessment</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

    </div>
  );
}
