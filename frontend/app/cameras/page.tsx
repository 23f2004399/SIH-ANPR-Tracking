'use client';

import React, { useState, useEffect } from 'react';
import { CameraGridTable } from '@/components/cameras/CameraGridTable';
import { AddCameraModal } from '@/components/cameras/AddCameraModal';
import { useCameraStore } from '@/stores/useCameraStore';
import { Camera, Radio, MapPin, Eye, CheckCircle2 } from 'lucide-react';

export default function CamerasPage() {
  const [isAddOpen, setIsAddOpen] = useState(false);
  const { selectedCamera, fetchCamerasList } = useCameraStore();

  useEffect(() => {
    fetchCamerasList();
  }, [fetchCamerasList]);

  return (
    <div className="space-y-4">
      {/* Top Banner / Summary */}
      <div className="bg-surface border border-border-warm rounded-[4px] p-4 shadow-gov-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="font-heading font-black text-lg uppercase tracking-wider text-navy-950 flex items-center gap-2">
            <Radio className="w-5 h-5 text-saffron-600 animate-pulse" />
            ANPR Camera Node Registry & Telemetry
          </h2>
          <p className="font-sans text-xs text-slate-500 mt-0.5">
            Surveillance gantries, highway overpass sensors, and RTSP stream ingest endpoints across Delhi-NCR.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="bg-emerald-50 text-emerald-700 border border-emerald-600/30 px-2.5 py-1 rounded font-bold">
            LIVE GANTRIES ONLINE
          </span>
          <span className="bg-tint text-slate-600 border border-border-warm px-2.5 py-1 rounded">
            PORT 8000 API SYNC
          </span>
        </div>
      </div>

      {/* Selected Camera Telemetry Detail (if selected) */}
      {selectedCamera && (
        <div className="bg-tint border border-border-warm rounded-[4px] p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded bg-navy-950 text-white flex items-center justify-center shrink-0">
              <Camera className="w-5 h-5 text-saffron-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-xs bg-navy-900 text-white px-2 py-0.5 rounded">
                  {selectedCamera.id}
                </span>
                <span className="font-heading font-bold text-sm uppercase text-navy-950">
                  {selectedCamera.name}
                </span>
              </div>
              <p className="font-mono text-xs text-slate-600 mt-1">
                WGS84: {selectedCamera.latitude.toFixed(4)}° N, {selectedCamera.longitude.toFixed(4)}° E · {selectedCamera.location_label}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-emerald-700 bg-emerald-50 border border-emerald-600/30 px-2.5 py-1 rounded font-bold">
              1080P @ 30 FPS // RTSP STREAM STABLE
            </span>
          </div>
        </div>
      )}

      {/* Full Camera Grid Table */}
      <CameraGridTable onOpenAddModal={() => setIsAddOpen(true)} />

      {/* Add Camera Modal Dialog */}
      <AddCameraModal isOpen={isAddOpen} onClose={() => setIsAddOpen(false)} />
    </div>
  );
}
