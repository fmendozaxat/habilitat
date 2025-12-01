import { api } from '@/core/api';
import type {
  OnboardingFlow,
  OnboardingModule,
  OnboardingAssignment,
  ModuleProgress,
  PaginatedResponse,
} from '@/core/types';
import type {
  CreateFlowData,
  UpdateFlowData,
  CreateModuleData,
  UpdateModuleData,
  CreateAssignmentData,
  FlowFilters,
  AssignmentFilters,
} from '../types';

export const onboardingApi = {
  // Flows
  getFlows: (filters?: FlowFilters) =>
    api.get<PaginatedResponse<OnboardingFlow>>('/onboarding/flows', filters as Record<string, unknown>),

  getFlow: (id: number) =>
    api.get<OnboardingFlow>(`/onboarding/flows/${id}`),

  createFlow: (data: CreateFlowData) =>
    api.post<OnboardingFlow>('/onboarding/flows', data),

  updateFlow: (id: number, data: UpdateFlowData) =>
    api.patch<OnboardingFlow>(`/onboarding/flows/${id}`, data),

  deleteFlow: (id: number) =>
    api.delete(`/onboarding/flows/${id}`),

  duplicateFlow: (id: number) =>
    api.post<OnboardingFlow>(`/onboarding/flows/${id}/duplicate`),

  // Modules
  getModules: (flowId: number) =>
    api.get<OnboardingModule[]>(`/onboarding/flows/${flowId}/modules`),

  createModule: (data: CreateModuleData) =>
    api.post<OnboardingModule>('/onboarding/modules', data),

  updateModule: (id: number, data: UpdateModuleData) =>
    api.patch<OnboardingModule>(`/onboarding/modules/${id}`, data),

  deleteModule: (id: number) =>
    api.delete(`/onboarding/modules/${id}`),

  reorderModules: (flowId: number, moduleIds: number[]) =>
    api.post(`/onboarding/flows/${flowId}/reorder`, { module_ids: moduleIds }),

  // Assignments
  getAssignments: (filters?: AssignmentFilters) =>
    api.get<PaginatedResponse<OnboardingAssignment>>('/onboarding/assignments', filters as Record<string, unknown>),

  getAssignment: (id: number) =>
    api.get<OnboardingAssignment>(`/onboarding/assignments/${id}`),

  createAssignment: (data: CreateAssignmentData) =>
    api.post<OnboardingAssignment>('/onboarding/assignments', data),

  deleteAssignment: (id: number) =>
    api.delete(`/onboarding/assignments/${id}`),

  bulkAssign: (flowId: number, userIds: number[], dueDate?: string) =>
    api.post('/onboarding/assignments/bulk', {
      flow_id: flowId,
      user_ids: userIds,
      due_date: dueDate,
    }),

  // My Onboarding (Employee)
  getMyAssignments: () =>
    api.get<OnboardingAssignment[]>('/onboarding/my-assignments'),

  getMyAssignment: (id: number) =>
    api.get<OnboardingAssignment>(`/onboarding/my-assignments/${id}`),

  startAssignment: (id: number) =>
    api.post<OnboardingAssignment>(`/onboarding/assignments/${id}/start`),

  // Module Progress
  getModuleProgress: (assignmentId: number) =>
    api.get<ModuleProgress[]>(`/onboarding/assignments/${assignmentId}/progress`),

  startModule: (assignmentId: number, moduleId: number) =>
    api.post<ModuleProgress>(`/onboarding/assignments/${assignmentId}/modules/${moduleId}/start`),

  completeModule: (assignmentId: number, moduleId: number, data?: Record<string, unknown>) =>
    api.post<ModuleProgress>(`/onboarding/assignments/${assignmentId}/modules/${moduleId}/complete`, data),

  updateModuleProgress: (assignmentId: number, moduleId: number, timeSpent: number) =>
    api.patch<ModuleProgress>(`/onboarding/assignments/${assignmentId}/modules/${moduleId}/progress`, {
      time_spent_seconds: timeSpent,
    }),
};
