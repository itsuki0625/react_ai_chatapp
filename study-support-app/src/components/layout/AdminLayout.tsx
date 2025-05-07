import React from 'react';
import { AdminNavBar } from '@/components/common/AdminNavBar'; // Assuming AdminNavBar exists

interface AdminLayoutProps {
  children: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col">
      <AdminNavBar />
      <main className="flex-grow p-6 bg-gray-50">
        {children}
      </main>
      {/* Optional Footer can be added here */}
    </div>
  );
}; 