import { useEffect, useState } from 'react';
import axios from 'axios';
import { Briefcase, Building, PlusCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { API_BASE_URL } from '../api/config';

export default function Jobs() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/jobs`)
      .then(res => {
        setJobs(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Job Profiles</h2>
          <p className="text-slate-500 text-sm mt-0.5">Target roles with AI-extracted required and preferred skills</p>
        </div>
        <Link 
          to="/analysis/new" 
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-xs transition-colors shadow-sm self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Job & Analysis</span>
        </Link>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-slate-400 text-sm">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-sm">
            <p className="font-semibold text-slate-700">No job descriptions added yet.</p>
            <p className="text-xs text-slate-400 mt-1">Start a new analysis to create a target job profile.</p>
            <Link 
              to="/analysis/new" 
              className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors"
            >
              <span>Create Target Job</span>
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {jobs.map((job: any) => (
              <div key={job.id} className="p-6 hover:bg-slate-50/50 transition-colors space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 font-bold flex items-center justify-center border border-indigo-100">
                      <Briefcase className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 text-base">{job.title}</h3>
                      <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <Building className="w-3.5 h-3.5 text-slate-400" />
                        <span>{job.company || 'Direct Employer'}</span>
                        {job.minimum_experience && (
                          <>
                            <span className="text-slate-300">•</span>
                            <span>Exp: {job.minimum_experience}</span>
                          </>
                        )}
                      </p>
                    </div>
                  </div>

                  <Link 
                    to="/analysis/new" 
                    className="px-3.5 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold rounded-lg text-xs self-start sm:self-auto transition-colors"
                  >
                    Match Candidate
                  </Link>
                </div>

                {/* Required Skills */}
                {job.required_skills && job.required_skills.length > 0 && (
                  <div className="pt-2">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Required Skills</p>
                    <div className="flex flex-wrap gap-1.5">
                      {job.required_skills.map((s: string, idx: number) => (
                        <span key={idx} className="px-2.5 py-0.5 bg-slate-100 text-slate-700 border border-slate-200 rounded-md text-xs font-medium">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
