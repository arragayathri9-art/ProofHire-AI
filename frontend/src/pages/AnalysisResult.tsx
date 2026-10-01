import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import CandidatePipelineHeader from '../components/CandidatePipelineHeader';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

export default function AnalysisResult() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { setActiveAnalysis } = useAnalysis();

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/analyses/${id}`)
      .then(res => {
        setData(res.data);
        setLoading(false);
        if (id && res.data.candidate) {
          setActiveAnalysis(Number(id), {
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
  }, [id]);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading results...</div>;
  if (!data) return <div className="p-8 text-center text-red-500">Analysis not found.</div>;

  const { candidate, analysis, job, claims, candidate_skills } = data;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      <CandidatePipelineHeader 
        analysisId={id} 
        candidateName={candidate.name} 
        jobTitle={job.title} 
      />

      {/* Top Header */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 className="text-3xl font-bold text-slate-800">{candidate.name}</h2>
        <p className="text-slate-500 mt-1 font-medium">Target Job: <span className="text-slate-700">{job.title}</span></p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Candidate Details */}
        <div className="space-y-6">
          
          {/* Candidate Overview */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Candidate Overview</h3>
            <div className="space-y-2 text-sm">
              <p><span className="font-medium text-slate-600">Name:</span> {candidate.name}</p>
              {candidate.email && <p><span className="font-medium text-slate-600">Email:</span> {candidate.email}</p>}
              {candidate.location && <p><span className="font-medium text-slate-600">Location:</span> {candidate.location}</p>}
              {candidate.professional_summary && (
                <div className="mt-4">
                  <p className="font-medium text-slate-600">Professional Summary:</p>
                  <p className="text-slate-700 mt-1">{candidate.professional_summary}</p>
                </div>
              )}
            </div>
          </div>

          {/* Extracted Skills */}
          {candidate_skills && candidate_skills.length > 0 && (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Extracted Skills</h3>
              <div className="flex flex-wrap gap-2">
                {candidate_skills.map((s: string) => (
                  <span key={s} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-100">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Education */}
          {candidate.education && candidate.education.length > 0 && (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Education</h3>
              <ul className="space-y-4">
                {candidate.education.map((edu: any, i: number) => (
                  <li key={i} className="text-sm">
                    <p className="font-semibold text-slate-800">{edu.degree} {edu.field && `in ${edu.field}`}</p>
                    <p className="text-slate-600">{edu.institution}</p>
                    {(edu.start_date_if_available || edu.end_date_if_available) && (
                      <p className="text-slate-500 text-xs mt-1">
                        {edu.start_date_if_available} - {edu.end_date_if_available || 'Present'}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Projects */}
          {candidate.projects && candidate.projects.length > 0 && (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Projects</h3>
              <ul className="space-y-4">
                {candidate.projects.map((proj: any, i: number) => (
                  <li key={i} className="text-sm">
                    <p className="font-semibold text-slate-800">{proj.project_name}</p>
                    <p className="text-slate-600 mt-1">{proj.description}</p>
                    {proj.technologies && proj.technologies.length > 0 && (
                      <p className="text-slate-500 mt-1 text-xs">Technologies: {proj.technologies.join(', ')}</p>
                    )}
                    {proj.project_link_if_available && (
                      <a href={proj.project_link_if_available} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs block mt-1">View Project</a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Certifications */}
          {candidate.certifications && candidate.certifications.length > 0 && (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Certifications</h3>
              <ul className="space-y-3">
                {candidate.certifications.map((cert: any, i: number) => (
                  <li key={i} className="text-sm">
                    <p className="font-semibold text-slate-800">{cert.name}</p>
                    <p className="text-slate-600">{cert.issuer}</p>
                    {cert.date_if_available && <p className="text-slate-500 text-xs mt-1">{cert.date_if_available}</p>}
                    {cert.credential_link_if_available && (
                      <a href={cert.credential_link_if_available} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs block mt-1">View Credential</a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Right Column: Job & Analysis */}
        <div className="space-y-6">
          
          {/* Job Requirements */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Job Requirements</h3>
            <div className="space-y-4 text-sm">
              {job.required_skills && job.required_skills.length > 0 && (
                <div>
                  <p className="font-medium text-slate-700">Required Skills</p>
                  <p className="text-slate-600 mt-1">{job.required_skills.join(', ')}</p>
                </div>
              )}
              {job.preferred_skills && job.preferred_skills.length > 0 && (
                <div>
                  <p className="font-medium text-slate-700">Preferred Skills</p>
                  <p className="text-slate-600 mt-1">{job.preferred_skills.join(', ')}</p>
                </div>
              )}
              {job.minimum_experience && (
                <div>
                  <p className="font-medium text-slate-700">Experience Requirement</p>
                  <p className="text-slate-600 mt-1">{job.minimum_experience}</p>
                </div>
              )}
              {job.responsibilities && job.responsibilities.length > 0 && (
                <div>
                  <p className="font-medium text-slate-700">Responsibilities</p>
                  <ul className="list-disc list-inside text-slate-600 mt-1 space-y-1">
                    {job.responsibilities.map((r: string, i: number) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}
              {job.technical_requirements && job.technical_requirements.length > 0 && (
                <div>
                  <p className="font-medium text-slate-700">Technical Requirements</p>
                  <ul className="list-disc list-inside text-slate-600 mt-1 space-y-1">
                    {job.technical_requirements.map((r: string, i: number) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Preliminary Comparison */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Preliminary Comparison</h3>
            
            <div className="space-y-6">
              <div>
                <h4 className="font-medium text-green-700 mb-2">Skills Present</h4>
                {analysis.skills_present && analysis.skills_present.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {analysis.skills_present.map((s: string) => (
                      <span key={s} className="px-2 py-1 bg-green-50 text-green-700 text-sm rounded-md border border-green-200">{s}</span>
                    ))}
                  </div>
                ) : <p className="text-sm text-slate-500">None found.</p>}
              </div>
              
              <div>
                <h4 className="font-medium text-amber-600 mb-2">Skills Requiring Verification</h4>
                {analysis.skills_requiring_verification && analysis.skills_requiring_verification.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {analysis.skills_requiring_verification.map((s: string) => (
                      <span key={s} className="px-2 py-1 bg-amber-50 text-amber-700 text-sm rounded-md border border-amber-200">{s}</span>
                    ))}
                  </div>
                ) : <p className="text-sm text-slate-500">None found.</p>}
              </div>

              <div>
                <h4 className="font-medium text-red-600 mb-2">Potential Skill Gaps</h4>
                <p className="text-xs text-slate-500 mb-2">These skills were requested by the job but were not clearly found in the resume.</p>
                {analysis.potential_skill_gaps && analysis.potential_skill_gaps.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {analysis.potential_skill_gaps.map((s: string) => (
                      <span key={s} className="px-2 py-1 bg-red-50 text-red-700 text-sm rounded-md border border-red-200">{s}</span>
                    ))}
                  </div>
                ) : <p className="text-sm text-slate-500">None found.</p>}
              </div>
            </div>
          </div>

          {/* Professional Claims */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Professional Claims</h3>
            <p className="text-xs text-amber-700 mb-4 bg-amber-50 p-2 rounded border border-amber-200">Resume claims have not yet been independently verified.</p>
            {claims && claims.length > 0 ? (
              <ul className="space-y-4">
                {claims.map((c: any, i: number) => (
                  <li key={i} className="text-sm border-l-2 border-slate-300 pl-3 py-1">
                    <p className="font-medium text-slate-800">"{c.claim_text}"</p>
                    <div className="flex gap-2 mt-2 text-xs items-center">
                      <span className="text-slate-500">Source: {c.source_section}</span>
                      <span className="text-slate-400">•</span>
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded">Unverified</span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No specific professional claims extracted.</p>
            )}
          </div>
          
        </div>
      </div>

      {/* Pipeline Status */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mt-8">
        <h3 className="text-lg font-semibold mb-6 text-slate-800 text-center">Analysis Pipeline Status</h3>
        
        <div className="flex flex-col md:flex-row justify-center items-center md:items-start gap-4 md:gap-8 mb-8 text-sm">
          
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-green-100 text-green-600 flex items-center justify-center font-bold mb-2 border border-green-200">✓</div>
            <span className="font-medium text-slate-700 text-center">Resume Analysis</span>
            <span className="text-green-600 text-xs mt-1">Complete</span>
          </div>
          
          <div className="hidden md:block w-8 h-px bg-slate-300 mt-5"></div>
          
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold mb-2 border border-blue-200">2</div>
            <span className="font-medium text-slate-700 text-center">Evidence Verification</span>
            <span className="text-blue-600 text-xs mt-1">Next Step</span>
          </div>

          <div className="hidden md:block w-8 h-px bg-slate-300 mt-5"></div>
          
          <div className="flex flex-col items-center opacity-50">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center font-bold mb-2 border border-slate-200">3</div>
            <span className="font-medium text-slate-700 text-center">Skill Assessment</span>
            <span className="text-slate-500 text-xs mt-1">Pending</span>
          </div>

          <div className="hidden md:block w-8 h-px bg-slate-300 mt-5"></div>
          
          <div className="flex flex-col items-center opacity-50">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center font-bold mb-2 border border-slate-200">4</div>
            <span className="font-medium text-slate-700 text-center">Verified Skill Profile</span>
            <span className="text-slate-500 text-xs mt-1">Pending</span>
          </div>

          <div className="hidden md:block w-8 h-px bg-slate-300 mt-5"></div>
          
          <div className="flex flex-col items-center opacity-50">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center font-bold mb-2 border border-slate-200">5</div>
            <span className="font-medium text-slate-700 text-center">Interview Intelligence</span>
            <span className="text-slate-500 text-xs mt-1">Pending</span>
          </div>
          
        </div>

        <div className="flex justify-center mt-6 border-t pt-6">
          <Link to={`/evidence/${id}`} className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors shadow-sm">
            Continue to Evidence Verification
          </Link>
        </div>
      </div>

    </div>
  );
}
