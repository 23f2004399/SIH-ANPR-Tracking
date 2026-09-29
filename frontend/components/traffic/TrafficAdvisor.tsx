'use client';

import React from 'react';
import { useTrafficStore } from '@/stores/useTrafficStore';
import { Sparkles, CheckCircle2, TrendingDown, Leaf, Clock, ArrowRight } from 'lucide-react';

export function TrafficAdvisor() {
  const { advisories } = useTrafficStore();

  const priorityStyles = {
    urgent: 'bg-crimson-50 text-crimson-700 border-crimson-700/40',
    advisory: 'bg-saffron-50 text-saffron-700 border-saffron-600/40',
    info: 'bg-cobalt-50 text-cobalt-600 border-cobalt-600/40',
  };

  return (
    <div className="bg-surface border border-border-warm rounded-[4px] overflow-hidden shadow-gov-sm flex flex-col">
      <div className="bg-navy-900 text-white px-4 py-2.5 flex items-center justify-between border-b border-navy-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-saffron-400" />
          <h4 className="font-heading font-bold text-xs uppercase tracking-wider">
            AI Smart City Diversion & Signal Advisory Engine
          </h4>
        </div>
        <span className="font-mono text-[10px] bg-navy-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700/50">
          MoRTH ITMS ACTIVE
        </span>
      </div>

      <div className="p-4 space-y-3">
        {advisories.map((adv) => (
          <div
            key={adv.id}
            className="bg-porcelain border border-border-warm rounded-[3px] p-3.5 hover:border-slate-400 transition-colors"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 rounded-[2px] border font-mono text-[10px] font-bold uppercase tracking-wider ${
                    priorityStyles[adv.priority]
                  }`}
                >
                  {adv.priority} // {adv.id}
                </span>
                <span className="font-heading font-bold text-xs text-navy-950 uppercase tracking-wide">
                  {adv.title}
                </span>
              </div>

              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="flex items-center gap-1 text-emerald-700 font-bold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-600/30">
                  <Leaf className="w-3 h-3" />
                  -{adv.co2_reduction_kg} kg CO₂
                </span>
                <span className="flex items-center gap-1 text-saffron-700 font-bold bg-saffron-50 px-1.5 py-0.5 rounded border border-saffron-600/30">
                  <Clock className="w-3 h-3" />
                  -{adv.time_saved_minutes} min delay
                </span>
              </div>
            </div>

            <p className="mt-2 text-xs text-slate-700 font-sans">
              <b>Impact:</b> {adv.impact_summary}
            </p>

            <div className="mt-2.5 pt-2 border-t border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
              <span className="text-slate-500 text-[11px]">
                <b>ACTION:</b> {adv.recommended_action}
              </span>
              <button
                onClick={() =>
                  alert(`[AUTOMATED SIGNAL OVERRIDE SENT] Transmitted signal optimization command for ${adv.id}.`)
                }
                className="inline-flex items-center gap-1 px-3 py-1 bg-navy-900 hover:bg-navy-950 text-white rounded-[2px] font-heading font-bold text-[11px] uppercase tracking-wider transition-colors shrink-0 shadow-sm"
              >
                <span>EXECUTE OVERRIDE</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
