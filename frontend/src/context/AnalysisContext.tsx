import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../api/config';

export interface ActiveCandidateInfo {
  name: string;
  jobTitle: string;
  candidateId?: number;
  currentStage?: string;
  continueRoute?: string;
  pipelineStages?: {
    resume?: 'completed' | 'current' | 'pending' | string;
    evidence?: 'completed' | 'current' | 'pending' | string;
    assessment?: 'completed' | 'current' | 'pending' | string;
    profile?: 'completed' | 'current' | 'pending' | string;
    interview?: 'completed' | 'current' | 'pending' | string;
    report?: 'completed' | 'current' | 'pending' | string;
  };
}

interface AnalysisContextType {
  activeAnalysisId: number | null;
  activeCandidate: ActiveCandidateInfo | null;
  setActiveAnalysis: (id: number, candidateInfo?: Partial<ActiveCandidateInfo>) => void;
  clearActiveAnalysis: () => void;
  refreshActiveAnalysis: () => Promise<void>;
}

const AnalysisContext = createContext<AnalysisContextType>({
  activeAnalysisId: null,
  activeCandidate: null,
  setActiveAnalysis: () => {},
  clearActiveAnalysis: () => {},
  refreshActiveAnalysis: async () => {},
});

export const AnalysisProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeAnalysisId, setActiveAnalysisIdState] = useState<number | null>(() => {
    const saved = localStorage.getItem('proofhire_active_analysis_id');
    return saved ? parseInt(saved, 10) : null;
  });

  const [activeCandidate, setActiveCandidateState] = useState<ActiveCandidateInfo | null>(() => {
    const saved = localStorage.getItem('proofhire_active_candidate');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const fetchAnalysisInfo = async (id: number): Promise<ActiveCandidateInfo | null> => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/analyses/${id}`);
      const data = res.data;
      const stage = data.current_stage || 'Resume Analysis';
      
      let continueRoute = `/analysis/result/${id}`;
      if (stage === 'Interview Intelligence') continueRoute = `/interview/${id}`;
      else if (stage === 'Verified Skill Profile') continueRoute = `/skill-profile/${id}`;
      else if (stage === 'Skill Assessment') continueRoute = `/assessment/${id}`;
      else if (stage === 'Evidence Verification') continueRoute = `/evidence/${id}`;

      const info: ActiveCandidateInfo = {
        name: data.candidate?.name || 'Candidate',
        jobTitle: data.job?.title || 'Target Job',
        candidateId: data.candidate?.id,
        currentStage: stage,
        continueRoute: continueRoute,
        pipelineStages: data.pipeline_stages || {
          resume: 'completed',
          evidence: 'current',
          assessment: 'pending',
          profile: 'pending',
          interview: 'pending',
          report: 'pending'
        }
      };
      return info;
    } catch (err) {
      console.warn('Could not fetch active analysis details:', err);
      return null;
    }
  };

  const setActiveAnalysis = (id: number, candidateInfo?: Partial<ActiveCandidateInfo>) => {
    setActiveAnalysisIdState(id);
    localStorage.setItem('proofhire_active_analysis_id', id.toString());
    
    if (candidateInfo && candidateInfo.name && candidateInfo.jobTitle) {
      const merged: ActiveCandidateInfo = {
        name: candidateInfo.name,
        jobTitle: candidateInfo.jobTitle,
        candidateId: candidateInfo.candidateId,
        currentStage: candidateInfo.currentStage || 'Resume Analysis',
        continueRoute: candidateInfo.continueRoute || `/evidence/${id}`,
        pipelineStages: candidateInfo.pipelineStages
      };
      setActiveCandidateState(merged);
      localStorage.setItem('proofhire_active_candidate', JSON.stringify(merged));
    }
    
    // Always refresh full metadata in background
    fetchAnalysisInfo(id).then(fetched => {
      if (fetched) {
        setActiveCandidateState(prev => {
          const updated = { ...(prev || {}), ...fetched, ...(candidateInfo || {}) };
          localStorage.setItem('proofhire_active_candidate', JSON.stringify(updated));
          return updated;
        });
      }
    });
  };

  const clearActiveAnalysis = () => {
    setActiveAnalysisIdState(null);
    setActiveCandidateState(null);
    localStorage.removeItem('proofhire_active_analysis_id');
    localStorage.removeItem('proofhire_active_candidate');
  };

  const refreshActiveAnalysis = async () => {
    if (activeAnalysisId) {
      const updated = await fetchAnalysisInfo(activeAnalysisId);
      if (updated) {
        setActiveCandidateState(updated);
        localStorage.setItem('proofhire_active_candidate', JSON.stringify(updated));
      }
    }
  };

  // If activeAnalysisId exists on startup, populate it
  useEffect(() => {
    if (activeAnalysisId) {
      fetchAnalysisInfo(activeAnalysisId).then(info => {
        if (info) {
          setActiveCandidateState(info);
          localStorage.setItem('proofhire_active_candidate', JSON.stringify(info));
        }
      });
    }
  }, [activeAnalysisId]);

  return (
    <AnalysisContext.Provider value={{ activeAnalysisId, activeCandidate, setActiveAnalysis, clearActiveAnalysis, refreshActiveAnalysis }}>
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => useContext(AnalysisContext);
