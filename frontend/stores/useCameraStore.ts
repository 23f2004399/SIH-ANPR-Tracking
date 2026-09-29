import { create } from 'zustand';
import { Camera, CameraIn } from '@/types/api';
import { fetchCameras, createCamera } from '@/lib/api/cameras';

interface CameraState {
  cameras: Camera[];
  selectedCamera: Camera | null;
  searchFilter: string;
  segmentFilter: string | null;
  isLoading: boolean;
  hasLoaded: boolean;

  fetchCamerasList: () => Promise<void>;
  selectCamera: (camera: Camera | null) => void;
  setSearchFilter: (filter: string) => void;
  setSegmentFilter: (segmentId: string | null) => void;
  addCameraNode: (cameraIn: CameraIn) => Promise<Camera>;
}

export const useCameraStore = create<CameraState>((set, get) => ({
  cameras: [],
  selectedCamera: null,
  searchFilter: '',
  segmentFilter: null,
  isLoading: false,
  hasLoaded: false,

  fetchCamerasList: async () => {
    set({ isLoading: true });
    try {
      const cameras = await fetchCameras();
      set({
        cameras,
        selectedCamera: cameras.length > 0 ? (get().selectedCamera || cameras[0]) : null,
        isLoading: false,
        hasLoaded: true,
      });
    } catch {
      set({ isLoading: false, hasLoaded: true });
    }
  },

  selectCamera: (selectedCamera) => set({ selectedCamera }),
  setSearchFilter: (searchFilter) => set({ searchFilter }),
  setSegmentFilter: (segmentFilter) => set({ segmentFilter }),

  addCameraNode: async (cameraIn: CameraIn) => {
    set({ isLoading: true });
    try {
      const created = await createCamera(cameraIn);
      set((state) => ({
        cameras: [created, ...state.cameras.filter((c) => c.id !== created.id)],
        selectedCamera: created,
        isLoading: false,
      }));
      return created;
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },
}));
