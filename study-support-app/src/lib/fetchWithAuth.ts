import { getSession } from 'next-auth/react'; // Assuming you use NextAuth.js

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
  init?: RequestInit
): Promise<Response> => {
  const session = await getSession(); // Get the current session

  // Try to access accessToken property safely
  const sessionWithToken = session as SessionWithToken | null;
  const accessToken = sessionWithToken?.accessToken || sessionWithToken?.user?.accessToken;

  if (!session || !accessToken) {
    // Handle cases where the user is not authenticated or token is missing
    console.error('fetchWithAuth: No session or access token found.');
    // Option 1: Throw an error to stop the request
    // throw new Error('Authentication required.');

    // Option 2: Proceed without Authorization header (if some APIs allow it)
    // It's generally safer to require authentication for backend interaction
    console.warn('fetchWithAuth: No session or access token found. Making request without Authorization header.');
    // Depending on backend setup, this might fail or return limited data.
    // If authentication is always required, throwing an error is better.
    // return fetch(input, init);
    // For now, let's throw an error as backend likely requires auth for POST/PUT/DELETE
     throw new Error('Authentication token is missing.');
  }

  // Initialize headers, preserving existing ones
  const headers = new Headers(init?.headers);

  // Add the Authorization header
  headers.set('Authorization', `Bearer ${accessToken}`);

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

      // Optional: Handle 401 Unauthorized globally (e.g., redirect to login)
      if (response.status === 401) {
        console.error('fetchWithAuth: Received 401 Unauthorized. Session might be expired or invalid.');
        // Consider triggering sign-out or redirect
        // import { signOut } from 'next-auth/react';
        // await signOut({ callbackUrl: '/login' });
        // Throw a specific error to be caught by React Query's onError
        throw new Error('Unauthorized (401)');
      }

      return response;
  } catch (error) {
      console.error('fetchWithAuth: Network or other fetch error:', error);
      // Re-throw the error so it can be caught by the calling function / React Query
      throw error;
  }
}; 