"use client";

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import Button from '@/components/ui/Button';
import TagInput from './TagInput';
import { useProfiles } from '@/hooks/useProfiles';
import { PLATFORM_CONFIG } from '@/lib/constants';

const STEPS = ['Basic Info', 'Tags', 'Details', 'Platforms'];

export default function CriteriaBuilder() {
  const router = useRouter();
  const { createProfile } = useProfiles();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);

  // Form State
  const [name, setName] = useState('');
  const [tags, setTags] = useState<{name: string, type: string}[]>([]);
  const [budgetMin, setBudgetMin] = useState<number>(0);
  const [budgetMax, setBudgetMax] = useState<number>(150);
  const [location, setLocation] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [platforms, setPlatforms] = useState<string[]>(["reddit", "hackernews", "linkedin", "twitter", "threads"]);
  const [formError, setFormError] = useState<string | null>(null);

  const CANONICAL_PLATFORMS = ["reddit", "hackernews", "linkedin", "twitter", "threads"];

  const handleNext = () => {
    setFormError(null);
    if (step === 0 && !name.trim()) {
      setFormError('Profile name is required');
      return;
    }
    if (step === 1 && tags.length === 0) {
      setFormError('Add at least one tag');
      return;
    }
    if (step === 2 && budgetMin > budgetMax) {
      setFormError('Min budget cannot exceed max budget');
      return;
    }
    if (step < STEPS.length - 1) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 0) setStep(step - 1);
  };

  const handleSave = async () => {
    setFormError(null);
    if (!name.trim()) {
      setFormError('Profile name is required');
      return;
    }
    if (tags.length === 0) {
      setFormError('Add at least one tag');
      setStep(1);
      return;
    }
    if (platforms.length === 0) {
      setFormError('Select at least one platform');
      setStep(3);
      return;
    }
    if (budgetMin > budgetMax) {
      setFormError('Min budget cannot exceed max budget');
      setStep(2);
      return;
    }
    setLoading(true);
    try {
      await createProfile({
        name: name.trim(),
        tags,
        budget_min: budgetMin,
        budget_max: budgetMax,
        location,
        remote_only: remoteOnly,
        platforms: platforms.map(p => p.toLowerCase()),
      });
      router.push('/profiles');
    } catch (err: any) {
      console.error(err);
      setFormError(err?.message || 'Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  const togglePlatform = (p: string) => {
    setPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]);
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-8">
      {/* Progress */}
      <div className="flex items-center justify-between mb-8 relative">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-gray-800 -z-10"></div>
        {STEPS.map((s, i) => (
          <div key={s} className="flex flex-col items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
              i <= step ? 'bg-accent-green text-gray-950' : 'bg-gray-800 text-gray-400'
            }`}>
              {i + 1}
            </div>
            <span className={`text-xs mt-2 ${i <= step ? 'text-white' : 'text-gray-500'}`}>{s}</span>
          </div>
        ))}
      </div>

      {/* Content */}
      <div className="min-h-[300px] py-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {step === 0 && (
              <div className="space-y-4 max-w-md mx-auto">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Profile Name</label>
                  <input 
                    type="text" 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., React Developers in NY"
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:outline-none focus:border-accent-green"
                  />
                </div>
              </div>
            )}

            {step === 1 && (
              <div className="space-y-4">
                <label className="block text-sm font-medium text-gray-400 mb-2">Target Tags</label>
                <p className="text-xs text-gray-500 mb-4">Add skills, roles, or keywords to look for.</p>
                <TagInput tags={tags} onChange={setTags} />
              </div>
            )}

            {step === 2 && (
              <div className="space-y-6 max-w-md mx-auto">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Budget Range (k$)</label>
                  <div className="flex items-center space-x-4">
                    <input type="number" value={budgetMin} onChange={e => setBudgetMin(Number(e.target.value))} className="w-24 bg-gray-950 border border-gray-800 rounded-lg p-2 text-white" />
                    <span className="text-gray-500">to</span>
                    <input type="number" value={budgetMax} onChange={e => setBudgetMax(Number(e.target.value))} className="w-24 bg-gray-950 border border-gray-800 rounded-lg p-2 text-white" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Location</label>
                  <input type="text" value={location} onChange={e => setLocation(e.target.value)} placeholder="e.g., San Francisco, CA" className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:outline-none focus:border-accent-green" />
                </div>
                <div className="flex items-center space-x-3">
                  <input type="checkbox" id="remote" checked={remoteOnly} onChange={e => setRemoteOnly(e.target.checked)} className="w-4 h-4 rounded border-gray-800 bg-gray-950 text-accent-green focus:ring-accent-green focus:ring-offset-gray-900" />
                  <label htmlFor="remote" className="text-sm text-gray-300">Remote Only</label>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <label className="block text-sm font-medium text-gray-400 mb-4">Select Platforms to Scan</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {CANONICAL_PLATFORMS.map((key) => {
                    const config = PLATFORM_CONFIG[key];
                    const Icon = config.icon;
                    const isSelected = platforms.includes(key);
                    return (
                      <div 
                        key={key}
                        onClick={() => togglePlatform(key)}
                        className={`flex items-center space-x-3 p-4 rounded-xl border cursor-pointer transition-all ${
                          isSelected ? 'border-accent-green bg-emerald-500/10' : 'border-gray-800 bg-gray-950 hover:border-gray-600'
                        }`}
                      >
                        <div className={`w-5 h-5 rounded border flex items-center justify-center ${isSelected ? 'bg-accent-green border-accent-green' : 'border-gray-600'}`}>
                          {isSelected && <div className="w-2 h-2 bg-gray-950 rounded-sm"></div>}
                        </div>
                        <Icon size={20} className={isSelected ? 'text-white' : 'text-gray-500'} />
                        <span className={isSelected ? 'text-white font-medium' : 'text-gray-400'}>{config.name}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {formError && (
        <div className="mt-4 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3">{formError}</div>
      )}
      {/* Actions */}
      <div className="flex justify-between mt-8 pt-6 border-t border-gray-800">
        <Button variant="ghost" onClick={handleBack} disabled={step === 0}>Back</Button>
        {step < STEPS.length - 1 ? (
          <Button variant="primary" onClick={handleNext}>Next Step</Button>
        ) : (
          <Button variant="primary" onClick={handleSave} isLoading={loading}>Save Profile</Button>
        )}
      </div>
    </div>
  );
}
