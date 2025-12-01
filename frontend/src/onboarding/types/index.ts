import type { ModuleType } from '@/core/types';

export interface CreateFlowData {
  name: string;
  description?: string;
  is_active?: boolean;
  is_default?: boolean;
}

export interface UpdateFlowData {
  name?: string;
  description?: string;
  is_active?: boolean;
  is_default?: boolean;
}

export interface CreateModuleData {
  flow_id: number;
  title: string;
  description?: string;
  module_type: ModuleType;
  content_data: Record<string, unknown>;
  order_index: number;
  is_required?: boolean;
  estimated_duration_minutes?: number;
}

export interface UpdateModuleData {
  title?: string;
  description?: string;
  content_data?: Record<string, unknown>;
  order_index?: number;
  is_required?: boolean;
  estimated_duration_minutes?: number;
}

export interface CreateAssignmentData {
  user_id: number;
  flow_id: number;
  due_date?: string;
}

export interface FlowFilters {
  search?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface AssignmentFilters {
  status?: string;
  flow_id?: number;
  user_id?: number;
  page?: number;
  page_size?: number;
}
