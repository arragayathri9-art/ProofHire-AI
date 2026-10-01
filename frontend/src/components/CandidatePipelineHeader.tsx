import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { User, CheckCircle2, ChevronRight, Briefcase } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';

interface Props {
  analysisId?: number | string;
  candidateName?: string;
  jobTitle?: string;
}

export default function CandidatePipelineHeader({ analysisId, candidateName, jobTitle }: Props) {
  const { activeAnalysisId, activeCandidate } = useAnalysis();
  const location = useLocation();

  const currentId = analysisId || activeAnalysisId;
  const name = candidateName || activeCandidate?.name || 'Active Candidate';
  const role = jobTitle || activeCandidate?.jobTitle || 'Target Role';

  if (!currentId) return null;

  const steps = [
    { label: 'Resume Analysis', path: `/analysis/result/${currentId}`, id: 'resume' },
    { label: 'Evidence Verification', path: `/evidence/${currentId}`, id: 'evidence' },
    { label: 'Skill Assessment', path: `/assessment/${currentId}`, id: 'assessment' },
    { label: 'Verified Skill Profile', path: `/skill-profile/${currentId}`, id: 'profile' },
    { label: 'Interview Intelligence', path: `/interview/${currentId}`, id: 'interview' },
  ];

  const getCurrentStepIndex = () => {
    const p = location.pathname;
    if (p.includes('/analysis/result')) return 0;
    if (p.includes('/evidence')) return 1;
    if (p.includes('/assessment')) return 2;
    if (p.includes('/skill-profile')) return 3;
    if (p.includes('/interview')) return 4;
    return -1;
  };

  const currentIndex = getCurrentStepIndex();

  const getStageState = (stepId: string, idx: number): 'completed' | 'current' | 'pending' => {
    if (idx === currentIndex) return 'current';
    
    // Check from stored pipelineStages if available
    const stages = activeCandidate?.pipelineStages;
    if (stages) {
      const stageVal = (stages as any)[stepId];
      if (stageVal === 'completed') return 'completed';
      if (stageVal === 'pending') return 'pending';
    }
    
    // Fallback based on position relative to currentIndex
    if (currentIndex >= 0 && idx < currentIndex) return 'completed';
    return 'pending';
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6 shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-3 mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">
            <User className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-800 text-lg leading-tight">{name}</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-medium">
                Analysis #{currentId}
              </span>
            </div>
            <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
              <Briefcase className="w-3.5 h-3.5 text-slate-400" />
              <span>Target Job: <strong className="text-slate-700 font-medium">{role}</strong></span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-medium">
          <span className="text-slate-400">Current Pipeline:</span>
          <span className="text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-1 rounded-md font-semibold">
            {currentIndex >= 0 ? steps[currentIndex].label : 'In Progress'}
          </span>
          <Link
            to={`/reports/${currentId}`}
            className="ml-2 text-xs font-semibold px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 transition-colors"
          >
            Final Report
          </Link>
        </div>
      </div>

      {/* Interactive Step Navigator with Completed / Current / Pending states */}
      <div className="flex items-center gap-2 overflow-x-auto py-1 text-xs">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider shrink-0 mr-1 hidden sm:inline">
          Pipeline:
        </span>
        {steps.map((step, idx) => {
          const state = getStageState(step.id, idx);
          const isCurrent = state === 'current';
          const isCompleted = state === 'completed';
          const isPending = state === 'pending';

          const content = (
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors font-medium ${
                isCurrent
                  ? 'bg-blue-600 text-white shadow-xs'
                  : isCompleted
                  ? 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 cursor-pointer'
                  : 'bg-slate-50 text-slate-400 border border-slate-200 cursor-not-allowed opacity-75'
              }`}
              title={isPending ? 'Pending: Requires previous stage completion' : step.label}
            >
              <span className={`w-4 h-4 rounded-full text-[10px] font-bold flex items-center justify-center ${
                isCurrent ? 'bg-white text-blue-600' : isCompleted ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-500'
              }`}>
                {idx + 1}
              </span>
              {isCompleted && !isCurrent && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />}
              <span>{step.label}</span>
              <span className={`text-[10px] ml-1 px-1.5 py-0.2 rounded font-semibold uppercase ${
                isCurrent ? 'bg-blue-700/50 text-blue-100' : isCompleted ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'
              }`}>
                {state}
              </span>
              {isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-white ml-0.5 animate-pulse"></span>}
            </div>
          );

          return (
            <React.Fragment key={step.id}>
              {/* Only allow navigation if stage is completed or current. Disallow invalid navigation for pending stages. */}
              {isPending ? (
                <div>{content}</div>
              ) : (
                <Link to={step.path}>{content}</Link>
              )}
              {idx < steps.length - 1 && (
                <ChevronRight className="w-3.5 h-3.5 text-slate-300 shrink-0 mx-0.5" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
