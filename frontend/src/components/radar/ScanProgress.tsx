"use client";

import { ScanEvent } from '@/lib/types';
import { PLATFORM_CONFIG } from '@/lib/constants';

interface ScanProgressProps {
  platform: string;
  events: ScanEvent[];
  isScanning: boolean;
}

export default function ScanProgress({ platform, events, isScanning }: ScanProgressProps) {
  const config = PLATFORM_CONFIG[String(platform ?? '').toLowerCase()];
  if (!config) return null;

  const Icon = config.icon;

  // Deterministic stats derived from events only (no Math.random in render)
  const safeEvents = Array.isArray(events) ? events : [];
  const foundLeads = safeEvents.filter(e => e?.type === 'found').length;
  const totalProcessed = safeEvents.length;

  // Deterministic progress: 100 when done with events, indeterminate pulse while scanning
  const progress = isScanning ? (totalProcessed > 0 ? Math.min(95, totalProcessed * 20) : 10) : (totalProcessed > 0 ? 100 : 0);

  return (
    <div className="bg-gray-950 border border-gray-800 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Icon size={14} className={config.color} />
          <span className="text-sm font-medium text-gray-200">{config.name}</span>
        </div>
        <span className="text-xs text-gray-500">
          {foundLeads} leads / {totalProcessed} posts
        </span>
      </div>
      
      <div className="w-full h-1.5 bg-gray-900 rounded-full overflow-hidden">
        <div 
          className="h-full bg-accent-green transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
