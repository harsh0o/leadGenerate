"use client";

import { useState, useCallback } from 'react';
import { AIDraft, DraftRequest } from '@/lib/types';
import { apiGet, apiPost, apiDelete, API_ROUTES } from '@/lib/api';

export function useDrafts() {
  const [drafts, setDrafts] = useState<AIDraft[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchDrafts = useCallback(async (leadId: string | number) => {
    setIsLoading(true);
    try {
      const data = await apiGet<AIDraft[] | { drafts: AIDraft[]; items: AIDraft[] }>(`${API_ROUTES.DRAFTS}/lead/${leadId}`);
      const list = Array.isArray(data) ? data : ((data as unknown as { drafts?: AIDraft[]; items?: AIDraft[] }).drafts ?? (data as unknown as { items?: AIDraft[] }).items ?? []);
      setDrafts(list);
      setError(null);
    } catch (err: unknown) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const generateDraft = async (request: DraftRequest) => {
    setIsLoading(true);
    try {
      const lid = Number(request.lead_id);
      if (!Number.isInteger(lid) || lid <= 0) {
        throw new Error(`Invalid lead_id '${request.lead_id}'`);
      }
      const normType = String((request as unknown as { draft_type?: unknown; type?: unknown }).draft_type || (request as unknown as { type?: unknown }).type || 'COLD_DM').trim().toUpperCase().replace(/ /g, '_');
      const normTone = String(request.tone || 'PROFESSIONAL').trim().toUpperCase();
      const customInstructions = (request as unknown as { custom_instructions?: string; instructions?: string }).custom_instructions ?? (request as unknown as { instructions?: string }).instructions ?? '';
      // Send canonical fields only: strict backends (extra=forbid) reject aliases.
      const newDraft = await apiPost<AIDraft>(`${API_ROUTES.DRAFTS}/generate`, {
        lead_id: lid,
        draft_type: normType,
        tone: normTone,
        custom_instructions: customInstructions,
      });
      setDrafts(prev => [newDraft, ...prev]);
      return newDraft;
    } catch (err: unknown) {
      console.error("Failed to generate draft", err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const deleteDraft = async (draftId: string | number) => {
    try {
      await apiDelete(`${API_ROUTES.DRAFTS}/${draftId}`);
      setDrafts(prev => prev.filter(d => d.id !== draftId));
    } catch (err) {
      console.error("Failed to delete draft", err);
      throw err;
    }
  };

  return {
    drafts,
    isLoading,
    error,
    fetchDrafts,
    generateDraft,
    deleteDraft
  };
}
