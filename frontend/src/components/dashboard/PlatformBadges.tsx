"use client";

import { useEffect, useState } from 'react';
import { PlatformHealth } from '@/lib/types';
import { apiGet, API_ROUTES } from '@/lib/api';
import { PLATFORM_CONFIG } from '@/lib/constants';

export default function PlatformBadges() {
  const [healthData, setHealthData] = useState<PlatformHealth[]>([]);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await apiGet<unknown>(API_ROUTES.HEALTH_PLATFORMS);
        // Backend returns an array, but guard against wrapped/object responses
        // (e.g. /api/health returns { status: "ok", ... } which is not mappable).
        const list = Array.isArray(data)
          ? data
          : Array.isArray((data as { platforms?: unknown })?.platforms)
            ? (data as { platforms: unknown[] }).platforms
            : Array.isArray((data as { data?: unknown })?.data)
              ? (data as { data: unknown[] }).data
              : [];
        // Normalize: backend uses UPPER_SNAKE (HEALTHY) + last_check_at,
        // frontend type uses lowercase + last_check.
        const normalized = (list as Record<string, unknown>[]).map((item) => ({
          platform: String(item.platform ?? 'unknown'),
          status: String(item.status ?? 'unknown').toLowerCase(),
          last_check: String(item.last_check ?? item.last_check_at ?? ''),
        })) as PlatformHealth[];
        setHealthData(normalized);
      } catch (err) {
        console.error("Failed to fetch platform health", err);
      }
    };
    fetchHealth();
  }, []);

  const getStatusColor = (status: string) => {
    switch (String(status ?? '').toLowerCase()) {
      case 'healthy': return 'bg-emerald-500';
      case 'degraded': return 'bg-amber-500';
      case 'down': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const safeHealthData = Array.isArray(healthData) ? healthData : [];

  if (safeHealthData.length === 0) {
    return <div className="text-gray-500 text-sm">Loading health status...</div>;
  }

  return (
    <div className="flex flex-col space-y-4">
      {safeHealthData.map((platform) => {
        const key = String(platform?.platform ?? 'unknown').toLowerCase();
        const config = PLATFORM_CONFIG[key] || { name: platform?.platform ?? 'Unknown', icon: () => null };
        const Icon = config.icon;
        return (
          <div key={platform.platform} className="flex items-center justify-between p-3 rounded-lg bg-gray-800/50 border border-gray-800">
            <div className="flex items-center space-x-3">
              <Icon size={18} className="text-gray-400" />
              <span className="text-sm font-medium text-gray-200">{config.name}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-400 capitalize">{platform.status}</span>
              <div className={`w-2.5 h-2.5 rounded-full ${getStatusColor(platform.status)}`}></div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
