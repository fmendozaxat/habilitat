/**
 * Core type definitions
 */

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  items?: T[];  // Alias for compatibility
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// User types
export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  tenant_id: number;
  created_at: string;
  updated_at: string;
  last_login?: string;
  profile_image_url?: string;
}

export type UserRole = 'super_admin' | 'tenant_admin' | 'employee';

// Tenant types
export interface Tenant {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  branding?: TenantBranding;
}

export interface TenantBranding {
  id: number;
  tenant_id: number;
  logo_url?: string;
  favicon_url?: string;
  primary_color: string;
  secondary_color: string;
  font_family?: string;
  custom_css?: string;
}

// Auth types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  tenant_slug?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  tenant: Tenant | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Onboarding types
export interface OnboardingFlow {
  id: number;
  tenant_id: number;
  name: string;
  description?: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  modules?: OnboardingModule[];
}

export interface OnboardingModule {
  id: number;
  flow_id: number;
  title: string;
  description?: string;
  module_type: ModuleType;
  content_data: Record<string, unknown>;
  order_index: number;
  is_required: boolean;
  estimated_duration_minutes?: number;
  created_at: string;
  updated_at: string;
}

export type ModuleType = 'text' | 'video' | 'document' | 'quiz' | 'link';

export interface OnboardingAssignment {
  id: number;
  user_id: number;
  flow_id: number;
  status: OnboardingStatus;
  assigned_at: string;
  started_at?: string;
  completed_at?: string;
  due_date?: string;
  progress_percentage: number;
  flow?: OnboardingFlow;
  user?: User;
}

export type OnboardingStatus = 'not_started' | 'in_progress' | 'completed';

export interface ModuleProgress {
  id: number;
  assignment_id: number;
  module_id: number;
  status: OnboardingStatus;
  started_at?: string;
  completed_at?: string;
  time_spent_seconds: number;
  quiz_score?: number;
  quiz_attempts?: number;
}

// Content types
export interface Content {
  id: number;
  tenant_id: number;
  title: string;
  description?: string;
  content_type: ModuleType;
  content_data: Record<string, unknown>;
  is_published: boolean;
  tags: string[];
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

// Notification types
export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  notification_type: NotificationType;
  is_read: boolean;
  action_url?: string;
  created_at: string;
}

export type NotificationType = 'info' | 'success' | 'warning' | 'error' | 'assignment' | 'reminder';

// Analytics types
export interface DashboardStats {
  total_users: number;
  active_users: number;
  total_flows: number;
  active_assignments: number;
  completion_rate: number;
  average_completion_time_days: number;
}

export interface OnboardingAnalytics {
  total_assignments: number;
  completed: number;
  in_progress: number;
  not_started: number;
  overdue: number;
  completion_rate: number;
  average_time_to_complete_days: number;
}

// Form types
export interface SelectOption {
  value: string | number;
  label: string;
}

// Table types
export interface TableColumn<T> {
  key: keyof T | string;
  header: string;
  render?: (item: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

export interface PaginationConfig {
  page: number;
  pageSize: number;
  total: number;
}
