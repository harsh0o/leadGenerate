"use client";

import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { Lead } from '@/lib/types';
import { PLATFORM_CONFIG } from '@/lib/constants';
import { GripVertical } from 'lucide-react';
import Link from 'next/link';

export default function LeadCard({ lead }: { lead: Lead }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: lead.id,
    data: lead
  });

  const style = {
    transform: CSS.Translate.toString(transform),
  };

  const platKey = String(lead?.platform ?? 'unknown').toLowerCase();
  const platform = PLATFORM_CONFIG[platKey];
  const PlatformIcon = platform?.icon;
  const scoreRaw = Number(lead?.confidence_score ?? 0);
  const score = Number.isFinite(scoreRaw) ? Math.max(0, Math.min(100, scoreRaw <= 1 && scoreRaw > 0 ? scoreRaw * 100 : scoreRaw)) : 0;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-sm group relative ${
        isDragging ? 'opacity-50 scale-105 z-50 shadow-xl border-accent-green/50' : 'hover:border-gray-500'
      } transition-colors cursor-default`}
    >
      <div 
        {...attributes} 
        {...listeners}
        className="absolute top-2 right-2 p-1 text-gray-500 hover:text-gray-300 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <GripVertical size={14} />
      </div>

      <div className="mb-2">
        <Link href={`/leads/${lead?.id}`} className="block hover:underline">
          <h4 className="font-medium text-white text-sm line-clamp-2 pr-6 leading-tight">{lead?.title || 'Untitled'}</h4>
        </Link>
        {lead?.company && <p className="text-xs text-gray-400 mt-1 truncate">{lead.company}</p>}
      </div>

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center space-x-1 text-xs text-gray-400">
          {PlatformIcon && <PlatformIcon size={12} className={platform.color} />}
          <span>{platform?.name || lead?.platform || 'Unknown'}</span>
        </div>

        <div className="flex items-center">
          <div className="w-12 h-1.5 bg-gray-900 rounded-full overflow-hidden mr-2">
            <div
              className="h-full bg-emerald-400"
              style={{ width: `${score}%` }}
            />
          </div>
          <span className="text-[10px] text-gray-500">{Math.round(score)}%</span>
        </div>
      </div>
    </div>
  );
}
