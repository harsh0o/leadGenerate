"use client";

import { useEffect, useRef } from 'react';
import { ScanEvent } from '@/lib/types';
import { PLATFORM_CONFIG } from '@/lib/constants';

export default function LiveFeed({ events }: { events: ScanEvent[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    // Only autoscroll when already near the bottom so users can inspect history.
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    if (nearBottom) {
      el.scrollTop = el.scrollHeight;
    }
  }, [events]);

  return (
    <div 
      ref={scrollRef}
      className="h-full overflow-y-auto space-y-2 pr-2 custom-scrollbar font-mono text-xs"
    >
      {!Array.isArray(events) || events.length === 0 ? (
        <div className="text-gray-600 text-center py-4">Waiting for scan events...</div>
      ) : (
        events.map((event, i) => {
          const config = PLATFORM_CONFIG[String(event?.platform ?? 'unknown').toLowerCase()];
          const dt = event?.timestamp ? new Date(event.timestamp) : null;
          const time = dt && !isNaN(dt.getTime()) ? dt.toLocaleTimeString([], { hour12: false }) : '--:--:--';
          
          let colorClass = "text-gray-400";
          if (event.type === 'found') colorClass = "text-accent-green";
          if (event.type === 'error') colorClass = "text-red-400";

          return (
            <div key={event?.id || i} className="flex space-x-3 py-1 border-b border-gray-800/50">
              <span className="text-gray-600 shrink-0">[{time}]</span>
              <span className={`shrink-0 w-20 truncate ${config?.color || 'text-gray-500'}`}>
                {config?.name || event?.platform || 'system'}
              </span>
              <span className={`${colorClass} whitespace-pre-wrap break-words`}>
                {event?.message || ''}
              </span>
            </div>
          );
        })
      )}
    </div>
  );
}
