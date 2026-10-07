"use client";

import { useState, useEffect, useCallback } from 'react';
import { ScanEvent } from '@/lib/types';
import { createSSEConnection, API_ROUTES, apiPost } from '@/lib/api';

export function useScan() {
  const [events, setEvents] = useState<ScanEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [scanStatus, setScanStatus] = useState<'idle' | 'scanning' | 'error'>('idle');

  useEffect(() => {
    let sse: EventSource | null = null;
    try {
      sse = createSSEConnection(API_ROUTES.SCAN_LIVE);
    } catch {
      return;
    }

    sse.onopen = () => setIsConnected(true);

    const pushEvent = (evtName: string, rawData: string) => {
      try {
        let raw: Record<string, unknown> = {};
        try {
          const parsed: unknown = JSON.parse(rawData || '{}');
          raw = (typeof parsed === 'object' && parsed !== null ? parsed : { message: rawData }) as Record<string, unknown>;
        } catch {
          raw = { message: rawData };
        }
        // Backend named events: scan_started/item_found/lead_qualified/scan_completed/error/ping
        let type: ScanEvent['type'] = 'info';
        let message = String((raw.message as string) || rawData || evtName);
        let platform = String((raw.platform as string) || 'system');
        if (evtName === 'item_found') {
          type = 'found';
          const title = typeof raw.title === 'string' ? raw.title : '';
          const content = typeof raw.content === 'string' ? raw.content.slice(0, 120) : '';
          message = title || content || `Found item on ${platform}...`;
        } else if (evtName === 'lead_qualified') {
          type = 'found';
          const n = (raw.leads_found as number) ?? (raw.total as number) ?? 0;
          message = `Qualified ${n} lead(s)${raw.platform ? ` on ${raw.platform}` : ''}`;
          if (raw.platform) platform = String(raw.platform);
        } else if (evtName === 'scan_started') {
          type = 'info';
          message = `Scan started (profile ${String(raw.profile_id ?? '')})`;
          setScanStatus('scanning');
        } else if (evtName === 'scan_completed') {
          type = 'info';
          message = 'Scan completed';
          setScanStatus('idle');
        } else if (evtName === 'error') {
          type = 'error';
          message = String(raw.message || 'Scan error');
        } else if (evtName === 'ping') {
          return;
        }
        const data: ScanEvent = {
          id: typeof raw.id === 'string' && raw.id ? raw.id : (typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`),
          job_id: String(raw.job_id ?? raw.profile_id ?? ''),
          platform,
          type,
          message: String(message),
          timestamp: typeof raw.timestamp === 'string' ? raw.timestamp : new Date().toISOString(),
        };
        setEvents(prev => [...prev.slice(-499), data]);
      } catch {
        // ignore malformed event
      }
    };

    const names = ['scan_started', 'item_found', 'lead_qualified', 'scan_completed', 'error', 'ping'];
    const handlers: Array<[string, (e: MessageEvent) => void]> = names.map((n) => {
      const h = (e: MessageEvent) => pushEvent(n, e.data as string);
      sse.addEventListener(n, h as EventListener);
      return [n, h];
    });
    // Fallback for unnamed messages
    sse.onmessage = (event) => pushEvent('message', event.data as string);

    sse.onerror = () => {
      setIsConnected(false);
      setScanStatus(prev => (prev === 'scanning' ? 'error' : prev));
      try { sse.close(); } catch { /* ignore */ }
    };

    return () => {
      try {
        handlers.forEach(([n, h]) => sse?.removeEventListener(n, h as EventListener));
      } catch {}
      sse?.close();
    };
  }, []);

  const triggerScan = useCallback(async (profileId?: string | number, platforms?: string[]) => {
    try {
      if (profileId === undefined || profileId === null || String(profileId).trim() === '') {
        console.error("triggerScan requires profileId");
        setScanStatus('error');
        return;
      }
      const pid = Number(profileId);
      if (!Number.isInteger(pid) || pid <= 0) {
        console.error("Invalid profileId for scan", profileId);
        setScanStatus('error');
        return;
      }
      setScanStatus('scanning');
      await apiPost(API_ROUTES.SCAN_TRIGGER, {
        search_profile_id: pid,
        platforms,
      });
    } catch (err) {
      console.error("Failed to trigger scan", err);
      setScanStatus('error');
    }
  }, []);

  return {
    events,
    isConnected,
    scanStatus,
    triggerScan,
    clearEvents: () => setEvents([])
  };
}
