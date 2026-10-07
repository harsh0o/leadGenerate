"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Lead } from '@/lib/types';
import { apiGet, apiPatch, API_ROUTES } from '@/lib/api';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import DraftPanel from '@/components/drafts/DraftPanel';
import { ArrowLeft, ExternalLink, Calendar, User, Building } from 'lucide-react';
import Spinner from '@/components/ui/Spinner';
import { PLATFORM_CONFIG } from '@/lib/constants';

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [lead, setLead] = useState<Lead | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    const rawId = Array.isArray(params.id) ? params.id[0] : params.id;
    if (!rawId) return;
    const fetchLead = async () => {
      try {
        const data = await apiGet<Lead>(`${API_ROUTES.LEADS}/${rawId}`);
        setLead(data);
        setNotes(data.notes || '');
      } catch (err) {
        console.error("Failed to fetch lead", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchLead();
  }, [params.id]);

  const [isSaving, setIsSaving] = useState(false);
  const saveNotes = async () => {
    if (!lead) return;
    setIsSaving(true);
    try {
      const updated = await apiPatch<Lead>(`${API_ROUTES.LEADS}/${lead.id}/notes`, { notes });
      setLead(updated);
      setNotes(updated.notes || '');
    } catch (err) {
      console.error("Failed to save notes", err);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;
  if (!lead) return <div className="text-center py-12 text-gray-400">Lead not found</div>;

  const platform = PLATFORM_CONFIG[String(lead?.platform ?? 'unknown').toLowerCase()];
  const PlatformIcon = platform?.icon;
  const tags = Array.isArray(lead?.tags) ? lead.tags : [];
  const created = lead?.created_at ? new Date(lead.created_at) : null;
  const createdStr = created && !isNaN(created.getTime()) ? created.toLocaleDateString() : '—';
  const confRaw = Number(lead?.confidence_score ?? 0);
  const confNorm = Number.isFinite(confRaw) ? (confRaw > 0 && confRaw <= 1 ? confRaw * 100 : confRaw) : 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <button onClick={() => router.back()} className="flex items-center text-sm text-gray-400 hover:text-white transition-colors">
        <ArrowLeft size={16} className="mr-2" /> Back to Pipeline
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-2xl font-bold text-white mb-2">{lead?.title || 'Untitled'}</h1>
                <div className="flex flex-wrap gap-3 text-sm text-gray-400">
                  {lead?.company && <span className="flex items-center"><Building size={14} className="mr-1" /> {lead.company}</span>}
                  <span className="flex items-center"><User size={14} className="mr-1" /> {lead?.author || 'Unknown'}</span>
                  <span className="flex items-center"><Calendar size={14} className="mr-1" /> {createdStr}</span>
                </div>
              </div>
              <Badge variant="outline" className="flex items-center gap-1 px-3 py-1">
                {PlatformIcon && <PlatformIcon size={14} className={platform.color} />}
                {platform?.name || lead?.platform || 'Unknown'}
              </Badge>
            </div>

            <div className="prose prose-invert max-w-none mt-6">
              <div className="text-gray-300 whitespace-pre-wrap text-sm leading-relaxed bg-gray-950 p-4 rounded-lg border border-gray-800">
                {lead?.content || 'No content'}
              </div>
            </div>

            <div className="mt-6 flex gap-2 flex-wrap">
              {tags.map(tag => (
                <Badge key={String(tag)} variant="default">{String(tag)}</Badge>
              ))}
            </div>

            <div className="mt-6 pt-6 border-t border-gray-800 flex justify-between items-center">
              <span className="text-sm text-gray-400">Confidence Score: <span className="text-emerald-400 font-medium">{Math.round(confNorm)}%</span></span>
              {lead.url ? (
                <Button variant="secondary" size="sm" asChild>
                  <a href={lead.url} target="_blank" rel="noopener noreferrer" className="flex items-center">
                    View Original <ExternalLink size={14} className="ml-2" />
                  </a>
                </Button>
              ) : (
                <span className="text-sm text-gray-500">No link available</span>
              )}
            </div>
          </div>

          <DraftPanel leadId={lead.id} />
        </div>

        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Lead Status</h3>
            <div className="space-y-3">
              <Badge variant="info" className="w-full justify-center py-2 text-sm">{lead.kanban_status}</Badge>
              <div className="text-xs text-center text-gray-500">Update status from the Kanban board</div>
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Notes</h3>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              onBlur={saveNotes}
              className="w-full h-32 bg-gray-950 border border-gray-800 rounded-lg p-3 text-sm text-gray-300 focus:outline-none focus:border-accent-green resize-none"
              placeholder="Add personal notes here..."
            />
            <div className="flex items-center justify-between mt-3">
              <div className="text-xs text-gray-500">{isSaving ? 'Saving...' : 'Auto-saves on blur'}</div>
              <Button variant="secondary" size="sm" onClick={saveNotes} disabled={isSaving}>
                {isSaving ? 'Saving...' : 'Save Notes'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
