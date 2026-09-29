import { create } from 'zustand';
import { Job, JobIn } from '@/types/api';
import { fetchJobs, createJob } from '@/lib/api/jobs';

interface JobState {
  jobs: Job[];
  isLoading: boolean;
  hasLoaded: boolean;
  fetchJobsList: () => Promise<void>;
  submitJob: (jobIn: JobIn) => Promise<Job>;
}

export const useJobStore = create<JobState>((set) => ({
  jobs: [],
  isLoading: false,
  hasLoaded: false,

  fetchJobsList: async () => {
    set({ isLoading: true });
    try {
      const jobs = await fetchJobs();
      set({ jobs, isLoading: false, hasLoaded: true });
    } catch {
      set({ isLoading: false, hasLoaded: true });
    }
  },

  submitJob: async (jobIn: JobIn) => {
    set({ isLoading: true });
    try {
      const job = await createJob(jobIn);
      set((state) => ({
        jobs: [job, ...state.jobs],
        isLoading: false,
      }));
      return job;
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },
}));
