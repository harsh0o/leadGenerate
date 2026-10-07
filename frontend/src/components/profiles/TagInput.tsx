"use client";

import { useState } from 'react';
import { X } from 'lucide-react';
import Badge from '@/components/ui/Badge';

interface Tag {
  name: string;
  type: string;
}

interface TagInputProps {
  tags: Tag[];
  onChange: (tags: Tag[]) => void;
}

export default function TagInput({ tags, onChange }: TagInputProps) {
  const [input, setInput] = useState('');
  const [type, setType] = useState('skill');

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag();
    }
  };

  const safeTags = Array.isArray(tags) ? tags : [];
  const addTag = () => {
    const val = input.trim();
    if (val && !safeTags.find(t => t.name.toLowerCase() === val.toLowerCase())) {
      onChange([...safeTags, { name: val, type }]);
      setInput('');
    }
  };

  const removeTag = (name: string) => {
    onChange((Array.isArray(tags) ? tags : []).filter(t => t.name.toLowerCase() !== String(name).toLowerCase()));
  };

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <select 
          value={type}
          onChange={e => setType(e.target.value)}
          className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-green"
        >
          <option value="skill">Skill</option>
          <option value="role">Role</option>
          <option value="industry">Industry</option>
          <option value="keyword">Keyword</option>
        </select>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type and press Enter..."
          className="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-accent-green"
        />
        <button 
          onClick={addTag}
          className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
        >
          Add
        </button>
      </div>

      <div className="flex flex-wrap gap-2 p-4 bg-gray-950 border border-gray-800 rounded-lg min-h-[100px]">
        {safeTags.length === 0 && <span className="text-gray-500 text-sm">No tags added yet.</span>}
        {safeTags.map(tag => (
          <Badge key={tag.name} variant="success" className="pr-1 pl-3 py-1 text-sm flex items-center gap-2">
            <span>{tag.name}</span>
            <span className="text-[10px] opacity-70 uppercase tracking-wider">{tag.type}</span>
            <button 
              onClick={() => removeTag(tag.name)}
              className="hover:bg-emerald-500/20 rounded-full p-0.5 transition-colors"
            >
              <X size={14} />
            </button>
          </Badge>
        ))}
      </div>
    </div>
  );
}
