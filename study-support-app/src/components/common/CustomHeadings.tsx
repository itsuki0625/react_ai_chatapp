import React, { HTMLAttributes } from 'react';

interface HeadingProps extends HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
}

/**
 * スタイル付きH1見出しコンポーネント
 */
export const StyledH1: React.FC<HeadingProps> = ({ children, className, ...props }) => {
  return (
    <h1 
      className={`text-3xl font-bold text-gray-800 ${className || ''}`}
      {...props}
    >
      {children}
    </h1>
  );
};

/**
 * スタイル付きH2見出しコンポーネント
 */
export const StyledH2: React.FC<HeadingProps> = ({ children, className, ...props }) => {
  return (
    <h2 
      className={`text-2xl font-semibold text-gray-700 ${className || ''}`}
      {...props}
    >
      {children}
    </h2>
  );
}; 