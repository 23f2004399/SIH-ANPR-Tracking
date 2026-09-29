'use client';

import React from 'react';
import { useVehicleStore } from '@/stores/useVehicleStore';
import { Modal } from '@/components/ui/Modal';
import { HsrpPlate } from '@/components/ui/HsrpPlate';
import { Sparkles, ArrowRight, ShieldCheck } from 'lucide-react';

export function SimilarVehiclesModal() {
  const {
    isSimilarModalOpen,
    setSimilarModalOpen,
    similarVehicles,
    selectedTrack,
    searchPlates,
  } = useVehicleStore();

  const handleSelectSimilar = (plate: string) => {
    setSimilarModalOpen(false);
    searchPlates(plate);
  };

  return (
    <Modal
      isOpen={isSimilarModalOpen}
      onClose={() => setSimilarModalOpen(false)}
      title="AI Vector Re-ID Visual Appearance Matching"
      subtitle={`pgvector cosine similarity embeddings for ${selectedTrack?.primary_plate || 'Suspect'}`}
      maxWidth="2xl"
    >
      <div className="space-y-4">
        <div className="bg-tint border border-border-warm rounded p-3 text-xs font-mono text-slate-600">
          <p className="flex items-center gap-1.5 font-bold text-navy-950 mb-1">
            <Sparkles className="w-3.5 h-3.5 text-saffron-600" />
            DEEP LEARNING VEHICLE RE-IDENTIFICATION (BEL DEFENSE RE-ID ENGINE)
          </p>
          <p>
            Surfaces vehicles sharing visual vehicle body vectors across non-overlapping CCTV cameras, even if license plates have been swapped, obscured with mud, or damaged.
          </p>
        </div>

        <div className="space-y-2">
          {similarVehicles.map((vehicle) => {
            const matchPct = Math.round(vehicle.similarity_score * 100);
            return (
              <div
                key={vehicle.track_id}
                className="bg-porcelain border border-border-warm rounded-[3px] p-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:border-slate-400 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-16 h-12 rounded-[2px] bg-cover bg-center shrink-0 border border-border-warm"
                    style={{ backgroundImage: `url(${vehicle.thumbnail_url})` }}
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <HsrpPlate plateText={vehicle.plate_text} size="sm" />
                      <span className="font-heading font-bold text-xs uppercase text-navy-950">
                        {vehicle.vehicle_type}
                      </span>
                    </div>
                    <div className="font-mono text-[10px] text-slate-500 mt-1">
                      LAST SEEN: {vehicle.location_name || 'Highway Junction'} · {vehicle.color}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
                  <div className="text-right">
                    <span className="font-mono text-xs font-bold text-saffron-700 bg-saffron-50 px-2 py-0.5 rounded border border-saffron-600/30">
                      {matchPct}% SIMILARITY
                    </span>
                  </div>

                  <button
                    onClick={() => handleSelectSimilar(vehicle.plate_text)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-navy-900 hover:bg-navy-950 text-white rounded-[2px] font-heading font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
                  >
                    <span>TRACK</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Modal>
  );
}
