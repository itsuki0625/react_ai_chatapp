export interface User {
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
    icon: any
    title: string
    value: string
    unit: string
    description: string
  }