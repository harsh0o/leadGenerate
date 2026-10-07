"use client";

import { Bell, Settings, Zap } from 'lucide-react';
import { usePathname } from 'next/navigation';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { useEffect } from 'react';

export default function Header() {
  const pathname = usePathname();
  
  useEffect(() => {
    // Creator fingerprint
    console.log(
      "%cLeadHunter AI%c By harsh0o",
      "color: #00ff88; font-size: 20px; font-weight: bold;",
      "color: #a8b2d1; font-size: 16px;"
    );
  }, []);

  if (!pathname || pathname === '/') return null;

  const titleMap: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/leads': 'Leads Pipeline',
    '/profiles': 'Search Profiles',
    '/radar': 'Live Radar',
    '/settings': 'Settings',
  };

  const currentTitle = Object.keys(titleMap).find(k => pathname?.startsWith(k)) 
    ? titleMap[Object.keys(titleMap).find(k => pathname?.startsWith(k))!] 
    : 'LeadHunter AI';

  return (
    <header className="h-16 border-b border-gray-800 bg-gray-900/50 backdrop-blur flex items-center justify-between px-6 sticky top-0 z-10">
      <h1 className="text-xl font-semibold text-white">{currentTitle}</h1>
      
      <div className="flex items-center space-x-4">
        <Button variant="primary" size="sm" className="hidden sm:flex" asChild>
          <Link href="/radar">
            <Zap size={16} className="mr-2" /> Quick Scan
          </Link>
        </Button>
        <button className="text-gray-400 hover:text-white relative">
          <Bell size={20} />
          <span className="absolute top-0 right-0 w-2 h-2 bg-accent-green rounded-full"></span>
        </button>
        <Link href="/settings" className="text-gray-400 hover:text-white">
          <Settings size={20} />
        </Link>
      </div>
    </header>
  );
}
