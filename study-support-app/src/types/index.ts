import React from 'react';

export interface UserProfile {
    id: string
    name: string
    email: string
    avatar?: string
}
  
export interface Activity {
    id: number
    title: string
    timestamp: string
}
  
export interface NextAction {
    id: number
    title: string
    description: string
}
  
export interface Stat {
    icon: React.ReactNode | React.ElementType
    title: string
    value: string
    unit: string
    description: string
}