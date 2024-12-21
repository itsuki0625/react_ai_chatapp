import React from 'react';

interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ label, onClick, disabled = false }) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        px-4 
        py-2 
        rounded-lg 
        font-medium 
        transition-colors 
        ${
          disabled
            ? 'bg-gray-300 cursor-not-allowed'
            : 'bg-blue-500 hover:bg-blue-600 text-white cursor-pointer'
        }
      `}
    >
      {label}
    </button>
  );
};

export default Button;
