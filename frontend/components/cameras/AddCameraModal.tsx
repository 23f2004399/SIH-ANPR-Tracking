'use client';

import React, { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { CameraIn } from '@/types/api';
import { useCameraStore } from '@/stores/useCameraStore';

interface AddCameraModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AddCameraModal({ isOpen, onClose }: AddCameraModalProps) {
  const { addCameraNode } = useCameraStore();
  const [formData, setFormData] = useState<CameraIn>({
    id: 'CAM-',
    name: '',
    latitude: 28.7,
    longitude: 77.2,
    location_label: '',
    road_segment_id: 'seg-nh44-n',
    is_active: true,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.id || !formData.name) return;

    setIsSubmitting(true);
    try {
      await addCameraNode(formData);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Register ANPR CCTV Node Gantry"
      subtitle="Adds telemetry endpoint to ITMS surveillance registry"
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <label className="block font-heading uppercase tracking-wider font-bold text-slate-700 mb-1">
              Node Identifier (ID)
            </label>
            <input
              type="text"
              required
              value={formData.id}
              onChange={(e) => setFormData({ ...formData, id: e.target.value.toUpperCase() })}
              placeholder="CAM-42"
              className="w-full px-3 py-1.5 bg-tint border border-border-warm rounded font-mono text-navy-950 focus:outline-none focus:border-navy-900"
            />
          </div>

          <div>
            <label className="block font-heading uppercase tracking-wider font-bold text-slate-700 mb-1">
              Highway Segment ID
            </label>
            <select
              value={formData.road_segment_id || ''}
              onChange={(e) => setFormData({ ...formData, road_segment_id: e.target.value })}
              className="w-full px-3 py-1.5 bg-tint border border-border-warm rounded font-mono text-navy-950 focus:outline-none focus:border-navy-900"
            >
              <option value="seg-nh44-n">seg-nh44-n (NH-44 North Trunk)</option>
              <option value="seg-ring-s">seg-ring-s (Inner Ring Road)</option>
              <option value="seg-dnd">seg-dnd (DND Flyway)</option>
              <option value="seg-or-w">seg-or-w (Outer Ring Road West)</option>
            </select>
          </div>

          <div className="col-span-2">
            <label className="block font-heading uppercase tracking-wider font-bold text-slate-700 mb-1">
              Gantry Name & Landmark
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Dhaula Kuan Cloverleaf Underpass"
              className="w-full px-3 py-1.5 bg-tint border border-border-warm rounded font-sans text-navy-950 focus:outline-none focus:border-navy-900"
            />
          </div>

          <div>
            <label className="block font-heading uppercase tracking-wider font-bold text-slate-700 mb-1">
              Latitude (WGS84)
            </label>
            <input
              type="number"
              step="0.0001"
              required
              value={formData.latitude}
              onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
              className="w-full px-3 py-1.5 bg-tint border border-border-warm rounded font-mono text-navy-950 focus:outline-none focus:border-navy-900"
            />
          </div>

          <div>
            <label className="block font-heading uppercase tracking-wider font-bold text-slate-700 mb-1">
              Longitude (WGS84)
            </label>
            <input
              type="number"
              step="0.0001"
              required
              value={formData.longitude}
              onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
              className="w-full px-3 py-1.5 bg-tint border border-border-warm rounded font-mono text-navy-950 focus:outline-none focus:border-navy-900"
            />
          </div>
        </div>

        <div className="pt-3 border-t border-border-warm flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-heading font-semibold uppercase tracking-wider text-slate-600 hover:bg-tint rounded"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-5 py-1.5 bg-navy-900 hover:bg-navy-950 text-white rounded font-heading font-bold text-xs uppercase tracking-wider shadow-sm transition-colors"
          >
            {isSubmitting ? 'Registering...' : 'Register Camera'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
