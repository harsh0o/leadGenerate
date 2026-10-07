"use client";

import { useState, useEffect, useCallback } from 'react';
import { SearchProfile, SearchProfileCreate } from '@/lib/types';
import { apiGet, apiPost, apiPut, apiDelete, API_ROUTES } from '@/lib/api';

export function useProfiles() {
  const [profiles, setProfiles] = useState<SearchProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchProfiles = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await apiGet<SearchProfile[] | { items: SearchProfile[] }>(API_ROUTES.PROFILES);
      const list = Array.isArray(data) ? data : (data as { items?: SearchProfile[] })?.items ?? [];
      setProfiles(list);
      setError(null);
    } catch (err: unknown) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  const createProfile = async (data: SearchProfileCreate) => {
    try {
      const newProfile = await apiPost<SearchProfile>(API_ROUTES.PROFILES, data);
      setProfiles(prev => [...prev, newProfile]);
      return newProfile;
    } catch (err) {
      console.error("Failed to create profile", err);
      throw err;
    }
  };

  const updateProfile = async (id: string | number, data: Partial<SearchProfileCreate>) => {
    try {
      const updated = await apiPut<SearchProfile>(`${API_ROUTES.PROFILES}/${id}`, data);
      setProfiles(prev => prev.map(p => p.id === id ? updated : p));
      return updated;
    } catch (err) {
      console.error("Failed to update profile", err);
      throw err;
    }
  };

  const deleteProfile = async (id: string | number) => {
    try {
      await apiDelete(`${API_ROUTES.PROFILES}/${id}`);
      setProfiles(prev => prev.filter(p => p.id !== id));
    } catch (err) {
      console.error("Failed to delete profile", err);
      throw err;
    }
  };

  const toggleProfile = async (id: string | number, currentStatus: boolean) => {
    try {
      const updated = await apiPut<SearchProfile>(`${API_ROUTES.PROFILES}/${id}/toggle`, { is_active: !currentStatus });
      // Backend now returns full profile; merge defensively for backwards compat
      setProfiles(prev => prev.map(p => {
        if (p.id !== id) return p;
        if (updated && (updated as SearchProfile).tags) return updated as SearchProfile;
        return { ...p, ...(updated as object) } as SearchProfile;
      }));
      return updated;
    } catch (err) {
      console.error("Failed to toggle profile", err);
      throw err;
    }
  };

  return {
    profiles,
    isLoading,
    error,
    fetchProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    toggleProfile
  };
}
