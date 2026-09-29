import { create } from 'zustand';
import {
  VehicleTrack,
  VehicleObservation,
  EvidenceAsset,
  SimilarVehicle,
} from '@/types/api';
import {
  searchVehiclesByPlate,
  fetchVehicleHistory,
  fetchVehicleEvidence,
  fetchSimilarVehicles,
} from '@/lib/api/vehicles';

interface VehicleState {
  searchQuery: string;
  isExactMatch: boolean;
  searchResults: VehicleTrack[];
  isSearching: boolean;
  selectedTrack: VehicleTrack | null;
  history: VehicleObservation[];
  evidence: EvidenceAsset[];
  similarVehicles: SimilarVehicle[];
  isLoadingTimeline: boolean;
  selectedObservation: VehicleObservation | null;
  isSimilarModalOpen: boolean;
  hasInitialized: boolean;

  setSearchQuery: (query: string) => void;
  setIsExactMatch: (exact: boolean) => void;
  searchPlates: (overrideQuery?: string) => Promise<void>;
  selectTrack: (track: VehicleTrack) => Promise<void>;
  selectObservation: (obs: VehicleObservation | null) => void;
  fetchSimilar: (trackId: number) => Promise<void>;
  setSimilarModalOpen: (open: boolean) => void;
  clearSelection: () => void;
  initDefaultTrack: (defaultQuery?: string) => Promise<void>;
}

export const useVehicleStore = create<VehicleState>((set, get) => ({
  searchQuery: 'HR 26 CX 9021',
  isExactMatch: false,
  searchResults: [],
  isSearching: false,
  selectedTrack: null,
  history: [],
  evidence: [],
  similarVehicles: [],
  isLoadingTimeline: false,
  selectedObservation: null,
  isSimilarModalOpen: false,
  hasInitialized: false,

  setSearchQuery: (searchQuery) => set({ searchQuery }),
  setIsExactMatch: (isExactMatch) => set({ isExactMatch }),

  searchPlates: async (overrideQuery?: string) => {
    const q = overrideQuery !== undefined ? overrideQuery : get().searchQuery;
    set({ isSearching: true, searchQuery: q });
    try {
      const results = await searchVehiclesByPlate(q, get().isExactMatch);
      set({ searchResults: results, isSearching: false });

      if (results.length > 0) {
        await get().selectTrack(results[0]);
      } else {
        set({
          selectedTrack: null,
          history: [],
          evidence: [],
          selectedObservation: null,
        });
      }
    } catch {
      set({ isSearching: false });
    }
  },

  selectTrack: async (track: VehicleTrack) => {
    set({ selectedTrack: track, isLoadingTimeline: true });
    try {
      const [history, evidence] = await Promise.all([
        fetchVehicleHistory(track.id),
        fetchVehicleEvidence(track.id),
      ]);

      set({
        history,
        evidence,
        selectedObservation: history.length > 0 ? history[history.length - 1] : null,
        isLoadingTimeline: false,
      });

      // Fetch vector similarity matches via API
      get().fetchSimilar(track.id);
    } catch {
      set({ isLoadingTimeline: false });
    }
  },

  selectObservation: (obs) => set({ selectedObservation: obs }),

  fetchSimilar: async (trackId: number) => {
    try {
      const similar = await fetchSimilarVehicles(trackId, 10);
      set({ similarVehicles: similar });
    } catch {
      set({ similarVehicles: [] });
    }
  },

  setSimilarModalOpen: (isSimilarModalOpen) => set({ isSimilarModalOpen }),

  clearSelection: () =>
    set({
      selectedTrack: null,
      history: [],
      evidence: [],
      similarVehicles: [],
      selectedObservation: null,
      searchQuery: '',
      searchResults: [],
    }),

  initDefaultTrack: async (defaultQuery = 'HR 26 CX 9021') => {
    if (get().hasInitialized) return;
    set({ hasInitialized: true });
    await get().searchPlates(defaultQuery);
  },
}));
