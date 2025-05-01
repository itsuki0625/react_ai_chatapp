import { getSession, signOut } from 'next-auth/react';
// import { useRouter } from 'next/navigation'; // useRouter はここでは使わない

// --- 401 Retry Logic --- //
let isRefreshing = false;
let failedQueue: ((token: string | null) => void)[] = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom(null); // エラー時は null を渡して reject させる
    } else {
      prom(token);
    }
  });
  failedQueue = [];
};

async function refreshToken() {
  try {
    // 環境変数からAPIベースURLを取得
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '';
    if (!baseUrl) {
      throw new Error('API base URL is not configured.');
    }

    // リフレッシュAPIを叩く
    const response = await fetch(`${baseUrl}/api/v1/auth/refresh-token`, {
      method: 'POST',
      // Credentials Provider を使っているので Cookie は不要なはずだが、念のため include
      // NextAuth が HttpOnly Cookie で Refresh Token を管理している前提
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      // ボディはバックエンドの仕様に合わせる（ここでは空を想定）
      // もしリフレッシュトークンをボディで送る仕様なら修正が必要
      // body: JSON.stringify({ refresh_token: currentRefreshToken }), // 必要なら
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("refreshToken: Failed to refresh token", { status: response.status, detail: errorData?.detail });
        throw new Error(errorData?.detail || 'Failed to refresh token');
    }

    // リフレッシュ成功後、新しいセッション（=新しいアクセストークンを含む）を取得
    // getSession() は内部で jwt コールバックをトリガーし、新しいトークンを返すはず
    const newSession = await getSession();
    // Fix: Cast to unknown first to resolve TS error
    const newAccessToken = ((newSession as unknown) as SessionWithToken)?.accessToken || ((newSession as unknown) as SessionWithToken)?.user?.accessToken;

    if (!newAccessToken) {
        console.error("refreshToken: New access token not found after refresh.");
        throw new Error('Could not get new access token after refresh');
    }
    console.info("refreshToken: Token refreshed successfully.");
    return newAccessToken;
  } catch (error) {
    console.error("refreshToken: Error during token refresh:", error);
    // リフレッシュ失敗時は null を返す
    return null;
  }
}
// --- End 401 Retry Logic --- //

// 型定義を追加
interface SessionWithToken {
  accessToken?: string;
  user?: {
    accessToken?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

/**
 * A wrapper around the native fetch function that automatically adds
 * the Authorization header with the JWT access token obtained from the
 * NextAuth.js session.
 *
 * @param input The resource that you wish to fetch. This can be either a string or a URL object.
 * @param init An object containing any custom settings that you want to apply to the request.
 * @returns A Promise that resolves to the Response to that request.
 * @throws An error if the session or access token cannot be retrieved.
 */
export const fetchWithAuth = async (
  input: RequestInfo | URL,
  init?: RequestInit,
  isRetry = false // ★ リトライフラグを追加
): Promise<Response> => {
  // const router = useRouter();

  const session = await getSession(); // Get the current session

  // Try to access accessToken property safely
  const sessionWithToken = session as SessionWithToken | null;
  const accessToken = sessionWithToken?.accessToken || sessionWithToken?.user?.accessToken;

  // ★ リトライでない初回リクエスト時にトークンがない場合のみエラー
  if (!isRetry && (!session || !accessToken)) {
    console.error('fetchWithAuth: No session or access token found on initial request.');
    throw new Error('Authentication required.');
  }

  // Initialize headers, preserving existing ones
  const headers = new Headers(init?.headers);

  // Add the Authorization header if token exists
  // ★ リトライ時など、リフレッシュ直後でトークンがない場合を考慮
  if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`);
  } else if (!isRetry) {
      // 初回リクエストでトークンがないのは上の if で捕捉されるはずだが念のため
      console.warn('fetchWithAuth: Access token is missing, request might fail.');
  }

  // Ensure Content-Type is set for methods that typically have a body,
  // if not already provided.
  if (init?.body && !headers.has('Content-Type')) {
    // Default to application/json if body is a string, adjust if necessary
    if (typeof init.body === 'string') {
      headers.set('Content-Type', 'application/json');
    }
    // Note: If body is FormData, fetch sets Content-Type automatically.
    // If body is URLSearchParams, Content-Type should be 'application/x-www-form-urlencoded'.
  }

  // Perform the fetch request with the modified headers
  try {
    const response = await fetch(input, {
      ...init,
      headers,
    });

    // Handle 401 Unauthorized globally with retry logic
    if (response.status === 401 && !isRetry) {
      console.warn('fetchWithAuth: Received 401 Unauthorized. Attempting token refresh...');

      if (isRefreshing) {
        // 他のリクエストがリフレッシュ中の場合、キューに追加して待機
        return new Promise((resolve, reject) => {
          failedQueue.push((newAccessToken: string | null) => {
            if (newAccessToken) {
              console.debug('fetchWithAuth: Token refreshed by another request, retrying with new token.');
              // 新しいトークンでリクエストを再試行
              const retryHeaders = new Headers(init?.headers);
              retryHeaders.set('Authorization', `Bearer ${newAccessToken}`);
              fetch(input, { ...init, headers: retryHeaders })
                .then(resolve)
                .catch(reject);
            } else {
              // リフレッシュに失敗した場合は signout してエラーを reject
              console.error('fetchWithAuth: Token refresh failed by another request. Signing out.');
              signOut();
              reject(new Error('Token refresh failed and signed out.'));
            }
          });
        });
      } else {
        // 最初の 401 リクエストがリフレッシュ処理を開始
        isRefreshing = true;
        const newAccessToken = await refreshToken();
        isRefreshing = false;

        if (newAccessToken) {
          console.info('fetchWithAuth: Token refreshed successfully. Retrying original request.');
          // キュー内の待機中リクエストを処理
          processQueue(null, newAccessToken);
          // 元のリクエストを新しいトークンで再試行
          const retryHeaders = new Headers(init?.headers);
          retryHeaders.set('Authorization', `Bearer ${newAccessToken}`);
          return fetch(input, { ...init, headers: retryHeaders }); // ★ return する
        } else {
          console.error('fetchWithAuth: Token refresh failed. Signing out.');
          // キュー内の待機中リクエストに失敗を通知
          processQueue(new Error('Token refresh failed'));
          signOut();
          // ★ エラーをスローするか、特定のレスポンスを返すか検討
          // ここではエラーをスローする
          throw new Error('Failed to refresh token and signed out.');
        }
      }
    }

    // 401 以外のレスポンス、またはリトライ成功時のレスポンス
    return response;

  } catch (error) {
    console.error('fetchWithAuth: Fetch error:', error);
    // Re-throw the error so it can be caught by the calling function
    throw error;
  }
}; 