import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
// import * as React from "react"; // Remove duplicate React import
// import type { ToastActionElement, ToastProps } from "@/components/ui/toast"; // Remove import

// const TOAST_LIMIT = 1; // Remove unused variable
const TOAST_REMOVE_DELAY = 1000000;

type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'destructive';

// Restore local ToastProps definition
type ToastProps = {
  id?: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  variant?: ToastVariant;
  action?: React.ReactNode; // Restore action property if needed by the component
  duration?: number; // Add duration property
};

// --- コンテキストの定義 ---
type ToastContextType = {
  toast: (props: ToastProps) => void; // Use local ToastProps
};

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  const toast = useCallback((props: ToastProps) => {
    const id = String(Date.now());
    const newToast = { ...props, id };

    setToasts((currentToasts) => [
      ...currentToasts,
      newToast,
    ]);

    if (props.duration !== 0) {
      setTimeout(() => {
        setToasts((current) => current.filter((t) => t.id !== id));
      }, props.duration || TOAST_REMOVE_DELAY);
    }
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-0 right-0 p-4 z-50 flex flex-col space-y-2">
        {toasts.map(({ id, title, description, variant = 'default' }) => (
          <Toast
            key={id}
            title={title}
            description={description}
            variant={variant}
            onClose={() => setToasts(current => current.filter(toast => toast.id !== id))}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

interface ToastComponentProps extends ToastProps {
  onClose: () => void;
}

const Toast: React.FC<ToastComponentProps> = ({ title, description, variant = 'default', onClose }) => {
  // バリアントごとのスタイル
  const variantStyles = {
    default: 'bg-white border-gray-200',
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    warning: 'bg-yellow-50 border-yellow-200',
    destructive: 'bg-red-100 border-red-300',
  };

  // タイトルのスタイル
  const titleStyles = {
    default: 'text-gray-900',
    success: 'text-green-800',
    error: 'text-red-800',
    warning: 'text-yellow-800',
    destructive: 'text-red-900',
  };

  // 説明のスタイル
  const descriptionStyles = {
    default: 'text-gray-600',
    success: 'text-green-700',
    error: 'text-red-700',
    warning: 'text-yellow-700',
    destructive: 'text-red-800',
  };

  return (
    <div
      className={`border ${variantStyles[variant]} rounded-lg shadow-md p-4 max-w-md animate-fade-in`}
      role="alert"
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className={`font-medium ${titleStyles[variant]}`}>{title}</h3>
          {description && <p className={`mt-1 text-sm ${descriptionStyles[variant]}`}>{description}</p>}
        </div>
        <button
          onClick={onClose}
          className="ml-4 text-gray-400 hover:text-gray-600"
          aria-label="閉じる"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default Toast; 