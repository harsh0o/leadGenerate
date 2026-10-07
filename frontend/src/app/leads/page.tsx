"use client";

import { useLeads } from '@/hooks/useLeads';
import KanbanBoard from '@/components/kanban/KanbanBoard';
import Spinner from '@/components/ui/Spinner';
import { Search } from 'lucide-react';
import { useState } from 'react';

export default function LeadsPage() {
  const [search, setSearch] = useState('');
  const { leads, isLoading, updateLeadStatus } = useLeads({ search });

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white">Leads Pipeline</h1>
          <p className="text-sm text-gray-400 mt-1">Manage your opportunities</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
            <input 
              type="text" 
              placeholder="Search leads..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-white focus:outline-none focus:border-accent-green w-64"
            />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : (
        <KanbanBoard leads={leads} onStatusChange={updateLeadStatus} />
      )}
    </div>
  );
}
