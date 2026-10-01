'use client';

import React from 'react';
import { useVehicleStore } from '@/stores/useVehicleStore';
import { AlertTriangle, Radio, ShieldAlert, Crosshair } from 'lucide-react';
import { HsrpPlate } from '@/components/ui/HsrpPlate';

export function HotlistAlertBanner() {
  const { selectedTrack } = useVehicleStore();

  if (!selectedTrack?.is_hotlist) {
    return null;
  }

  return (
    <div className="bg-saffron-50 border-2 border-saffron-600 rounded-[4px] p-3 shadow-gov-md animate-alert-pulse">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-[3px] bg-saffron-600 text-white flex items-center justify-center shrink-0 shadow-sm">
            <ShieldAlert className="w-5 h-5 animate-pulse" />
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-heading font-black text-sm uppercase tracking-wider text-saffron-700 bg-saffron-100/80 px-2 py-0.5 rounded-[2px] border border-saffron-600/40">
                ACTIVE HOTLIST ALERT // PRIORITY INTERCEPT
              </span>
              <HsrpPlate
                plateText={selectedTrack.primary_plate}
                size="sm"
                vehicleType={selectedTrack.vehicle_type}
              />
              <span className="font-mono text-xs font-bold text-navy-950">
                {selectedTrack.make_model}
              </span>
            </div>

            <p className="mt-1 font-mono text-xs font-semibold text-saffron-700 tracking-wide">
              REASON: {selectedTrack.hotlist_reason}
            </p>
          </div>
        </div>

        {/* Action button */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => alert(`[DISPATCH INITIATED] PCR Vans alerted for ${selectedTrack.primary_plate} interception at Singhu Toll.`)}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-saffron-700 hover:bg-saffron-800 text-white rounded-[3px] font-heading font-bold text-xs uppercase tracking-wider shadow-sm transition-colors"
          >
            <Radio className="w-3.5 h-3.5" />
            <span>DISPATCH INTERCEPT PATROL</span>
          </button>
        </div>
      </div>
    </div>
  );
}
