'use client';

import React, { useState, useEffect } from 'react';
import { useJobStore } from '@/stores/useJobStore';
import { Film, Play, CheckCircle, Clock, Plus, Cpu, AlertCircle } from 'lucide-react';
import { formatIST } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';

export default function JobsPipelinePage() {
  const { jobs, submitJob, fetchJobsList, isLoading } = useJobStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [cameraId, setCameraId] = useState('CAM-26');
  const [sourceKey, setSourceKey] = useState('cctv_feeds/gt_karnal_feed_live.mp4');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchJobsList();
  }, [fetchJobsList]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceKey) return;
    setIsSubmitting(true);
    try {
      await submitJob({ camera_id: cameraId, source_file_key: sourceKey });
      setIsModalOpen(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Banner */}
      <div className="bg-surface border border-border-warm rounded-[4px] p-4 shadow-gov-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="font-heading font-black text-lg uppercase tracking-wider text-navy-950 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-saffron-600" />
            Video Ingestion & ANPR Inference Pipeline
          </h2>
          <p className="font-sans text-xs text-slate-500 mt-0.5">
            Distributed YOLOv8 + OCR + Vector Re-ID pipeline tracking vehicle embeddings from raw video feeds.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-navy-900 hover:bg-navy-950 text-white rounded-[3px] font-heading font-bold text-xs uppercase tracking-wider shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4 text-saffron-400" />
          <span>INGEST VIDEO FEED</span>
        </button>
      </div>

      {/* Jobs Cards List */}
      <div className="space-y-3">
        {jobs.length === 0 ? (
          <div className="bg-surface border border-border-warm rounded-[4px] p-8 text-center text-slate-400 font-mono text-xs">
            {isLoading ? 'SYNCING JOBS WITH FASTAPI PIPELINE...' : 'NO VIDEO INGESTION JOBS FOUND'}
          </div>
        ) : (
          jobs.map((job) => (
            <div
              key={job.id}
              className="bg-surface border border-border-warm rounded-[4px] p-4 shadow-gov-sm"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-border-subtle">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold bg-navy-950 text-white px-2 py-0.5 rounded">
                    {job.id}
                  </span>
                  <span className="font-heading font-bold text-sm uppercase text-navy-950">
                    Target Camera: {job.camera_id}
                  </span>
                  <span className="font-mono text-xs text-slate-500 truncate max-w-xs">
                    ({job.source_file_key})
                  </span>
                </div>

                <div>
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded font-mono text-[11px] font-bold uppercase ${
                      job.status === 'completed'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-600/30'
                        : 'bg-saffron-50 text-saffron-700 border border-saffron-600/30'
                    }`}
                  >
                    {job.status === 'completed' ? (
                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                    ) : (
                      <Clock className="w-3 h-3 text-saffron-600 animate-spin" />
                    )}
                    {job.status} ({job.progress}%)
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-3">
                <div className="w-full bg-tint rounded-full h-2 overflow-hidden border border-border-warm">
                  <div
                    className={`h-full transition-all duration-500 ${
                      job.status === 'completed' ? 'bg-emerald-600' : 'bg-saffron-600'
                    }`}
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>

              {/* Job Statistics */}
              <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                <div>
                  <span className="text-slate-400 block text-[10px]">FRAMES PROCESSED</span>
                  <span className="font-bold text-navy-950">
                    {job.processed_frames?.toLocaleString() || 0} / {job.total_frames?.toLocaleString() || 0}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">DETECTED TRACKS</span>
                  <span className="font-bold text-emerald-700">
                    {job.detected_tracks || 0} Vehicles
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">INFERENCE ENGINE</span>
                  <span className="text-navy-950 font-semibold">YOLOv8x + ByteTrack</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">QUEUED AT</span>
                  <span className="text-slate-600">{formatIST(job.created_at)}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Ingest Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Ingest Video Stream / Recorded CCTV Feed"
        subtitle="POST /api/v1/jobs (Camera ID + Source Key)"
        maxWidth="md"
      >
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-heading uppercase tracking-wider font-bold text-slate-700 mb-1">
              Select Camera Node
            </label>
            <select
              value={cameraId}
              onChange={(e) => setCameraId(e.target.value)}
              className="w-full px-3 py-2 bg-tint border border-border-warm rounded font-mono text-navy-950 focus:outline-none focus:border-navy-900"
            >
              <option value="CAM-12">CAM-12 (Azadpur Mandi)</option>
              <option value="CAM-14">CAM-14 (Shahdara Flyover)</option>
              <option value="CAM-18">CAM-18 (Mukarba Chowk)</option>
              <option value="CAM-26">CAM-26 (GT Karnal Road)</option>
              <option value="CAM-31">CAM-31 (Singhu Border)</option>
              <option value="CAM-08">CAM-08 (Ashram Flyover)</option>
            </select>
          </div>

          <div>
            <label className="block font-heading uppercase tracking-wider font-bold text-slate-700 mb-1">
              Source File Key / RTSP URI
            </label>
            <input
              type="text"
              required
              value={sourceKey}
              onChange={(e) => setSourceKey(e.target.value)}
              placeholder="e.g. s3://surveillance-cctv/highway_gantry.mp4"
              className="w-full px-3 py-2 bg-tint border border-border-warm rounded font-mono text-navy-950 focus:outline-none focus:border-navy-900"
            />
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-1.5 font-heading font-semibold uppercase tracking-wider text-slate-600 hover:bg-tint rounded"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-1.5 bg-navy-900 hover:bg-navy-950 text-white rounded font-heading font-bold uppercase tracking-wider shadow-sm transition-colors"
            >
              {isSubmitting ? 'Queueing via API...' : 'Queue Video Job'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
