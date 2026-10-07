"use client";

import { useState, useEffect, useCallback } from 'react';
import { Lead, LeadUpdate } from '@/lib/types';
import { apiGet, apiPatch, apiDelete, API_ROUTES } from '@/lib/api';

interface LeadsFilters {
  platform?: string;
  kanban_status?: string;
  search?: string;
}

export function useLeads(initialFilters?: LeadsFilters) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchLeads = useCallback(async (filters?: LeadsFilters) => {
    setIsLoading(true);
    try {
      const query = new URLSearchParams();
      if (filters?.platform) query.append('platform', filters.platform);
      if (filters?.kanban_status) query.append('status', filters.kanban_status);
      if (filters?.search) query.append('search', filters.search);
      
      const queryString = query.toString();
      const url = `${API_ROUTES.LEADS}${queryString ? `?${queryString}` : ''}`;
      
      const data = await apiGet<Lead[] | { items: Lead[] }>(url);
      const list = Array.isArray(data) ? data : (data as { items?: Lead[] })?.items ?? [];
      setLeads(list);
      setError(null);
    } catch (err: unknown) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const filtersKey = JSON.stringify(initialFilters ?? {});
  useEffect(() => {
    fetchLeads(JSON.parse(filtersKey));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchLeads, filtersKey]);

  const updateLeadStatus = async (id: string | number, status: string) => {
    try {
      const updated = await apiPatch<Lead>(`${API_ROUTES.LEADS}/${id}/status`, { status });
      setLeads(prev => prev.map(l => l.id === id ? updated : l));
      return updated;
    } catch (err) {
      console.error("Failed to update status", err);
      throw err;
    }
  };

  const updateLeadNotes = async (id: string | number, notes: string) => {
    try {
      const updated = await apiPatch<Lead>(`${API_ROUTES.LEADS}/${id}/notes`, { notes });
      setLeads(prev => prev.map(l => l.id === id ? updated : l));
      return updated;
    } catch (err) {
      console.error("Failed to update notes", err);
      throw err;
    }
  };

  const deleteLead = async (id: string | number) => {
    try {
      await apiDelete(`${API_ROUTES.LEADS}/${id}`);
      setLeads(prev => prev.filter(l => l.id !== id));
    } catch (err) {
      console.error("Failed to delete lead", err);
      throw err;
    }
  };

  return {
    leads,
    isLoading,
    error,
    fetchLeads,
    updateLeadStatus,
    updateLeadNotes,
    deleteLead
  };
}
