'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ShieldAlert,
  Activity,
  Camera,
  Film,
  Radio,
  Server,
  RefreshCw,
} from 'lucide-react';
import { useUIStore } from '@/stores/useUIStore';
import { checkBackendHealth } from '@/lib/api/client';
import { formatISTTime } from '@/lib/utils';

export function Header() {
  const pathname = usePathname();
  const { backendStatus, setBackendStatus } = useUIStore();
  const [istTime, setIstTime] = useState<string>('');
  const [isPinging, setIsPinging] = useState(false);

  useEffect(() => {
    const updateTime = () => setIstTime(formatISTTime(new Date()));
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handlePingBackend = async () => {
    setIsPinging(true);
    const isUp = await checkBackendHealth();
    setBackendStatus(isUp ? 'connected' : 'demo');
    setIsPinging(false);
  };

  useEffect(() => {
    handlePingBackend();
  }, []);

  const navLinks = [
    {
      href: '/police',
      label: 'Police Surveillance',
      badge: 'C4I HOTLIST',
      icon: ShieldAlert,
    },
    {
      href: '/traffic',
      label: 'Traffic Intelligence',
      badge: 'URBAN FLOW',
      icon: Activity,
    },
    {
      href: '/cameras',
      label: 'Camera Network',
      badge: 'NODES',
      icon: Camera,
    },
    {
      href: '/jobs',
      label: 'Video Pipeline',
      badge: 'INFERENCE',
      icon: Film,
    },
  ];

  return (
    <header className="bg-navy-950 text-porcelain border-b border-navy-800 sticky top-0 z-40 select-none">
      {/* Institutional Top Bar */}
      <div className="max-w-7xl mx-auto px-4 py-1.5 flex items-center justify-between border-b border-navy-800/80 text-[11px] font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <span className="text-amber-400 font-bold">☸</span>
          <span className="tracking-wider uppercase text-slate-300 font-semibold">
            Government of India · Bharat Electronics Ltd (BEL) · MoRTH
          </span>
          <span className="text-navy-800">|</span>
          <span className="text-[10px] text-amber-500/90 font-mono tracking-widest hidden sm:inline">
            SMART INDIA HACKATHON DEFENSE PROTOTYPE
          </span>
        </div>

        <div className="flex items-center gap-4">
          {/* Live IST Clock */}
          <div className="flex items-center gap-1.5 text-slate-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="tabular-nums font-mono font-bold text-xs tracking-wider">
              {istTime ? `${istTime} IST` : '14:32:00 IST'}
            </span>
          </div>

          {/* Backend Connection Indicator */}
          <button
            onClick={handlePingBackend}
            disabled={isPinging}
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] border text-[10px] font-mono transition-colors ${
              backendStatus === 'connected'
                ? 'bg-emerald-950/80 border-emerald-600 text-emerald-400 hover:bg-emerald-900'
                : 'bg-navy-900 border-saffron-600/60 text-saffron-400 hover:bg-navy-800'
            }`}
            title="Click to check FastAPI connectivity (port 8000)"
          >
            <Server className="w-3 h-3" />
            <span className="font-bold">
              {backendStatus === 'connected' ? 'LIVE BACKEND: 8000' : 'OFFLINE DEMO MODE'}
            </span>
            <RefreshCw className={`w-2.5 h-2.5 ml-0.5 ${isPinging ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Primary Command Navigation Bar */}
      <div className="max-w-7xl mx-auto px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/police" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-[3px] bg-saffron-600 flex items-center justify-center font-heading font-black text-white text-lg tracking-tighter shadow-sm group-hover:bg-saffron-500 transition-colors">
              ZT
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-heading font-bold text-lg tracking-wider text-white">
                  ZYROTRACE<span className="text-saffron-600">.AI</span>
                </span>
                <span className="bg-navy-800 text-slate-300 px-1.5 py-0.2 rounded text-[10px] font-mono font-semibold tracking-widest border border-slate-700/50">
                  v2.4 SECURE
                </span>
              </div>
              <p className="font-sans text-[10px] text-slate-400 tracking-wide uppercase">
                Multi-Camera ANPR Telemetry & Arterial Flow Platform
              </p>
            </div>
          </Link>
        </div>

        {/* Tactical Nav Tabs */}
        <nav className="flex items-center gap-1 bg-navy-900 p-1 rounded-[4px] border border-navy-800">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-[3px] font-heading font-semibold text-xs tracking-wider uppercase transition-all ${
                  isActive
                    ? 'bg-navy-800 text-white shadow-sm border border-slate-600/40 text-saffron-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-navy-800/40'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-saffron-500' : 'text-slate-400'}`} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
