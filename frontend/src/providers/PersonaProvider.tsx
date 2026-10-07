"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { PersonaType } from '@/lib/types';
import { PERSONA_CONFIG } from '@/lib/constants';
import { apiPut, API_ROUTES } from '@/lib/api';

interface PersonaContextType {
  persona: PersonaType | null;
  setPersona: (persona: PersonaType) => void;
  config: typeof PERSONA_CONFIG[PersonaType] | null;
}

const PersonaContext = createContext<PersonaContextType>({
  persona: null,
  setPersona: () => {},
  config: null,
});

export const PersonaProvider = ({ children }: { children: React.ReactNode }) => {
  const [persona, setPersonaState] = useState<PersonaType | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem('leadhunter_persona') as PersonaType;
    if (saved && PERSONA_CONFIG[saved]) {
      setPersonaState(saved);
    }
  }, []);

  const setPersona = useCallback((newPersona: PersonaType) => {
    setPersonaState(newPersona);
    try {
      localStorage.setItem('leadhunter_persona', newPersona);
    } catch {}
    // Persist to backend (fire-and-forget; UI stays responsive on failure)
    try {
      const map: Record<string, string> = { job_hunter: 'JOB_HUNTER', freelancer: 'FREELANCER', agency: 'AGENCY' };
      const backendPersona = map[newPersona] || 'FREELANCER';
      apiPut(`${API_ROUTES.SETTINGS}/persona`, { persona: backendPersona }).catch(() => {});
    } catch {}
  }, []);

  const config = persona ? PERSONA_CONFIG[persona] : null;
  const value = useMemo(() => ({ persona, setPersona, config }), [persona, setPersona, config]);

  return (
    <PersonaContext.Provider value={value}>
      {children}
    </PersonaContext.Provider>
  );
};

export const usePersonaContext = () => useContext(PersonaContext);
