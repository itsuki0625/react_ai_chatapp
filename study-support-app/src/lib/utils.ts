import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Tailwindのクラス名をマージするためのユーティリティ関数
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 日付をフォーマットするユーティリティ関数
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

// ステータスに応じたスタイルクラスを返すユーティリティ関数
export function getStatusColor(status: string): string {
  switch (status.toUpperCase()) {
    case 'DRAFT':
      return 'bg-yellow-100 text-yellow-800';
    case 'SUBMITTED':
      return 'bg-blue-100 text-blue-800';
    case 'REVIEWED':
      return 'bg-purple-100 text-purple-800';
    case 'APPROVED':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

// イベントタイプに応じたスタイルクラスを返すユーティリティ関数
export function getEventTypeColor(type: string): string {
  switch (type.toUpperCase()) {
    case 'EXAM':
      return 'bg-red-100 text-red-800';
    case 'INTERVIEW':
      return 'bg-blue-100 text-blue-800';
    case 'SUBMISSION':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

// イベントタイプの日本語表示を返すユーティリティ関数
export function getEventTypeLabel(type: string): string {
  switch (type.toUpperCase()) {
    case 'EXAM':
      return '試験';
    case 'INTERVIEW':
      return '面接';
    case 'SUBMISSION':
      return '書類提出';
    default:
      return 'その他';
  }
}

// 期限切れかどうかをチェックするユーティリティ関数
export function isExpired(date: string | Date): boolean {
  return new Date(date) < new Date();
}

// 期限が近いかどうかをチェックするユーティリティ関数（1週間以内）
export function isUpcoming(date: string | Date): boolean {
  const eventDate = new Date(date);
  const now = new Date();
  const diff = eventDate.getTime() - now.getTime();
  const oneWeek = 7 * 24 * 60 * 60 * 1000;
  return diff > 0 && diff < oneWeek;
}

// エラーメッセージを整形するユーティリティ関数
export function formatError(error: any): string {
  if (typeof error === 'string') return error;
  if (error.response?.data?.detail) return error.response.data.detail;
  if (error.message) return error.message;
  return '予期せぬエラーが発生しました';
}
