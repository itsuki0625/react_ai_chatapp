import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const formatDate = (dateString: string | undefined | null): string => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');
    return new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric', month: 'numeric', day: 'numeric',
      hour: 'numeric', minute: 'numeric', second: 'numeric',
      hour12: false,
      timeZone: 'Asia/Tokyo'
    }).format(date);
  } catch (e) {
    console.error("Date formatting error:", e);
    return dateString;
  }
};
