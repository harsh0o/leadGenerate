"use client";

import { clsx } from 'clsx';

interface ToneSelectorProps {
  value: string;
  onChange: (val: string) => void;
}

export default function ToneSelector({ value, onChange }: ToneSelectorProps) {
  const tones = ['PROFESSIONAL', 'FRIENDLY', 'CASUAL', 'FORMAL', 'PERSUASIVE', 'CONCISE'];

  return (
    <div className="flex flex-wrap bg-gray-950 border border-gray-800 rounded-lg p-1 gap-1">
      {tones.map((tone) => (
        <button
          key={tone}
          type="button"
          onClick={() => onChange(tone)}
          className={clsx(
            "flex-1 text-xs font-medium py-1.5 rounded-md transition-colors",
            value === tone 
              ? "bg-gray-800 text-white shadow-sm" 
              : "text-gray-400 hover:text-gray-200"
          )}
        >
          {tone}
        </button>
      ))}
    </div>
  );
}
