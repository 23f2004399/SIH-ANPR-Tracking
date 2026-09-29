import { create } from 'zustand';
import {
  TrafficOverview,
  SegmentTraffic,
  TrafficAdvisory,
} from '@/types/api';
import {
  fetchTrafficOverview,
  fetchSegmentTraffic,
  fetchTrafficAdvisories,
} from '@/lib/api/traffic';

interface TrafficState {
  windowMinutes: number;
  overview: TrafficOverview | null;
  segments: SegmentTraffic[];
  selectedSegmentId: string | null;
  advisories: TrafficAdvisory[];
  isLoading: boolean;
  hasLoaded: boolean;

  setWindowMinutes: (minutes: number) => void;
  fetchTrafficData: () => Promise<void>;
  selectSegment: (segmentId: string | null) => void;
}

export const useTrafficStore = create<TrafficState>((set, get) => ({
  windowMinutes: 60,
  overview: null,
  segments: [],
  selectedSegmentId: null,
  advisories: [],
  isLoading: false,
  hasLoaded: false,

  setWindowMinutes: (windowMinutes) => {
    set({ windowMinutes });
    get().fetchTrafficData();
  },

  fetchTrafficData: async () => {
    set({ isLoading: true });
    try {
      const [overview, segments, advisories] = await Promise.all([
        fetchTrafficOverview(get().windowMinutes),
        fetchSegmentTraffic(get().windowMinutes),
        fetchTrafficAdvisories(),
      ]);
      set({
        overview,
        segments,
        selectedSegmentId: segments.length > 0 ? (get().selectedSegmentId || segments[0].road_segment_id) : null,
        advisories,
        isLoading: false,
        hasLoaded: true,
      });
    } catch {
      set({ isLoading: false, hasLoaded: true });
    }
  },

  selectSegment: (selectedSegmentId) => set({ selectedSegmentId }),
}));
