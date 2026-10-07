"use client";

import { useMemo } from 'react';
import { DndContext, DragEndEvent, closestCorners } from '@dnd-kit/core';
import KanbanColumn from './KanbanColumn';
import { Lead } from '@/lib/types';
import { usePersonaContext } from '@/providers/PersonaProvider';

interface KanbanBoardProps {
  leads: Lead[];
  onStatusChange: (leadId: string | number, newStatus: string) => void;
}

export default function KanbanBoard({ leads, onStatusChange }: KanbanBoardProps) {
  const { config } = usePersonaContext();
  const columns: string[] = config?.kanban_columns || ['NEW', 'CONTACTED', 'INTERVIEWING', 'CLOSED_WON', 'CLOSED_LOST'];

  // Group leads by status (defensive: leads may be undefined during load)
  // Normalize case-insensitively so 'NEW' and 'New' land in the same column
  // regardless of which persona column set is active.
  const safeLeads = Array.isArray(leads) ? leads : [];
  const leadsByColumn = useMemo(() => {
    const grouped: Record<string, Lead[]> = {};
    columns.forEach((col: string) => grouped[col] = []);
    const normIndex: Record<string, string> = {};
    columns.forEach((col: string) => { normIndex[col.toUpperCase()] = col; });

    safeLeads.forEach(lead => {
      const rawStatus = String(lead?.kanban_status || columns[0] || 'NEW');
      const canonical = normIndex[rawStatus.toUpperCase()] || columns[0];
      grouped[canonical].push(lead);
    });
    return grouped;
  }, [safeLeads, columns]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const leadId = String(active.id);
    const overId = String(over.id);

    // over can be another card (cards are draggable) – only accept column ids
    if (!(columns as string[]).includes(overId)) {
      return;
    }

    const lead = leads.find(l => String(l.id) === leadId);
    if (lead && lead.kanban_status !== overId) {
      onStatusChange(leadId, overId);
    }
  };

  return (
    <DndContext collisionDetection={closestCorners} onDragEnd={handleDragEnd}>
      <div className="flex-1 flex gap-6 overflow-x-auto pb-4 h-full">
        {(columns as string[]).map((column: string) => (
          <KanbanColumn
            key={column}
            id={column}
            title={column}
            leads={leadsByColumn[column] ?? []}
          />
        ))}
      </div>
    </DndContext>
  );
}
