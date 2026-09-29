'use client';

import React from 'react';
import { useVehicleStore } from '@/stores/useVehicleStore';
import { HsrpPlate } from '@/components/ui/HsrpPlate';
import {
  FileText,
  Radio,
  FileCheck,
  SearchCode,
  Shield,
  ExternalLink,
} from 'lucide-react';
import { formatIST } from '@/lib/utils';

export function EvidenceDossier() {
  const {
    selectedTrack,
    evidence,
    setSimilarModalOpen,
  } = useVehicleStore();

  if (!selectedTrack) {
    return (
      <div className="bg-surface border border-border-warm rounded-[4px] p-6 text-center text-slate-400 font-mono text-xs">
        NO VEHICLE TRACK SELECTED
      </div>
    );
  }

  const plateCrop = evidence.find((e) => e.asset_type === 'plate_crop');
  const vehicleCrop = evidence.find((e) => e.asset_type === 'vehicle_crop');

  return (
    <div className="bg-surface border border-border-warm rounded-[4px] overflow-hidden shadow-gov-sm flex flex-col gap-0 select-none">
      {/* Dossier Header */}
      <div className="bg-navy-900 text-white px-4 py-2.5 flex items-center justify-between border-b border-navy-800">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-saffron-500" />
          <h4 className="font-heading font-bold text-xs uppercase tracking-wider">
            Forensic Telemetry Dossier // Track #{selectedTrack.id}
          </h4>
        </div>
        <span className="font-mono text-[10px] bg-navy-800 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700/50">
          VAHAN 4.0 SYNC
        </span>
      </div>

      <div className="p-4 space-y-4">
        {/* Optical Crop Evidence Rail */}
        <div>
          <span className="font-heading font-bold text-[11px] uppercase tracking-wider text-slate-500 block mb-2">
            OPTICAL CROP ARTIFACTS
          </span>
          <div className="grid grid-cols-2 gap-2">
            {/* Cropped Plate */}
            <div className="bg-tint border border-border-warm rounded p-2 flex flex-col items-center justify-center">
              <span className="font-mono text-[9px] text-slate-500 uppercase font-semibold mb-1">
                Extracted Plate
              </span>
              <HsrpPlate
                plateText={selectedTrack.primary_plate}
                size="md"
                vehicleType={selectedTrack.vehicle_type}
              />
              <span className="font-mono text-[9px] text-emerald-700 mt-1 font-bold">
                CONF: {Math.round(selectedTrack.confidence * 100)}%
              </span>
            </div>

            {/* Vehicle Crop */}
            <div className="bg-tint border border-border-warm rounded p-1 overflow-hidden relative group">
              <div
                className="w-full h-20 bg-cover bg-center rounded-[2px]"
                style={{
                  backgroundImage: `url(${
                    vehicleCrop?.file_url ||
                    'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=400&q=80'
                  })`,
                }}
              />
              <div className="absolute inset-x-1 bottom-1 bg-navy-950/80 text-[9px] font-mono text-slate-200 px-1 py-0.5 rounded-[1px] flex justify-between">
                <span>RE-ID CROP</span>
                <span>{selectedTrack.vehicle_color}</span>
              </div>
            </div>
          </div>
        </div>

        {/* VAHAN 4.0 National Registry Extract */}
        <div className="border border-border-subtle rounded bg-porcelain p-3">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-border-warm">
            <span className="font-heading font-bold text-xs uppercase tracking-wider text-navy-950 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-cobalt-600" />
              VAHAN 4.0 National Registry
            </span>
            <span className="font-mono text-[10px] text-emerald-700 font-bold bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-600/30">
              VERIFIED
            </span>
          </div>

          <div className="grid grid-cols-2 gap-y-2 text-xs font-mono">
            <div>
              <span className="text-slate-400 block text-[10px]">VEHICLE MODEL</span>
              <span className="font-bold text-navy-950 text-[11px]">
                {selectedTrack.make_model || 'Hyundai Creta SX (O)'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block text-[10px]">REGISTRATION RTO</span>
              <span className="font-bold text-navy-950 text-[11px]">
                {selectedTrack.registration_state || 'Haryana (Gurugram)'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block text-[10px]">REGISTERED OWNER</span>
              <span className="font-semibold text-slate-700 text-[11px]">
                {selectedTrack.owner_name_masked || 'R**** K**** S****'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block text-[10px]">CHASSIS / ENGINE</span>
              <span className="font-semibold text-slate-700 text-[11px]">
                MALC481••• / G4FLM•••
              </span>
            </div>

            <div className="col-span-2 pt-1 border-t border-border-subtle">
              <span className="text-slate-400 block text-[10px]">CURRENT LEGAL STATUS</span>
              <span
                className={`font-bold text-[11px] uppercase ${
                  selectedTrack.is_hotlist ? 'text-crimson-700' : 'text-emerald-700'
                }`}
              >
                {selectedTrack.vahan_status || 'FLAGGED / POLICE SURVEILLANCE'}
              </span>
            </div>
          </div>
        </div>

        {/* Tactical Actions Strip */}
        <div className="space-y-2 pt-1">
          <button
            onClick={() => setSimilarModalOpen(true)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-tint hover:bg-border-warm text-navy-950 border border-border-warm rounded-[3px] font-heading font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
          >
            <SearchCode className="w-3.5 h-3.5 text-saffron-600" />
            <span>FIND RE-ID SIMILAR VEHICLES</span>
          </button>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => alert(`[INTERCEPTOR DISPATCHED] Patrol units alerted for ${selectedTrack.primary_plate}`)}
              className="flex items-center justify-center gap-1.5 px-3 py-2 bg-crimson-700 hover:bg-crimson-800 text-white rounded-[3px] font-heading font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
            >
              <Radio className="w-3.5 h-3.5" />
              <span>DISPATCH PATROL</span>
            </button>

            <button
              onClick={() => alert(`[E-CHALLAN ISSUED] Violation ticket generated under Sec 183 MV Act for ${selectedTrack.primary_plate}`)}
              className="flex items-center justify-center gap-1.5 px-3 py-2 bg-navy-900 hover:bg-navy-950 text-white rounded-[3px] font-heading font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
            >
              <FileCheck className="w-3.5 h-3.5 text-saffron-400" />
              <span>ISSUE E-CHALLAN</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
