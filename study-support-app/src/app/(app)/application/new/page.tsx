"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import { DesiredSchoolForm } from '@/components/application/DesiredSchoolForm';
import { applicationApi } from '@/lib/api-client';
import { toast } from 'react-hot-toast';

// ApplicationFormData is provided by DesiredSchoolForm
// Backend API (ApplicationCreate schema) expects a compatible structure.
interface ApplicationFormData { // This should align with DesiredSchoolForm's output and ApplicationCreate schema
  university_id: string; // FastAPI will handle string to UUID conversion if valid
  department_id: string;
  admission_method_id: string;
  priority: number;
  notes?: string;
}

// The ApplicationData interface that was previously here was a guess and is not needed
// as ApplicationFormData directly matches the backend's ApplicationCreate schema.

export default function CreateApplicationPage() {
  const router = useRouter();

  const handleSubmit = async (formData: ApplicationFormData) => {
    console.log('Form data received, sending to API:', formData);

    try {
      // Directly use formData as it matches the ApplicationCreate schema
      const response = await applicationApi.createApplication(formData);

      if (response.data) { // Check if response.data exists and indicates success
        toast.success('志望校を登録しました。');
        router.push('/application'); // Redirect to the list page
      } else {
        // This case might indicate an issue with the API response structure
        // or a non-standard success/failure indication.
        // Consider what `response.data` would be on failure if not an error.
        console.error('API response did not contain data, assuming failure:', response);
        toast.error('志望校の登録に失敗しました。サーバーからの応答が不正です。');
      }
    } catch (error: any) {
      console.error('志望校の登録エラー:', error);
      let errorMessage = '志望校の登録に失敗しました。';
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail) && error.response.data.detail.length > 0) {
          // Handle FastAPI validation errors (array of objects)
          errorMessage += ' ' + error.response.data.detail.map((d: any) => `${d.loc.join('.')} - ${d.msg}`).join('; ');
        } else if (typeof error.response.data.detail === 'string') {
          // Handle simple string detail messages
          errorMessage += ' ' + error.response.data.detail;
        }
      } else if (error.message) {
        errorMessage += ' ' + error.message;
      }
      toast.error(errorMessage);
    }
  };

  const handleCancel = () => {
    router.push('/application'); // Redirect to the application list page
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">志望校の新規登録</h1>
      <DesiredSchoolForm onSubmit={handleSubmit} onCancel={handleCancel} />
    </div>
  );
} 