"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/common/Button';
import { universityApi, admissionApi } from '@/lib/api-client';

interface UniversityFromAPI {
  id: string;
  name: string;
  departments?: {
    id: string;
    name: string;
  }[];
}

interface AdmissionMethodFromAPI {
  id: string;
  name: string;
  university_id: string;
}

interface ApplicationFormData {
  university_id: string;
  department_id: string;
  admission_method_id: string;
  priority: number;
  notes?: string;
}

interface DesiredSchoolFormProps {
  onSubmit: (data: ApplicationFormData) => void;
  onCancel: () => void;
  initialData?: {
    id?: string;
    university_id: string;
    department_id: string;
    admission_method_id: string;
    priority: number;
    notes?: string;
  };
}

export const DesiredSchoolForm: React.FC<DesiredSchoolFormProps> = ({
  onSubmit,
  onCancel,
  initialData
}) => {
  const [universities, setUniversities] = useState<UniversityFromAPI[]>([]);
  const [admissionMethods, setAdmissionMethods] = useState<AdmissionMethodFromAPI[]>([]);
  const [selectedUniversity, setSelectedUniversity] = useState<string>(
    initialData?.university_id || ''
  );
  const [formData, setFormData] = useState<ApplicationFormData>({
    university_id: initialData?.university_id || '',
    department_id: initialData?.department_id || '',
    admission_method_id: initialData?.admission_method_id || '',
    priority: initialData?.priority || 1,
    notes: initialData?.notes || ''
  });
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError('');
        const [uniResponse, admResponse] = await Promise.all([
          universityApi.getUniversities(),
          admissionApi.getAllAdmissionMethods()
        ]);

        if (uniResponse.data) {
          setUniversities(uniResponse.data as any);
        } else {
          console.error('Failed to fetch universities or data is not in expected format', uniResponse);
        }

        if (admResponse.data) {
          setAdmissionMethods(admResponse.data as any);
        } else {
          console.error('Failed to fetch admission methods or data is not in expected format', admResponse);
        }

      } catch (err: any) {
        console.error('Error fetching initial data:', err);
        let detailedError = '初期データの読み込みに失敗しました。';
        if (err.response?.data?.detail) {
            detailedError += ` ${err.response.data.detail}`;
        } else if (err.message) {
            detailedError += ` ${err.message}`;
        }
        setError(detailedError);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (initialData) {
      setFormData({
        university_id: initialData.university_id,
        department_id: initialData.department_id,
        admission_method_id: initialData.admission_method_id,
        priority: initialData.priority,
        notes: initialData.notes || ''
      });
      setSelectedUniversity(initialData.university_id);
    }
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (name === 'university_id') {
      setSelectedUniversity(value);
      setFormData(prev => ({
        ...prev,
        department_id: ''
      }));
    }
  };

  const priorityOptions = Array.from({ length: 10 }, (_, i) => ({
    value: i + 1,
    label: `第${i + 1}志望`
  }));

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 text-red-700 bg-red-100 rounded-md">
          {error}
        </div>
      )}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">大学</label>
        <select
          name="university_id"
          value={formData.university_id}
          onChange={handleChange}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
          required
        >
          <option value="">選択してください</option>
          {universities.map(univ => (
            <option key={univ.id} value={univ.id}>{univ.name}</option>
          ))}
        </select>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">学部・学科</label>
        <select
          name="department_id"
          value={formData.department_id}
          onChange={handleChange}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
          required
        >
          <option value="">選択してください</option>
          {
            (universities.find(u => u.id === selectedUniversity)?.departments || [])
            .map(dept => (
              <option key={dept.id} value={dept.id}>{dept.name}</option>
            ))
          }
        </select>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">入試方式</label>
        <select
          name="admission_method_id"
          value={formData.admission_method_id}
          onChange={handleChange}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
          required
        >
          <option value="">選択してください</option>
          {admissionMethods.map(method => (
            <option key={method.id} value={method.id}>{method.name}</option>
          ))}
        </select>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">志望順位</label>
        <select
          name="priority"
          value={formData.priority}
          onChange={handleChange}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
          required
        >
          {priorityOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">メモ</label>
        <textarea
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
          rows={4}
        />
      </div>

      <div className="flex justify-end space-x-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          キャンセル
        </Button>
        <Button type="submit" variant="primary">
          {initialData ? '更新する' : '登録する'}
        </Button>
      </div>
    </form>
  );
}; 