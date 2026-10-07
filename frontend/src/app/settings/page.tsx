"use client";

import { useState } from 'react';
import { usePersonaContext } from '@/providers/PersonaProvider';
import { PERSONA_CONFIG } from '@/lib/constants';
import { PersonaType } from '@/lib/types';
import Button from '@/components/ui/Button';
import { apiPut } from '@/lib/api';

export default function SettingsPage() {
  const { persona, setPersona } = usePersonaContext();
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-400 mt-1">Configure LeadHunter AI preferences</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Workflow Persona</h3>
        <p className="text-sm text-gray-400 mb-6">
          Changing your persona updates your default Kanban columns, tags, and AI prompt contexts.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(PERSONA_CONFIG).map(([key, config]) => {
            const Icon = config.icon;
            const isSelected = persona === key;
            return (
              <button
                key={key}
                onClick={() => setPersona(key as PersonaType)}
                className={`p-4 rounded-xl border text-left transition-all ${
                  isSelected ? 'border-accent-green bg-emerald-500/10' : 'border-gray-800 hover:border-gray-600'
                }`}
              >
                <Icon size={24} className={`${config.color.replace('bg-', 'text-')} mb-3`} />
                <h4 className="font-semibold text-white mb-1">{config.label}</h4>
                <p className="text-xs text-gray-500">
                  Columns: {config.kanban_columns.join(', ')}
                </p>
              </button>
            )
          })}
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">API Configurations</h3>

        <div className="space-y-4 max-w-2xl">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">OpenRouter API Key (AI Engine)</label>
            <input
              type="password"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder="sk-or-v1-... (stored server-side, never committed)"
              className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:outline-none focus:border-accent-green font-mono"
            />
            <p className="text-xs text-gray-500 mt-1">Leave blank to keep existing key. Never commit keys to git.</p>
          </div>
          
          <div className="pt-4 border-t border-gray-800">
            <h4 className="text-sm font-medium text-white mb-3">Platform Connections</h4>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-950 rounded-lg border border-gray-800">
                <span className="text-sm font-medium text-gray-300">Reddit API (PRAW)</span>
                <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">Connected</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-950 rounded-lg border border-gray-800">
                <span className="text-sm font-medium text-gray-300">LinkedIn (Cookie Auth)</span>
                <button className="text-xs text-accent-green hover:underline">Configure</button>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-950 rounded-lg border border-gray-800">
                <span className="text-sm font-medium text-gray-300">Hacker News API</span>
                <span className="text-xs text-gray-500">No auth required</span>
              </div>
            </div>
          </div>
        </div>

        {msg && <div className="text-sm text-gray-300 bg-gray-950 border border-gray-800 rounded-lg p-3">{msg}</div>}
        <div className="mt-6">
          <Button
            variant="primary"
            isLoading={saving}
            onClick={async () => {
              setSaving(true);
              setMsg(null);
              try {
                if (apiKey.trim()) {
                  await apiPut('/api/settings/platforms', { openrouter_api_key: apiKey.trim() });
                  setApiKey('');
                }
                setMsg('Configuration saved.');
              } catch (e: any) {
                setMsg(e?.message || 'Save failed');
              } finally {
                setSaving(false);
              }
            }}
          >
            Save Configuration
          </Button>
        </div>
      </div>

      <div className="text-center py-8 border-t border-gray-800">
        <p className="text-sm text-gray-500">
          LeadHunter AI • Built by <a href="https://github.com/harsh0o" target="_blank" rel="noopener noreferrer" className="text-accent-green hover:underline">harsh0o</a>
        </p>
      </div>
    </div>
  );
}
