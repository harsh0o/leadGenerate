"use client";

import { Lead } from '@/lib/types';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { PLATFORM_CONFIG } from '@/lib/constants';
import Link from 'next/link';

export default function RecentLeads({ leads }: { leads: Lead[] }) {
  if (!leads || leads.length === 0) {
    return (
      <Card>
        <div className="text-center py-8 text-gray-500">
          No recent leads found. Run a scan to find leads.
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-0">
      <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center">
        <h3 className="text-lg font-semibold text-white">Recent Leads</h3>
        <Link href="/leads" className="text-sm text-accent-green hover:underline">
          View all
        </Link>
      </div>
      <div className="divide-y divide-gray-800">
        {(Array.isArray(leads) ? leads : []).slice(0, 5).map((lead) => {
          const platform = PLATFORM_CONFIG[String(lead?.platform ?? 'unknown').toLowerCase()];
          const PlatformIcon = platform?.icon;
          const sRaw = Number(lead?.confidence_score ?? 0);
          const sNorm = Number.isFinite(sRaw) ? (sRaw > 0 && sRaw <= 1 ? sRaw * 100 : sRaw) : 0;
          const d = lead?.created_at ? new Date(lead.created_at) : null;
          const dateStr = d && !isNaN(d.getTime()) ? d.toLocaleDateString() : '—';

          return (
            <Link key={lead?.id} href={`/leads/${lead?.id}`} className="block hover:bg-gray-800/50 transition-colors p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0 pr-4">
                  <h4 className="text-base font-medium text-white truncate">{lead?.title || 'Untitled'}</h4>
                  {lead?.company && <p className="text-sm text-gray-400 mt-1">{lead.company}</p>}
                  <div className="flex items-center space-x-3 mt-3">
                    <Badge variant="outline" className="flex items-center gap-1">
                      {PlatformIcon && <PlatformIcon size={12} className={platform.color} />}
                      {platform?.name || lead?.platform || 'Unknown'}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      Score: <span className="text-emerald-400 font-medium">{Math.round(sNorm)}%</span>
                    </span>
                  </div>
                </div>
                <div className="text-xs text-gray-500 whitespace-nowrap">
                  {dateStr}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </Card>
  );
}
