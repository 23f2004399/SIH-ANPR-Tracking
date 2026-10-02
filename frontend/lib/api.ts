import {
  Camera,
  TrafficAggregate,
  VehicleTrack,
  VehicleObservation,
  EvidenceAsset,
  SimilarVehicle,
  CityTrafficAnalytics,
} from '@/types';

// In Next.js client, requests to /api/v1/... are proxied through rewrites in next.config.mjs to FastAPI
const API_BASE = '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`API error ${res.status}: ${errorText || res.statusText}`);
  }

  const json = await res.json();
  // Handle envelope responses { success: true, data: [...] } or direct objects
  if (json && typeof json === 'object' && 'data' in json && (json.data !== undefined)) {
    return json.data as T;
  }
  return json as T;
}

export async function checkBackendHealth(): Promise<{ status: string }> {
  return fetchJson<{ status: string }>('/backend-health');
}

export async function listCameras(): Promise<Camera[]> {
  return fetchJson<Camera[]>('/api/v1/cameras');
}

export async function getTrafficOverview(windowMinutes: number = 60): Promise<TrafficAggregate> {
  return fetchJson<TrafficAggregate>(`/api/v1/traffic/overview?window_minutes=${windowMinutes}`);
}

export async function getTrafficCameras(windowMinutes: number = 60): Promise<TrafficAggregate[]> {
  return fetchJson<TrafficAggregate[]>(`/api/v1/traffic/cameras?window_minutes=${windowMinutes}`);
}

export async function getTrafficSegments(windowMinutes: number = 60): Promise<TrafficAggregate[]> {
  return fetchJson<TrafficAggregate[]>(`/api/v1/traffic/segments?window_minutes=${windowMinutes}`);
}

export async function getCityTrafficAnalytics(city?: string): Promise<CityTrafficAnalytics> {
  const query = city ? `?city=${encodeURIComponent(city)}` : '';
  return fetchJson<CityTrafficAnalytics>(`/api/v1/traffic/analytics${query}`);
}

export async function getTrafficHistory(params?: {
  cameraId?: string;
  segmentId?: string;
  startTime?: string;
  endTime?: string;
  limit?: number;
  offset?: number;
}): Promise<TrafficAggregate[]> {
  const query = new URLSearchParams();
  if (params?.cameraId) query.set('camera_id', params.cameraId);
  if (params?.segmentId) query.set('segment_id', params.segmentId);
  if (params?.startTime) query.set('start_time', params.startTime);
  if (params?.endTime) query.set('end_time', params.endTime);
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset) query.set('offset', String(params.offset));

  return fetchJson<TrafficAggregate[]>(`/api/v1/traffic/history?${query.toString()}`);
}

export async function searchPlates(
  q: string,
  exact: boolean = false,
  limit: number = 20
): Promise<VehicleTrack[]> {
  return fetchJson<VehicleTrack[]>(
    `/api/v1/vehicles/search/plate?q=${encodeURIComponent(q)}&exact=${exact}&limit=${limit}`
  );
}

export async function getVehicleHistory(trackId: number): Promise<VehicleObservation[]> {
  return fetchJson<VehicleObservation[]>(`/api/v1/vehicles/${trackId}/history`);
}

export async function getVehicleEvidence(trackId: number): Promise<EvidenceAsset[]> {
  return fetchJson<EvidenceAsset[]>(`/api/v1/vehicles/${trackId}/evidence`);
}

export async function getSimilarVehicles(
  trackId: number,
  limit: number = 10
): Promise<SimilarVehicle[]> {
  return fetchJson<SimilarVehicle[]>(`/api/v1/vehicles/${trackId}/similar?limit=${limit}`);
}

export async function getVehicleStatsOverview(): Promise<{
  total_tracks: number;
  total_plates: number;
  vehicle_types: Record<string, number>;
}> {
  return fetchJson<{
    total_tracks: number;
    total_plates: number;
    vehicle_types: Record<string, number>;
  }>('/api/v1/vehicles/stats/overview');
}
