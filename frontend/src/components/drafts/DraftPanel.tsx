"use client";

import { useState, useEffect } from 'react';
import { useDrafts } from '@/hooks/useDrafts';
import Button from '@/components/ui/Button';
import ToneSelector from './ToneSelector';
import { Bot, Copy, CheckCircle2, History } from 'lucide-react';

const TYPE_OPTIONS = [
  { label: 'Cold DM', value: 'COLD_DM' },
  { label: 'Cold Email', value: 'COLD_EMAIL' },
  { label: 'Cover Letter', value: 'COVER_LETTER' },
  { label: 'Follow Up', value: 'FOLLOW_UP' },
  { label: 'Proposal', value: 'PROPOSAL' },
];
const TONE_OPTIONS = ['PROFESSIONAL', 'FRIENDLY', 'CASUAL', 'FORMAL', 'PERSUASIVE', 'CONCISE'];

export default function DraftPanel({ leadId }: { leadId: string | number }) {
  const { drafts, isLoading, fetchDrafts, generateDraft } = useDrafts();
  const [type, setType] = useState('COLD_DM');
  const [tone, setTone] = useState('PROFESSIONAL');
  const [instructions, setInstructions] = useState('');
  const [copied, setCopied] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    fetchDrafts(leadId);
  }, [leadId, fetchDrafts]);

  const handleGenerate = async () => {
    await generateDraft({
      lead_id: leadId,
      type,
      tone,
      instructions
    });
    setShowHistory(false);
  };

  const currentDraft = [...(Array.isArray(drafts) ? drafts : [])].sort((a, b) => {
    const ta = a?.created_at ? new Date(a.created_at).getTime() : 0;
    const tb = b?.created_at ? new Date(b.created_at).getTime() : 0;
    return (isNaN(tb) ? 0 : tb) - (isNaN(ta) ? 0 : ta);
  })[0];

  const handleCopy = async () => {
    if (!currentDraft) return;
    try {
      await navigator.clipboard.writeText(currentDraft.content);
    } catch {
      // Fallback for http:// or non-secure contexts where clipboard API fails
      try {
        const ta = document.createElement('textarea');
        ta.value = currentDraft.content;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      } catch { /* ignore */ }
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6 border-b border-gray-800 pb-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <Bot size={20} className="mr-2 text-accent-green" /> AI Draft Generator
        </h3>
        <button 
          onClick={() => setShowHistory(!showHistory)}
          className="text-sm text-gray-400 hover:text-white flex items-center transition-colors"
        >
          <History size={16} className="mr-1" /> History ({drafts.length})
        </button>
      </div>

      <div className="space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Message Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-accent-green"
            >
              {TYPE_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Tone</label>
            <ToneSelector value={tone} onChange={setTone} />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Custom Instructions (Optional)</label>
          <input 
            type="text" 
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="E.g., Mention our new product launch..."
            className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-accent-green"
          />
        </div>

        <Button 
          variant="primary" 
          className="w-full" 
          onClick={handleGenerate} 
          isLoading={isLoading}
        >
          Generate Draft
        </Button>

        {currentDraft && !showHistory && (
          <div className="mt-6 pt-6 border-t border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">Generated Draft</span>
              <button 
                onClick={handleCopy}
                className="text-gray-400 hover:text-white transition-colors"
              >
                {copied ? <CheckCircle2 size={16} className="text-emerald-400" /> : <Copy size={16} />}
              </button>
            </div>
            <textarea
              className="w-full h-48 bg-gray-950 border border-gray-800 rounded-lg p-4 text-sm text-gray-300 focus:outline-none focus:border-accent-green resize-none leading-relaxed"
              value={currentDraft.content}
              readOnly
            />
          </div>
        )}

        {showHistory && drafts.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-800 space-y-4">
            <h4 className="text-sm font-medium text-gray-400">Previous Drafts</h4>
            {(Array.isArray(drafts) ? drafts : []).map(draft => {
              const d = draft?.created_at ? new Date(draft.created_at) : null;
              const ds = d && !isNaN(d.getTime()) ? d.toLocaleDateString() : '—';
              return (
              <div key={draft?.id} className="bg-gray-950 border border-gray-800 rounded-lg p-4 text-sm text-gray-300">
                <div className="flex justify-between items-center mb-2 text-xs text-gray-500">
                  <span>{draft?.type || draft?.draft_type} • {draft?.tone}</span>
                  <span>{ds}</span>
                </div>
                <p className="line-clamp-3 whitespace-pre-wrap">{draft?.content}</p>
              </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
