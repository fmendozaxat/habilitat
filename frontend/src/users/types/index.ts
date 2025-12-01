import type { UserRole } from '@/core/types';

export interface CreateUserData {
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
}

export interface UpdateUserData {
  first_name?: string;
  last_name?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface InviteUserData {
  email: string;
  role: UserRole;
  flow_ids?: number[];
}

export interface UserFilters {
  search?: string;
  role?: UserRole;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}
