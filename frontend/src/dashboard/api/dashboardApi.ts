import { api } from '@/core/api';
import type { DashboardStats, OnboardingAnalytics } from '@/core/types';

export const dashboardApi = {
  getStats: () =>
    api.get<DashboardStats>('/analytics/dashboard'),

  getOnboardingAnalytics: () =>
    api.get<OnboardingAnalytics>('/analytics/onboarding'),

  getRecentActivity: () =>
    api.get<{
      recent_completions: Array<{
        user_name: string;
        flow_name: string;
        completed_at: string;
      }>;
      upcoming_deadlines: Array<{
        user_name: string;
        flow_name: string;
        due_date: string;
      }>;
    }>('/analytics/activity'),
};
