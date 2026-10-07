"use client";

import { useSearchParams } from 'next/navigation';
import { Suspense, useMemo } from 'react';
import Link from 'next/link';
import { useScan } from '@/hooks/useScan';
import RadarDisplay from '@/components/radar/RadarDisplay';
import ScanProgress from '@/components/radar/ScanProgress';
import LiveFeed from '@/components/radar/LiveFeed';
import Button from '@/components/ui/Button';
import { Play, Square } from 'lucide-react';

function RadarContent() {
  const searchParams = useSearchParams();
  const profileId = searchParams.get('profile');
  
  const { events, isConnected, scanStatus, triggerScan, clearEvents } = useScan();
  // Canonical platforms only (dedupe hn->hackernews, x->twitter aliases)
  const activePlatforms = useMemo(() => ["reddit", "hackernews", "linkedin", "twitter", "threads"], []);

  const handleStartScan = () => {
    clearEvents();
    triggerScan(profileId || undefined, activePlatforms);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center">
            Live Radar 
            <span className="ml-3 flex h-3 w-3 relative">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isConnected ? 'bg-emerald-400' : 'bg-red-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
            </span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">Real-time opportunity scanning</p>
          {!profileId && (
            <p className="text-sm text-amber-400 mt-2">
              No profile selected — <Link href="/profiles" className="underline hover:text-amber-300">choose a profile</Link> or start a scan with all platforms below.
            </p>
          )}
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-400 hidden sm:block">
            Status: <span className={scanStatus === 'scanning' ? 'text-accent-green' : 'text-gray-300'}>{scanStatus === 'scanning' ? 'Scanning...' : 'Idle'}</span>
          </div>
          {scanStatus === 'scanning' ? (
            <Button variant="danger" className="w-32" onClick={clearEvents}>
              <Square size={16} className="mr-2" /> Clear
            </Button>
          ) : (
            <Button variant="primary" onClick={handleStartScan} className="w-32" disabled={!profileId}>
              <Play size={16} className="mr-2" /> Start Scan
            </Button>
          )}
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-6 flex flex-col items-center justify-center relative overflow-hidden">
          <RadarDisplay isScanning={scanStatus === 'scanning'} events={events} />
        </div>
        
        <div className="flex flex-col gap-6 min-h-0">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 shrink-0">
            <h3 className="text-sm font-semibold text-white mb-3">Platform Progress</h3>
            <div className="space-y-3 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
              {activePlatforms.map(platform => (
                <ScanProgress 
                  key={platform} 
                  platform={platform} 
                  events={events.filter(e => e.platform === platform)} 
                  isScanning={scanStatus === 'scanning'} 
                />
              ))}
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex-1 flex flex-col min-h-0">
            <h3 className="text-sm font-semibold text-white mb-3">Live Feed</h3>
            <div className="flex-1 min-h-0">
              <LiveFeed events={events} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function RadarPage() {
  return (
    <Suspense fallback={<div className="text-gray-400">Loading radar...</div>}>
      <RadarContent />
    </Suspense>
  );
}
