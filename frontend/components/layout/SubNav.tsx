'use client';

import React from 'react';
import { useVehicleStore } from '@/stores/useVehicleStore';
import { HsrpPlate } from '@/components/ui/HsrpPlate';
import { Zap, ShieldCheck } from 'lucide-react';

export function SubNav() {
  const { searchPlates, selectedTrack } = useVehicleStore();

  const demoScenarios = [
    {
      plate: 'HR 26 CX 9021',
      desc: 'Armed Robbery (Creta)',
      badgeVariant: 'crimson' as const,
      variant: 'private' as const,
    },
    {
      plate: 'DL 01 AB 1234',
      desc: 'Stolen Vehicle (Dzire)',
      badgeVariant: 'saffron' as const,
      variant: 'private' as const,
    },
    {
      plate: 'UP 16 Z 8844',
      desc: 'Overheight Truck (Tata)',
      badgeVariant: 'navy' as const,
      variant: 'commercial' as const,
    },
  ];

  return (
    <div className="bg-surface border-b border-border-warm px-4 py-2 select-none">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Quick 1-Click Verification Trigger Strip */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 text-slate-500 font-heading font-bold uppercase tracking-wider text-[11px]">
            <Zap className="w-3.5 h-3.5 text-saffron-600" />
            <span>1-Click Test Scenarios:</span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {demoScenarios.map((demo) => {
              const isSelected = selectedTrack?.primary_plate === demo.plate;
              return (
                <button
                  key={demo.plate}
                  onClick={() => searchPlates(demo.plate)}
                  className={`inline-flex items-center gap-2 px-2 py-1 rounded-[3px] border transition-all text-left ${
                    isSelected
                      ? 'bg-saffron-50 border-saffron-600 ring-1 ring-saffron-600/50 shadow-sm'
                      : 'bg-porcelain border-border-warm hover:border-slate-400 hover:bg-tint'
                  }`}
                  title={`Run ANPR query for ${demo.plate} (${demo.desc})`}
                >
                  <HsrpPlate
                    plateText={demo.plate}
                    size="sm"
                    variant={demo.variant}
                  />
                  <span className="font-sans text-[11px] font-semibold text-slate-700 hidden sm:inline">
                    {demo.desc}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Security & Station Clearance Stamps */}
        <div className="hidden lg:flex items-center gap-3 text-[11px] font-mono text-slate-500">
          <div className="flex items-center gap-1.5 bg-tint px-2 py-0.5 rounded-[2px] border border-border-warm">
            <ShieldCheck className="w-3 h-3 text-emerald-700" />
            <span>CLEARANCE: LEVEL-3 C4I</span>
          </div>
          <div className="text-slate-400">|</div>
          <div className="text-slate-500">
            NODE: <span className="font-bold text-navy-950">NORTH-DELHI-HQ</span>
          </div>
        </div>
      </div>
    </div>
  );
}
