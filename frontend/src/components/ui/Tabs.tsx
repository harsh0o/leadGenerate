"use client";

import { motion } from 'framer-motion';

interface Tab {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  activeId: string;
  onChange: (id: string) => void;
}

export default function Tabs({ tabs, activeId, onChange }: TabsProps) {
  return (
    <div className="flex space-x-1 bg-gray-900/50 p-1 rounded-lg border border-gray-800 overflow-x-auto">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`relative px-4 py-2 text-sm font-medium rounded-md transition-colors whitespace-nowrap ${
            activeId === tab.id ? 'text-gray-950' : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
        >
          {activeId === tab.id && (
            <motion.div
              layoutId="activeTab"
              className="absolute inset-0 bg-accent-green rounded-md"
              initial={false}
              transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
            />
          )}
          <span className="relative z-10">{tab.label}</span>
        </button>
      ))}
    </div>
  );
}
