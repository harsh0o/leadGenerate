"use client";

import CriteriaBuilder from '@/components/profiles/CriteriaBuilder';
import { ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function NewProfilePage() {
  const router = useRouter();

  return (
    <div className="max-w-3xl mx-auto py-8">
      <button 
        onClick={() => router.back()} 
        className="flex items-center text-sm text-gray-400 hover:text-white transition-colors mb-6"
      >
        <ArrowLeft size={16} className="mr-2" /> Back to Profiles
      </button>

      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Create Search Profile</h1>
        <p className="text-gray-400 mt-1">Define your ideal target parameters</p>
      </div>

      <CriteriaBuilder />
    </div>
  );
}
