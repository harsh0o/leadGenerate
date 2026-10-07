"use client";

import { useEffect, useState } from 'react';
import StatsGrid from '@/components/dashboard/StatsGrid';
import PlatformBadges from '@/components/dashboard/PlatformBadges';
import RecentLeads from '@/components/dashboard/RecentLeads';
import Button from '@/components/ui/Button';
import PersonaBanner from '@/components/layout/PersonaBanner';
import { apiGet, API_ROUTES } from '@/lib/api';
import { DashboardStats } from '@/lib/types';
import Link from 'next/link';
import { Zap, Plus } from 'lucide-react';
import Spinner from '@/components/ui/Spinner';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiGet<DashboardStats>(API_ROUTES.DASHBOARD_STATS);
        setStats(data);
        setLoadError(null);
      } catch (err: any) {
        console.error("Failed to load stats", err);
        setLoadError(err?.message || 'Failed to load dashboard');
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (isLoading) {
    return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;
  }

  if (loadError && !stats) {
    return (
      <div className="max-w-7xl mx-auto py-16 text-center">
        <p className="text-red-400 mb-2">Failed to load dashboard</p>
        <p className="text-sm text-gray-500 mb-6">{loadError}</p>
        <Button variant="primary" onClick={() => window.location.reload()}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PersonaBanner />
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">Overview of your lead generation pipeline</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="secondary" asChild>
            <Link href="/profiles/new">
              <Plus size={16} className="mr-2" /> New Profile
            </Link>
          </Button>
          <Button variant="primary" asChild>
            <Link href="/radar">
              <Zap size={16} className="mr-2" /> Live Scan
            </Link>
          </Button>
        </div>
      </div>

      <StatsGrid stats={stats} />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <RecentLeads leads={stats?.recent_leads || []} />
        </div>
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Platform Health</h3>
            <PlatformBadges />
          </div>
        </div>
      </div>
    </div>
  );
}
