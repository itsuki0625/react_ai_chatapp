import { API_BASE_URL } from '@/lib/config';
import { fetchWithAuth } from '@/lib/fetchWithAuth';

export interface University {
  id: string;
  name: string;
  departments: Department[];
  prefecture: string;
  address?: string;
  website_url?: string;
  description?: string;
  is_national: boolean;
  logo_url?: string;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  name: string;
  faculty_name: string;
  university_id: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface DesiredSchool {
  id: string;
  user_id: string;
  university_id: string;
  preference_order: number;
  university?: University;
  desired_departments: DesiredDepartment[];
  created_at: string;
  updated_at: string;
}

export interface DesiredDepartment {
  id: string;
  desired_school_id: string;
  department_id: string;
  admission_method_id: string;
  department?: Department;
  admission_method?: AdmissionMethod;
  created_at: string;
  updated_at: string;
}

export interface AdmissionMethod {
  id: string;
  name: string;
  description?: string;
  category: string;
  university_id: string;
  created_at: string;
  updated_at: string;
}

// 大学一覧を取得
export const getUniversities = async (): Promise<University[]> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/universities/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    throw new Error(`Failed to fetch universities: ${response.status}`);
  }

  return response.json();
};

// 志望大学一覧を取得
export const getDesiredSchools = async (): Promise<DesiredSchool[]> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/desired-schools/me`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    throw new Error(`Failed to fetch desired schools: ${response.status}`);
  }

  const data = await response.json();
  // DesiredSchoolListResponseの場合はdesired_schoolsを返す
  return data.desired_schools || data;
}; 