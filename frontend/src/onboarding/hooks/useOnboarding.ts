import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/core/components/ui/Toast';
import { onboardingApi } from '../api/onboardingApi';
import type {
  FlowFilters,
  CreateFlowData,
  UpdateFlowData,
  CreateModuleData,
  UpdateModuleData,
  CreateAssignmentData,
} from '../types';

// Flows
export function useFlows(filters?: FlowFilters) {
  return useQuery({
    queryKey: ['flows', filters],
    queryFn: () => onboardingApi.getFlows(filters),
  });
}

export function useFlow(id: number) {
  return useQuery({
    queryKey: ['flows', id],
    queryFn: () => onboardingApi.getFlow(id),
    enabled: !!id,
  });
}

export function useCreateFlow() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (data: CreateFlowData) => onboardingApi.createFlow(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flows'] });
      success('Flujo creado', 'El flujo de onboarding ha sido creado');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useUpdateFlow() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateFlowData }) =>
      onboardingApi.updateFlow(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flows'] });
      success('Flujo actualizado', 'El flujo ha sido actualizado');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useDeleteFlow() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (id: number) => onboardingApi.deleteFlow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flows'] });
      success('Flujo eliminado', 'El flujo ha sido eliminado');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

// Modules
export function useModules(flowId: number) {
  return useQuery({
    queryKey: ['modules', flowId],
    queryFn: () => onboardingApi.getModules(flowId),
    enabled: !!flowId,
  });
}

export function useCreateModule() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (data: CreateModuleData) => onboardingApi.createModule(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['modules', variables.flow_id] });
      queryClient.invalidateQueries({ queryKey: ['flows'] });
      success('Módulo creado', 'El módulo ha sido creado');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useUpdateModule() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateModuleData }) =>
      onboardingApi.updateModule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modules'] });
      queryClient.invalidateQueries({ queryKey: ['flows'] });
      success('Módulo actualizado', 'El módulo ha sido actualizado');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

export function useDeleteModule() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (id: number) => onboardingApi.deleteModule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modules'] });
      queryClient.invalidateQueries({ queryKey: ['flows'] });
      success('Módulo eliminado', 'El módulo ha sido eliminado');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

// Assignments
export function useCreateAssignment() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (data: CreateAssignmentData) => onboardingApi.createAssignment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
      success('Asignación creada', 'El usuario ha sido asignado al flujo');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}

// My Onboarding
export function useMyAssignments() {
  return useQuery({
    queryKey: ['my-assignments'],
    queryFn: onboardingApi.getMyAssignments,
  });
}

export function useMyAssignment(id: number) {
  return useQuery({
    queryKey: ['my-assignments', id],
    queryFn: () => onboardingApi.getMyAssignment(id),
    enabled: !!id,
  });
}

export function useModuleProgress(assignmentId: number) {
  return useQuery({
    queryKey: ['module-progress', assignmentId],
    queryFn: () => onboardingApi.getModuleProgress(assignmentId),
    enabled: !!assignmentId,
  });
}

export function useCompleteModule() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: ({
      assignmentId,
      moduleId,
      data,
    }: {
      assignmentId: number;
      moduleId: number;
      data?: Record<string, unknown>;
    }) => onboardingApi.completeModule(assignmentId, moduleId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['module-progress', variables.assignmentId] });
      queryClient.invalidateQueries({ queryKey: ['my-assignments'] });
      success('Módulo completado', 'Has completado este módulo');
    },
    onError: (err: Error) => {
      error('Error', err.message);
    },
  });
}
