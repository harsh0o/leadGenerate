"use client";

import { SearchProfile } from '@/lib/types';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { Trash2, Edit2, Play, Power } from 'lucide-react';
import Link from 'next/link';
import Button from '@/components/ui/Button';

interface ProfileCardProps {
  profile: SearchProfile;
  onDelete: () => void;
  onToggle: () => void;
}

export default function ProfileCard({ profile, onDelete, onToggle }: ProfileCardProps) {
  return (
    <Card className={`relative transition-opacity ${!profile.is_active ? 'opacity-60' : ''}`}>
      <div className="absolute top-4 right-4 flex items-center space-x-2">
        <button 
          onClick={onToggle}
          className={`p-1.5 rounded-md transition-colors ${profile.is_active ? 'text-accent-green bg-emerald-500/10' : 'text-gray-500 bg-gray-800'}`}
          title={profile.is_active ? "Deactivate" : "Activate"}
        >
          <Power size={14} />
        </button>
      </div>

      <h3 className="text-lg font-semibold text-white mb-1 pr-10 truncate">{profile?.name || 'Untitled'}</h3>
      <p className="text-xs text-gray-500 mb-4">
        Last scan: {(() => { const d = profile?.last_scan_at ? new Date(profile.last_scan_at) : null; return d && !isNaN(d.getTime()) ? d.toLocaleDateString() : 'Never'; })()}
      </p>

      <div className="space-y-4 mb-6">
        <div>
          <div className="text-xs font-medium text-gray-400 mb-2">Target Tags</div>
          <div className="flex flex-wrap gap-1.5">
            {(Array.isArray(profile?.tags) ? profile.tags : []).slice(0, 5).map((tag, i) => (
              <Badge key={tag?.name || `tag-${i}`} variant="outline" className="text-[10px]">{tag?.name}</Badge>
            ))}
            {(profile?.tags?.length || 0) > 5 && (
              <Badge variant="default" className="text-[10px]">+{(profile.tags.length - 5)} more</Badge>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Budget</span>
          <span className="text-white font-medium">
            {profile?.budget_min != null && profile?.budget_max != null ? `$${profile.budget_min} - $${profile.budget_max}` : 'Not specified'}
          </span>
        </div>
        
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Location</span>
          <span className="text-white font-medium">
            {profile.remote_only ? 'Remote Only' : profile.location || 'Anywhere'}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-gray-800">
        <div className="flex space-x-2">
          <Link href={`/profiles/${profile.id}`} className="p-2 text-gray-400 hover:text-white transition-colors" title="Edit profile">
            <Edit2 size={16} />
          </Link>
          <button
            onClick={() => { if (window.confirm(`Delete profile "${profile?.name || 'Untitled'}"?`)) onDelete(); }}
            className="p-2 text-gray-400 hover:text-red-500 transition-colors"
            title="Delete profile"
          >
            <Trash2 size={16} />
          </button>
        </div>
        <Button variant="primary" size="sm" asChild>
          <Link href={`/radar?profile=${profile.id}`}>
            <Play size={14} className="mr-1.5" /> Scan Now
          </Link>
        </Button>
      </div>
    </Card>
  );
}
