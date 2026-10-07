"use client";

import { motion } from 'framer-motion';
import { Users, UserPlus, Activity, Target } from 'lucide-react';
import Card from '@/components/ui/Card';
import { DashboardStats } from '@/lib/types';

export default function StatsGrid({ stats }: { stats: DashboardStats | null }) {
  // Derive directly from props (no props-to-state copy, no stale numbers).
  const total_leads = Number(stats?.total_leads ?? 0) || 0;
  const leads_today = Number(stats?.leads_today ?? 0) || 0;
  const active_scans = Number(stats?.active_scans ?? 0) || 0;
  const match_accuracy = Number(stats?.match_accuracy ?? 0) || 0;

  const items = [
    { label: 'Total Leads', value: total_leads, icon: Users, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { label: 'Leads Today', value: leads_today, icon: UserPlus, color: 'text-green-500', bg: 'bg-green-500/10' },
    { label: 'Active Scans', value: active_scans, icon: Activity, color: 'text-purple-500', bg: 'bg-purple-500/10' },
    { label: 'Match Accuracy', value: `${match_accuracy}%`, icon: Target, color: 'text-orange-500', bg: 'bg-orange-500/10' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {items.map((item, i) => (
        <motion.div
          key={item.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
        >
          <Card className="p-0" hoverEffect>
            <div className="flex items-center p-6">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mr-4 ${item.bg}`}>
                <item.icon className={item.color} size={24} />
              </div>
              <div>
                <p className="text-gray-400 text-sm font-medium">{item.label}</p>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {item.value}
                </h3>
              </div>
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
