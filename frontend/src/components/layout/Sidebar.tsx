"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, Search, Activity, Settings, Menu } from 'lucide-react';
import { useState } from 'react';
import { usePersonaContext } from '@/providers/PersonaProvider';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/leads', label: 'Leads', icon: Users },
  { href: '/profiles', label: 'Profiles', icon: Search },
  { href: '/radar', label: 'Radar', icon: Activity },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const { config } = usePersonaContext();
  
  if (!pathname || pathname === '/') return null;

  return (
    <aside className={twMerge("bg-gray-900 border-r border-gray-800 transition-all flex flex-col", collapsed ? "w-20" : "w-64")}>
      <div className="p-4 flex items-center justify-between border-b border-gray-800 h-16">
        {!collapsed && <span className="font-bold text-xl text-accent-green">LeadHunter<span className="text-white">AI</span></span>}
        <button onClick={() => setCollapsed(!collapsed)} className="text-gray-400 hover:text-white p-1">
          <Menu size={24} />
        </button>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const active = pathname?.startsWith(item.href) ?? false;
          return (
            <Link key={item.href} href={item.href}
              className={clsx(
                "flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors",
                active ? "bg-gray-800 text-accent-green" : "text-gray-400 hover:bg-gray-800 hover:text-white"
              )}>
              <item.icon size={20} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      {config && !collapsed && (
        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center space-x-2 text-sm text-gray-400">
            <config.icon size={16} className={config.color.replace('bg-', 'text-')} />
            <span>{config.label} Persona</span>
          </div>
        </div>
      )}
    </aside>
  );
}
