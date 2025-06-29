// API基本URL設定
// クライアント側とサーバー側で異なるURLを使用
export const API_BASE_URL = typeof window !== 'undefined' 
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050') // ブラウザ側では直接バックエンドにアクセス
  : (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:5050');

// デバッグ情報を出力（開発環境のみ）
if (process.env.NODE_ENV !== 'production' && typeof window !== 'undefined') {
  console.log('API接続先設定（ブラウザ）:', API_BASE_URL || 'relative path');
} else if (process.env.NODE_ENV !== 'production') {
  console.log('API接続先設定（サーバー）:', API_BASE_URL);
} 