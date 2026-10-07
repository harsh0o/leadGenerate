"use client";

import { motion } from 'framer-motion';
import { ScanEvent } from '@/lib/types';
import { useEffect, useState } from 'react';

interface RadarDisplayProps {
  isScanning: boolean;
  events: ScanEvent[];
}

export default function RadarDisplay({ isScanning, events }: RadarDisplayProps) {
  const [dots, setDots] = useState<{id: string, x: number, y: number, color: string}[]>([]);

  useEffect(() => {
    // Add a blip for every new 'found' event (batch-safe, not just the last one)
    const safe = Array.isArray(events) ? events : [];
    setDots(prev => {
      const known = new Set(prev.map(d => d.id));
      const fresh = safe.filter(e => e?.type === 'found' && e?.id && !known.has(e.id));
      if (fresh.length === 0) return prev;
      const blips = fresh.map(ev => {
        // Deterministic pseudo-position from id hash (stable across re-renders)
        let h = 0;
        for (let i = 0; i < ev.id.length; i++) h = (h * 31 + ev.id.charCodeAt(i)) >>> 0;
        const angle = (h % 360) * (Math.PI / 180);
        const radius = 20 + (h % 70);
        return {
          id: ev.id,
          x: 50 + radius * Math.cos(angle),
          y: 50 + radius * Math.sin(angle),
          color: '#00ff88',
        };
      });
      return [...prev, ...blips].slice(-20);
    });
  }, [events]);

  return (
    <div className="relative w-full max-w-md aspect-square rounded-full border border-gray-800 bg-gray-950 flex items-center justify-center overflow-hidden shadow-[0_0_50px_rgba(0,255,136,0.05)]">
      {/* Grid rings */}
      <div className="absolute inset-0 rounded-full border border-gray-800 m-8" />
      <div className="absolute inset-0 rounded-full border border-gray-800 m-16" />
      <div className="absolute inset-0 rounded-full border border-gray-800 m-24" />
      <div className="absolute inset-0 rounded-full border border-gray-800 m-32" />
      
      {/* Crosshairs */}
      <div className="absolute w-full h-px bg-gray-800" />
      <div className="absolute h-full w-px bg-gray-800" />

      {/* Center Pulse */}
      <div className="absolute w-2 h-2 rounded-full bg-accent-green z-10" />
      {isScanning && (
        <div className="absolute w-2 h-2 rounded-full bg-accent-green animate-ping z-10" />
      )}

      {/* Scanner Sweep */}
      {isScanning && (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
          className="absolute inset-0 rounded-full z-0"
          style={{
            background: 'conic-gradient(from 0deg, transparent 0deg, transparent 270deg, rgba(0, 255, 136, 0.1) 360deg)',
            transformOrigin: 'center'
          }}
        >
          <div className="absolute top-0 left-1/2 w-0.5 h-1/2 bg-gradient-to-b from-accent-green to-transparent origin-bottom" />
        </motion.div>
      )}

      {/* Blips */}
      {dots.map(dot => (
        <motion.div
          key={dot.id}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: [0, 1, 0.8, 0], scale: [0, 1, 1.2, 0.5] }}
          transition={{ duration: 3, times: [0, 0.1, 0.5, 1] }}
          className="absolute w-3 h-3 rounded-full z-20"
          style={{
            left: `${dot.x}%`,
            top: `${dot.y}%`,
            backgroundColor: dot.color,
            boxShadow: `0 0 10px ${dot.color}`
          }}
        />
      ))}
    </div>
  );
}
