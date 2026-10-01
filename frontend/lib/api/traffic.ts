import { apiClient } from './client';
import {
  TrafficOverview,
  CameraTraffic,
  SegmentTraffic,
  TrafficAggregateRow,
  TrafficAdvisory,
} from '@/types/api';
import {
  MOCK_TRAFFIC_OVERVIEW,
  MOCK_SEGMENTS,
  MOCK_ADVISORIES,
} from '../constants';

export async function fetchTrafficOverview(
  windowMinutes: number = 60
): Promise<TrafficOverview> {
  try {
    const res = await apiClient.get('/api/v1/traffic/overview', {
      params: { window_minutes: windowMinutes },
    });
    const payload = res.data;
    const row = payload?.data || payload;

    if (row && (typeof row.vehicle_count === 'number' || typeof row.distinct_tracks === 'number')) {
      const distinct = row.vehicle_count ?? row.distinct_tracks ?? 524000;
      const speed = row.average_speed ?? row.avg_speed_kmh ?? 38.2;
      const congestion = (row.congestion_level || row.congestion_index || 'high').toLowerCase();

      return {
        window_start: row.window_start || new Date(Date.now() - windowMinutes * 60000).toISOString(),
        window_end: row.window_end || new Date().toISOString(),
        distinct_tracks: distinct,
        estimated_flow_rate_per_hour: Math.round(distinct * (60 / windowMinutes)),
        avg_speed_kmh: Number(speed),
        congestion_index: congestion,
        estimated_co2_kg: Math.round(distinct * 0.272),
        delta_volume_pct: 3.4,
        delta_speed_pct: -5.1,
      };
    }
  } catch (error) {
    console.warn('[ZyroTrace] GET /api/v1/traffic/overview failed. Using fallback overview.', error);
  }
  return MOCK_TRAFFIC_OVERVIEW;
}

export async function fetchSegmentTraffic(
  windowMinutes: number = 60
): Promise<SegmentTraffic[]> {
  try {
    const res = await apiClient.get('/api/v1/traffic/segments', {
      params: { window_minutes: windowMinutes },
    });
    const payload = res.data;
    const items = payload?.data || (Array.isArray(payload) ? payload : null);

    if (Array.isArray(items) && items.length > 0) {
      return items.map((item) => {
        const segId = item.segment_id || item.road_segment_id || 'seg-corridor';
        const fallbackSeg = MOCK_SEGMENTS.find((s) => s.road_segment_id === segId);

        return {
          road_segment_id: segId,
          segment_name: item.segment_name || fallbackSeg?.segment_name || `Corridor Highway ${segId}`,
          total_vehicles: item.vehicle_count ?? item.total_vehicles ?? 18400,
          avg_speed_kmh: Number(item.average_speed ?? item.avg_speed_kmh ?? 45.0),
          congestion_status: (item.congestion_level || item.congestion_status || 'fluid').toLowerCase(),
          cameras: item.cameras || fallbackSeg?.cameras || [],
          coordinates: fallbackSeg?.coordinates || (item.cameras && item.cameras.length >= 2 ? item.cameras.map((c: any) => [c.latitude, c.longitude]) : [[28.74, 77.15], [28.78, 77.13]]),
        };
      });
    }
  } catch (error) {
    console.warn('[ZyroTrace] GET /api/v1/traffic/segments failed. Using fallback segments.', error);
  }
  return MOCK_SEGMENTS;
}

export async function fetchCameraTraffic(
  windowMinutes: number = 60
): Promise<CameraTraffic[]> {
  try {
    const res = await apiClient.get('/api/v1/traffic/cameras', {
      params: { window_minutes: windowMinutes },
    });
    const payload = res.data;
    const items = payload?.data || (Array.isArray(payload) ? payload : null);
    if (Array.isArray(items)) {
      return items.map((c) => ({
        camera_id: c.camera_id || c.id,
        camera_name: c.name || `Node ${c.camera_id}`,
        vehicle_count: c.vehicle_count || 0,
        avg_speed_kmh: c.average_speed || 0,
        congestion_level: c.congestion_level || 'fluid',
      }));
    }
  } catch (error) {
    console.warn('[ZyroTrace] GET /api/v1/traffic/cameras failed.', error);
  }
  return [];
}

export async function fetchTrafficHistory(params?: {
  camera_id?: string;
  segment_id?: string;
  start_time?: string;
  end_time?: string;
  limit?: number;
  offset?: number;
}): Promise<TrafficAggregateRow[]> {
  try {
    const res = await apiClient.get('/api/v1/traffic/history', { params });
    const payload = res.data;
    const items = payload?.data || (Array.isArray(payload) ? payload : null);
    if (Array.isArray(items)) {
      return items;
    }
  } catch (error) {
    console.warn('[ZyroTrace] GET /api/v1/traffic/history failed.', error);
  }
  return [];
}

export async function fetchTrafficAdvisories(): Promise<TrafficAdvisory[]> {
  return MOCK_ADVISORIES;
}
