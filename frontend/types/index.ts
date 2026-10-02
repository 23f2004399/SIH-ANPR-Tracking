export interface Camera {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  rtsp_url?: string;
  road_segment_id?: string;
  is_active?: boolean;
}

export interface TrafficMetrics {
  flow_rate?: number;
  congestion_index?: number;
  average_speed?: number;
  vehicle_count?: number;
  classification_counts?: Record<string, number>;
  [key: string]: any;
}

export interface TrafficAggregate {
  id?: string;
  camera_id?: string;
  road_segment_id?: string;
  window_start?: string;
  window_end?: string;
  metrics?: TrafficMetrics;
  name?: string;
  cameras?: Array<{
    id: string;
    name: string;
    latitude: number;
    longitude: number;
  }>;
}

export interface VehicleTrack {
  id: number;
  first_seen_at: string;
  last_seen_at?: string;
  vehicle_type?: string;
  color?: string;
  license_plate?: string;
  normalized_text?: string;
  [key: string]: any;
}

export interface VehicleObservation {
  id?: number;
  track_id: number;
  camera_id: string;
  observed_at: string;
  normalized_text?: string;
  confidence?: number;
  camera_name?: string;
  latitude?: number;
  longitude?: number;
  speed?: string;
}

export interface EvidenceAsset {
  id: number;
  track_id: number;
  timestamp: string;
  asset_type?: string;
  url?: string;
  crop_url?: string;
  confidence?: number;
}

export interface SimilarVehicle {
  track_id: number;
  similarity: number;
  license_plate?: string;
  first_seen_at?: string;
  vehicle_type?: string;
  color?: string;
}

// UI Models
export type AppMode = 'police' | 'urban';
export type SearchTab = 'plate' | 'image';
export type TimestampMode = 'live' | 'range';
export type PoliceViewMode = 'empty' | 'grid' | 'map' | 'live';

export interface AlertNotification {
  kind: string;
  plate: string;
  time: string;
  detail: string;
  c: string;
}

export interface RoutePoint {
  n: number;
  cam: string;
  street: string;
  time: string;
  speed: string;
  conf: string;
  geo: string;
  x: number;
  y: number;
}

export interface SightingItem {
  id?: number;
  track_id?: number;
  cam: string;
  street: string;
  geo: string;
  time: string;
  conf: string;
  reid: boolean;
  plateTag: string;
  vehicle_type?: string;
  best_crop_key?: string;
  plate_crop_key?: string;
}

export interface UrbanStat {
  label: string;
  value: string;
  delta: string;
  note: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
}

export interface Corridor {
  name: string;
  transit: string;
  tag: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
}

export interface CorridorMix {
  name: string;
  total: string;
  p: [number, number, number, number];
}

export interface FleetItem {
  name: string;
  pct: string;
  c: string;
}

export interface EmissionItem {
  name: string;
  tons: string;
  w: number;
  c: string;
}

export interface SuggestionItem {
  text: string;
  impact: string;
  scope: string;
}

export interface CityTrafficAnalytics {
  stats: UrbanStat[];
  corridors: Corridor[];
  corridor_mix: CorridorMix[];
  fleet: FleetItem[];
  emissions: EmissionItem[];
  suggestions: SuggestionItem[];
  total_vehicles_formatted: string;
  total_idle_hours_formatted: string;
  total_co2_formatted: string;
  node_count: number;
}

