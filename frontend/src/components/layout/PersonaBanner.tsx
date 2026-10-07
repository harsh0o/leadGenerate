"use client";

import { usePersonaContext } from '@/providers/PersonaProvider';

export default function PersonaBanner() {
  const { config } = usePersonaContext();

  if (!config) return null;
  const Icon = config.icon;

  return (
    <div className={`px-4 py-2 flex items-center justify-center space-x-2 text-sm font-medium ${config.color.replace('bg-', 'text-')} bg-opacity-10 rounded-lg mb-6 border border-gray-800`}>
      <Icon size={16} />
      <span>Active Workspace: {config.label}</span>
    </div>
  );
}
