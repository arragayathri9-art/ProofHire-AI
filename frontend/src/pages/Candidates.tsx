import { useEffect, useState } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, ShieldCheck, ArrowRight, PlusCircle, Search } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

export default function Candidates() {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const { setActiveAnalysis } = useAnalysis();
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE_URL}/api/candidates`).catch(() => ({ data: [] })),
      axios.get(`${API_BASE_URL}/api/analyses`).catch(() => ({ data: [] }))
    ]).then(([candRes, analysesRes]) => {
      setCandidates(candRes.data || []);
      setAnalyses(analysesRes.data || []);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  const getCandidateAnalysis = (candId: number) => {
    return analyses.find(a => a.candidate_id === candId);
  };

  const handleOpenEvidence = (candidate: any, analysis: any) => {
    setActiveAnalysis(analysis.id, {
      name: candidate.name,
      jobTitle: analysis.job_title,
      candidateId: candidate.id
    });
    navigate(`/evidence/${analysis.id}`);
  };

  const filteredCandidates = candidates.filter(c => 
    (c.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (c.email || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Candidates</h2>
          <p className="text-slate-500 text-sm mt-0.5">All candidates registered and analyzed in ProofHire</p>
        </div>
        <Link 
          to="/analysis/new" 
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-xs transition-colors shadow-sm self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Analysis</span>
        </Link>
      </div>

      {/* Search Bar */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 flex items-center gap-2 shadow-xs">
        <Search className="w-4 h-4 text-slate-400 ml-1" />
        <input 
          type="text" 
          value={search} 
          onChange={e => setSearch(e.target.value)} 
          placeholder="Search candidates by name or email..."
          className="w-full text-sm bg-transparent outline-none text-slate-800 placeholder-slate-400"
        />
      </div>

      {/* Candidate List Card */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-slate-400 text-sm">Loading candidates...</div>
        ) : filteredCandidates.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-sm">
            <p className="font-semibold text-slate-700">No candidates have been analyzed yet.</p>
            <p className="text-xs text-slate-400 mt-1">Upload a resume and job description to start candidate verification.</p>
            <Link 
              to="/analysis/new" 
              className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors"
            >
              <span>Start New Analysis</span>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/70 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-6">Candidate</th>
                  <th className="py-3.5 px-6">Target Role</th>
                  <th className="py-3.5 px-6">Experience & Projects</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {filteredCandidates.map((c: any) => {
                  const analysis = getCandidateAnalysis(c.id);
                  return (
                    <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-4 px-6">
                        <Link to={`/candidates/${c.id}`} className="flex items-center gap-3 group">
                          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-700 font-bold flex items-center justify-center border border-blue-100 text-sm">
                            {c.name ? c.name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
                          </div>
                          <div>
                            <p className="font-bold text-slate-900 group-hover:text-blue-600 transition-colors">{c.name}</p>
                            {c.email && (
                              <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                                <Mail className="w-3 h-3" />
                                <span>{c.email}</span>
                              </p>
                            )}
                          </div>
                        </Link>
                      </td>
                      <td className="py-4 px-6 text-slate-700">
                        {analysis ? (
                          <div>
                            <p className="font-semibold text-slate-800 text-xs">{analysis.job_title}</p>
                            <span className="text-xs text-slate-400">{analysis.job_company || 'Tech'}</span>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">Direct Entry</span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-xs text-slate-500">
                        <span>{c.experience?.length || 0} Exp. items</span>
                        <span className="mx-1.5">•</span>
                        <span>{c.projects?.length || 0} Projects</span>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link 
                            to={`/candidates/${c.id}`} 
                            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg text-xs transition-colors"
                          >
                            Profile
                          </Link>
                          {analysis && (
                            <button
                              onClick={() => handleOpenEvidence(c, analysis)}
                              className="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold rounded-lg text-xs transition-colors flex items-center gap-1 cursor-pointer"
                            >
                              <ShieldCheck className="w-3.5 h-3.5" />
                              <span>Evidence</span>
                              <ArrowRight className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
