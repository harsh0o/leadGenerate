"use client";

import { useDroppable } from '@dnd-kit/core';
import { Lead } from '@/lib/types';
import LeadCard from './LeadCard';

interface KanbanColumnProps {
  id: string;
  title: string;
  leads: Lead[];
}

export default function KanbanColumn({ id, title, leads }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id });
  const safeLeads = Array.isArray(leads) ? leads : [];

  return (
    <div className="flex flex-col w-80 shrink-0 h-full">
      <div className="flex items-center justify-between mb-4 px-1">
        <h3 className="font-semibold text-gray-200">{title}</h3>
        <span className="text-xs font-medium text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
          {safeLeads.length}
        </span>
      </div>

      <div
        ref={setNodeRef}
        className={`flex-1 bg-gray-900/50 rounded-xl p-3 border-2 transition-colors overflow-y-auto ${
          isOver ? 'border-accent-green/50 bg-gray-900/80' : 'border-transparent'
        }`}
      >
        <div className="flex flex-col gap-3 min-h-[100px]">
          {safeLeads.map((lead, i) => (
            <LeadCard key={lead?.id ?? lead?.url ?? `fallback-${i}`} lead={lead} />
          ))}
        </div>
      </div>
    </div>
  );
}
