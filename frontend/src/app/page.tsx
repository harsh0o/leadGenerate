"use client";

import { motion } from 'framer-motion';
import { PERSONA_CONFIG } from '@/lib/constants';
import { PersonaType } from '@/lib/types';
import { useRouter } from 'next/navigation';
import { usePersonaContext } from '@/providers/PersonaProvider';

export default function LandingPage() {
  const router = useRouter();
  const { setPersona } = usePersonaContext();

  const handleSelect = (key: string) => {
    setPersona(key as PersonaType);
    router.push('/dashboard');
  };

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden bg-gray-950 p-4">
      {/* Background gradient blur */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-accent-green/20 rounded-full blur-[120px] opacity-20 pointer-events-none"></div>
      
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center z-10 mb-12"
      >
        <h1 className="text-5xl font-extrabold mb-4 tracking-tight">
          Welcome to <span className="text-accent-green">LeadHunter</span> AI
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto">
          Select your workflow persona to customize your lead generation experience.
        </p>
      </motion.div>

      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full z-10"
      >
        {Object.entries(PERSONA_CONFIG).map(([key, config]) => (
          <motion.button
            key={key}
            variants={item}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleSelect(key)}
            className="bg-gray-900 border border-gray-800 rounded-2xl p-8 text-left hover:border-gray-600 transition-colors group relative overflow-hidden"
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-6 ${config.color} bg-opacity-20 group-hover:bg-opacity-30 transition-all`}>
              <config.icon className={`${config.color.replace('bg-', 'text-')}`} size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">{config.label}</h3>
            <p className="text-gray-400 text-sm mb-6">
              Optimized pipeline for {config.label.toLowerCase()}s looking to find the best opportunities across the web.
            </p>
            <div className="flex flex-wrap gap-2">
              {config.default_tags.slice(0, 3).map((tag: string) => (
                <span key={tag} className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded-md">
                  {tag}
                </span>
              ))}
            </div>
          </motion.button>
        ))}
      </motion.div>
    </div>
  );
}
