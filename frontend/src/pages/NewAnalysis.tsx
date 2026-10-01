import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../api/config';

export default function NewAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState('');
  const [jobCompany, setJobCompany] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { setActiveAnalysis } = useAnalysis();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !jobTitle || !jobDescription) {
      setError('Please provide a resume PDF, job title, and description.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Create job first
      const jobRes = await axios.post(`${API_BASE_URL}/api/jobs`, {
        title: jobTitle,
        company: jobCompany,
        description: jobDescription
      });
      
      const jobId = jobRes.data.id;
      
      // Submit analysis
      const formData = new FormData();
      formData.append('file', file);
      formData.append('job_id', jobId.toString());
      
      const analysisRes = await axios.post(`${API_BASE_URL}/api/candidates/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const newAnalysisId = analysisRes.data.analysis_id;
      setActiveAnalysis(newAnalysisId, {
        name: analysisRes.data.candidate_name || 'Candidate',
        jobTitle: analysisRes.data.job_title || jobTitle,
        candidateId: analysisRes.data.candidate_id
      });
      navigate(`/analysis/result/${newAnalysisId}`);
    } catch (err: any) {
      const rawDetail = err.response?.data?.detail || err.message || '';
      if (rawDetail.includes('503') || rawDetail.toLowerCase().includes('unavailable') || rawDetail.toLowerCase().includes('quota') || rawDetail.toLowerCase().includes('resource')) {
        setError('AI service is temporarily busy. Please try again.');
      } else if (rawDetail.toLowerCase().includes('network') || !err.response) {
        setError('Backend server is currently unavailable. Please verify the server is running.');
      } else if (rawDetail.toLowerCase().includes('pdf') || rawDetail.toLowerCase().includes('extract')) {
        setError('Unable to read text from this PDF file. Please ensure it contains selectable text.');
      } else {
        setError(rawDetail || 'Failed to complete resume analysis. Please try again.');
      }
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">New Candidate Analysis</h2>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl mb-6 flex items-center justify-between gap-3 text-xs">
          <span>{error}</span>
          <button
            type="button"
            onClick={handleSubmit}
            className="px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold shrink-0 cursor-pointer"
          >
            Try Again
          </button>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-8 bg-white p-8 rounded-xl shadow-sm border border-slate-200">
        
        {/* Step 1 */}
        <div>
          <h3 className="text-lg font-semibold mb-4 border-b pb-2">Step 1: Candidate Resume</h3>
          <div className="mt-2">
            <input type="file" accept=".pdf" onChange={handleFileChange} className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
          </div>
        </div>

        {/* Step 2 */}
        <div>
          <h3 className="text-lg font-semibold mb-4 border-b pb-2">Step 2: Target Job</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Job Title</label>
              <input type="text" value={jobTitle} onChange={e => setJobTitle(e.target.value)} className="w-full border border-slate-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Company</label>
              <input type="text" value={jobCompany} onChange={e => setJobCompany(e.target.value)} className="w-full border border-slate-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Job Description</label>
              <textarea rows={6} value={jobDescription} onChange={e => setJobDescription(e.target.value)} className="w-full border border-slate-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500" required></textarea>
            </div>
          </div>
        </div>

        <button type="submit" disabled={loading} className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400">
          {loading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing Candidate...
            </>
          ) : 'Analyze Candidate'}
        </button>
      </form>
    </div>
  );
}
