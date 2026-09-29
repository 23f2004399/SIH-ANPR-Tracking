import { create } from 'zustand';

export interface AppNotification {
  id: string;
  type: 'urgent' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
}

interface UIState {
  activeMode: 'police' | 'traffic' | 'cameras' | 'jobs';
  backendStatus: 'connected' | 'demo';
  isCheckingHealth: boolean;
  notifications: AppNotification[];
  setActiveMode: (mode: 'police' | 'traffic' | 'cameras' | 'jobs') => void;
  setBackendStatus: (status: 'connected' | 'demo') => void;
  addNotification: (notification: Omit<AppNotification, 'id' | 'timestamp'>) => void;
  dismissNotification: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeMode: 'police',
  backendStatus: 'demo',
  isCheckingHealth: false,
  notifications: [
    {
      id: 'notif-init',
      type: 'warning',
      title: 'HOTLIST ACTIVE TELEMETRY',
      message: 'Red Corner Alert vehicle HR 26 CX 9021 sighted near GT Karnal Rd NH-44.',
      timestamp: new Date().toISOString(),
    },
  ],
  setActiveMode: (activeMode) => set({ activeMode }),
  setBackendStatus: (backendStatus) => set({ backendStatus }),
  addNotification: (notif) =>
    set((state) => ({
      notifications: [
        {
          ...notif,
          id: `notif-${Date.now()}-${Math.random()}`,
          timestamp: new Date().toISOString(),
        },
        ...state.notifications.slice(0, 4),
      ],
    })),
  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}));
