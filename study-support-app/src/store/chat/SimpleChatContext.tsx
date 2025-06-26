'use client';

import React, { createContext, useContext, ReactNode } from 'react';

interface SimpleChatContextType {
  test: string;
}

const SimpleChatContext = createContext<SimpleChatContextType | undefined>(undefined);

export const SimpleChatProvider = ({ children }: { children: ReactNode }) => {
  const contextValue = {
    test: 'working'
  };

  return (
    <SimpleChatContext.Provider value={contextValue}>
      {children}
    </SimpleChatContext.Provider>
  );
};

export const useSimpleChat = () => {
  const context = useContext(SimpleChatContext);
  if (context === undefined) {
    throw new Error('useSimpleChat must be used within a SimpleChatProvider');
  }
  return context;
}; 