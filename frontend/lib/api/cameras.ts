import { apiClient } from './client';
import { Camera, CameraIn } from '@/types/api';
import { MOCK_CAMERAS } from '../constants';

export async function fetchCameras(): Promise<Camera[]> {
  try {
    const res = await apiClient.get('/api/v1/cameras');
    const payload = res.data;
    if (payload && Array.isArray(payload.data)) {
      return payload.data;
    }
    if (Array.isArray(payload)) {
      return payload;
    }
  } catch (error) {
    console.warn('[ZyroTrace] GET /api/v1/cameras failed. Using cached fallback cameras.', error);
  }
  return MOCK_CAMERAS;
}

export async function createCamera(camera: CameraIn): Promise<Camera> {
  const res = await apiClient.post('/api/v1/cameras', camera);
  const payload = res.data;
  if (payload?.data) {
    return payload.data;
  }
  if (payload?.id) {
    return payload;
  }
  // Fallback in case of unexpected envelope
  return {
    ...camera,
    location_label: camera.location_label || null,
    road_segment_id: camera.road_segment_id || null,
    is_active: camera.is_active ?? true,
    created_at: new Date().toISOString(),
  };
}
