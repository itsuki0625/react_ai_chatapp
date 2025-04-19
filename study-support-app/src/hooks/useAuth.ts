import { useState, useEffect } from 'react';
import axios from 'axios';
import { User } from '@/types/auth';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await axios.get<User>(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/me`, {
          withCredentials: true
        });
        setUser(response.data as User);
      } catch (err) {
        if (axios.isAxiosError(err) && err.response?.status === 401) {
          setUser(null);
        } else {
          console.error('認証エラー:', err);
          setError(err instanceof Error ? err : new Error('認証エラーが発生しました'));
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, []);

  return { user, isLoading, error };
} 