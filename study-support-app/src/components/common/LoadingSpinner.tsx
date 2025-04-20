import React from 'react';

interface LoadingSpinnerProps {
  className?: string;
}

/**
 * ローディングスピナーコンポーネント
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ className = '' }) => {
  return (
    <div
      className={`animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500 ${className}`}
      role="status"
      aria-label="読み込み中"
    />
  );
};

export default LoadingSpinner; 