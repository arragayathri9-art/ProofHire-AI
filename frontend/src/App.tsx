import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Briefcase, 
  FileSearch, 
  ShieldCheck, 
  BrainCircuit, 
  Award, 
  MessageSquareText, 
  FileBarChart,
  User,
  ArrowRight,
  X
} from 'lucide-react';
import { AnalysisProvider, useAnalysis } from './context/AnalysisContext';

import Dashboard from './pages/Dashboard';
import Candidates from './pages/Candidates';
import CandidateDetail from './pages/CandidateDetail';
import Jobs from './pages/Jobs';
import NewAnalysis from './pages/NewAnalysis';
import AnalysisResult from './pages/AnalysisResult';
import EvidenceCenter from './pages/EvidenceCenter';
import SkillAssessment from './pages/SkillAssessment';
import SkillProfile from './pages/SkillProfile';
import InterviewIntelligence from './pages/InterviewIntelligence';
import Reports from './pages/Reports';

function AppLayout() {
  const { activeAnalysisId, activeCandidate, clearActiveAnalysis } = useAnalysis();
  const location = useLocation();

  const evidenceLink = activeAnalysisId ? `/evidence/${activeAnalysisId}` : '/evidence';
  const assessmentLink = activeAnalysisId ? `/assessment/${activeAnalysisId}` : '/assessment';
  const profileLink = activeAnalysisId ? `/skill-profile/${activeAnalysisId}` : '/skill-profile';
  const interviewLink = activeAnalysisId ? `/interview/${activeAnalysisId}` : '/interview';
  const reportsLink = activeAnalysisId ? `/reports/${activeAnalysisId}` : '/reports';

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0">
        {/* Brand */}
        <div className="p-6 border-b border-slate-100">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center font-extrabold shadow-sm">
              PH
            </div>
            <div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight leading-tight">
                ProofHire<span className="text-blue-600">.ai</span>
              </h1>
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Evidence Intelligence</p>
            </div>
          </Link>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <SidebarNavItem 
            to="/" 
            icon={<LayoutDashboard size={18} />} 
            label="Dashboard" 
            active={isActive('/')}
          />
          <SidebarNavItem 
            to="/candidates" 
            icon={<Users size={18} />} 
            label="Candidates" 
            active={isActive('/candidates')}
          />
          <SidebarNavItem 
            to="/jobs" 
            icon={<Briefcase size={18} />} 
            label="Jobs" 
            active={isActive('/jobs')}
          />
          <SidebarNavItem 
            to="/analysis/new" 
            icon={<FileSearch size={18} />} 
            label="New Analysis" 
            active={isActive('/analysis/new')}
          />
          
          {/* Verification Section */}
          <div className="pt-6 pb-2 px-3">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Verification</p>
          </div>

          <SidebarNavItem 
            to={evidenceLink} 
            icon={<ShieldCheck size={18} />} 
            label="Evidence Center" 
            active={isActive('/evidence')}
          />
          <SidebarNavItem 
            to={assessmentLink} 
            icon={<BrainCircuit size={18} />} 
            label="Skill Assessment" 
            active={isActive('/assessment')}
          />
          <SidebarNavItem 
            to={profileLink} 
            icon={<Award size={18} />} 
            label="Verified Skill Profile" 
            active={isActive('/skill-profile')}
          />
          <SidebarNavItem 
            to={interviewLink} 
            icon={<MessageSquareText size={18} />} 
            label="Interview Intelligence" 
            active={isActive('/interview')}
          />

          {/* Reports Section */}
          <div className="pt-3 border-t border-slate-100 my-2"></div>

          <SidebarNavItem 
            to={reportsLink} 
            icon={<FileBarChart size={18} />} 
            label="Reports" 
            active={isActive('/reports')}
          />
        </nav>

        {/* Active Candidate Widget at Bottom of Sidebar */}
        {activeAnalysisId && (
          <div className="p-3 border-t border-slate-100 bg-slate-50/70">
            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded">
                  Active Session
                </span>
                <span className="text-[11px] font-mono text-slate-400">#{activeAnalysisId}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs shrink-0">
                  <User size={12} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-slate-800 truncate">
                    {activeCandidate?.name || `Candidate #${activeAnalysisId}`}
                  </p>
                  <p className="text-[11px] text-slate-500 truncate">
                    {activeCandidate?.jobTitle || 'Target Job'}
                  </p>
                </div>
              </div>
              <Link 
                to={`/evidence/${activeAnalysisId}`} 
                className="mt-1 flex items-center justify-between text-[11px] font-semibold text-blue-600 hover:text-blue-700 pt-1 border-t border-slate-100"
              >
                <span>Jump to Evidence</span>
                <ArrowRight size={12} />
              </Link>
            </div>
          </div>
        )}
      </aside>

      {/* Main App Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Active Candidate Bar */}
        <header className="bg-white border-b border-slate-200 px-8 py-3 shrink-0 flex items-center justify-between gap-4 shadow-xs">
          {activeAnalysisId && activeCandidate ? (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between w-full gap-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs shrink-0">
                  <User size={15} />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-bold text-slate-900">{activeCandidate.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                      #{activeAnalysisId}
                    </span>
                    <span className="text-slate-300 hidden sm:inline">•</span>
                    <span className="text-xs text-slate-600 font-medium">{activeCandidate.jobTitle}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 text-[11px]">
                    <span className="text-slate-400">Current Stage:</span>
                    <span className="font-semibold text-blue-700 bg-blue-50/80 px-2 py-0.2 rounded border border-blue-100">
                      {activeCandidate.currentStage || 'Resume Analysis'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Link
                  to={`/analysis/result/${activeAnalysisId}`}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-colors"
                >
                  View Candidate
                </Link>
                <Link
                  to={activeCandidate.continueRoute || `/evidence/${activeAnalysisId}`}
                  className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-all active:scale-95"
                >
                  <span>Continue Analysis</span>
                  <ArrowRight size={13} />
                </Link>
                <button
                  onClick={clearActiveAnalysis}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
                  title="Clear active candidate selection"
                >
                  <X size={15} />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between w-full text-xs">
              <span className="font-medium text-slate-500">
                ProofHire AI Command Center • <span className="text-slate-700 font-semibold">Evidence-Based Hiring Intelligence</span>
              </span>
              <Link 
                to="/analysis/new" 
                className="text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 hover:underline"
              >
                <span>+ Start New Candidate Analysis</span>
              </Link>
            </div>
          )}
        </header>

        {/* Scrollable Main Workspace */}
        <main className="flex-1 overflow-auto p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/candidates" element={<Candidates />} />
            <Route path="/candidates/:id" element={<CandidateDetail />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/analysis/new" element={<NewAnalysis />} />
            <Route path="/analysis/result/:id" element={<AnalysisResult />} />
            <Route path="/evidence" element={<EvidenceCenter />} />
            <Route path="/evidence/:id" element={<EvidenceCenter />} />
            <Route path="/assessment" element={<SkillAssessment />} />
            <Route path="/assessment/:id" element={<SkillAssessment />} />
            <Route path="/skill-profile" element={<SkillProfile />} />
            <Route path="/skill-profile/:id" element={<SkillProfile />} />
            <Route path="/interview" element={<InterviewIntelligence />} />
            <Route path="/interview/:id" element={<InterviewIntelligence />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/reports/:id" element={<Reports />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function SidebarNavItem({ to, icon, label, active = false }: any) {
  return (
    <Link 
      to={to} 
      className={`flex items-center px-3 py-2.5 text-xs font-semibold rounded-xl transition-all ${
        active 
          ? 'bg-blue-600 text-white shadow-xs' 
          : 'text-slate-600 hover:text-blue-600 hover:bg-blue-50/70'
      }`}
    >
      <span className={`mr-2.5 ${active ? 'text-white' : 'text-slate-400'}`}>{icon}</span>
      <span className="truncate">{label}</span>
    </Link>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AnalysisProvider>
        <AppLayout />
      </AnalysisProvider>
    </BrowserRouter>
  );
}
