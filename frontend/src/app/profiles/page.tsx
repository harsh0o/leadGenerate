"use client";

import { useProfiles } from '@/hooks/useProfiles';
import ProfileCard from '@/components/profiles/ProfileCard';
import Button from '@/components/ui/Button';
import { Plus } from 'lucide-react';
import Link from 'next/link';
import Spinner from '@/components/ui/Spinner';

export default function ProfilesPage() {
  const { profiles, isLoading, deleteProfile, toggleProfile } = useProfiles();

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Search Profiles</h1>
          <p className="text-gray-400 mt-1">Configure your target audience and requirements</p>
        </div>
        <Button variant="primary" asChild>
          <Link href="/profiles/new">
            <Plus size={16} className="mr-2" /> Create Profile
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="py-20 flex justify-center"><Spinner size="lg" /></div>
      ) : profiles.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <p className="text-gray-400 mb-4">No search profiles found.</p>
          <Button variant="secondary" asChild>
            <Link href="/profiles/new">Create your first profile</Link>
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {profiles.map(profile => (
            <ProfileCard 
              key={profile.id} 
              profile={profile} 
              onDelete={() => deleteProfile(profile.id)}
              onToggle={() => toggleProfile(profile.id, profile.is_active)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
