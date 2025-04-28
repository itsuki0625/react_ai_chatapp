import { fetchWithAuth } from '@/lib/fetchWithAuth';
import { ChatSession, ChatMessage } from '@/types/chat'; // Ensure types are correctly defined and imported

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';
const CHAT_API_URL = `${API_BASE_URL}/api/v1/chat`;

/**
 * Fetches active chat sessions.
 * @param sessionType Type of session (e.g., "CONSULTATION")
 * @returns Promise<ChatSession[]>
 */
export const getChatSessions = async (sessionType: string = "CONSULTATION"): Promise<ChatSession[]> => {
    const url = `${CHAT_API_URL}/sessions?session_type=${encodeURIComponent(sessionType)}`;
    console.log(`[ChatService] Fetching active sessions from: ${url}`);
    try {
        const response = await fetchWithAuth(url);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch active chat sessions' }));
            throw new Error(errorData.detail || `HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("[ChatService] Error in getChatSessions:", error);
        throw error; // Re-throw the error for React Query to handle
    }
};

/**
 * Fetches archived chat sessions.
 * @param sessionType Type of session
 * @returns Promise<ChatSession[]>
 */
export const getArchivedChatSessions = async (sessionType: string = "CONSULTATION"): Promise<ChatSession[]> => {
    const url = `${CHAT_API_URL}/sessions/archived?session_type=${encodeURIComponent(sessionType)}`;
    console.log(`[ChatService] Fetching archived sessions from: ${url}`);
    try {
        const response = await fetchWithAuth(url);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch archived chat sessions' }));
            throw new Error(errorData.detail || `HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("[ChatService] Error in getArchivedChatSessions:", error);
        throw error;
    }
};

/**
 * Fetches messages for a specific chat session.
 * @param sessionId ID of the session
 * @returns Promise<ChatMessage[]>
 */
export const getChatMessages = async (sessionId: string): Promise<ChatMessage[]> => {
    if (!sessionId) {
        console.warn('[ChatService] getChatMessages called with null/empty sessionId');
        return [];
    }
    const url = `${CHAT_API_URL}/sessions/${sessionId}/messages`;
    console.log(`[ChatService] Fetching messages for session ${sessionId} from: ${url}`);
    try {
        const response = await fetchWithAuth(url);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `Failed to fetch messages for session ${sessionId}` }));
            throw new Error(errorData.detail || `HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`[ChatService] Error in getChatMessages for ${sessionId}:`, error);
        throw error;
    }
};

/**
 * Archives a specific chat session.
 * @param sessionId ID of the session to archive
 * @returns Promise<ChatSession> The updated session (or confirm response based on backend)
 */
export const archiveChatSession = async (sessionId: string): Promise<ChatSession> => {
    const url = `${CHAT_API_URL}/sessions/${sessionId}/archive`;
    console.log(`[ChatService] Archiving session: ${sessionId}`);
    try {
        const response = await fetchWithAuth(url, { method: 'PATCH' });
        if (!response.ok) {
             const errorData = await response.json().catch(() => ({ detail: `Failed to archive session ${sessionId}` }));
            throw new Error(errorData.detail || `HTTP error ${response.status}`);
        }
        // Assuming backend returns the archived session object
        return await response.json(); 
    } catch (error) {
        console.error(`[ChatService] Error in archiveChatSession for ${sessionId}:`, error);
        throw error;
    }
};

/**
 * Sends a message and processes the streaming response.
 * @param sessionId ID of the session (must not be null)
 * @param message The message content
 * @param onChunk Callback function called with each received chunk of the AI response
 */
export const sendMessageStream = async (
    sessionId: string, 
    message: string,
    onChunk: (chunk: string) => void
): Promise<void> => {
    const url = `${CHAT_API_URL}/stream`;
    console.log(`[ChatService] Sending message stream to: ${url} for session: ${sessionId}`);
    try {
        const response = await fetchWithAuth(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify({ 
                session_id: sessionId, 
                content: message,
                session_type: "CONSULTATION" // Match backend expectation
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error ${response.status}: ${errorText}`);
        }

        if (!response.body) {
            throw new Error('Response body is null for stream');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                console.log("[ChatService] Stream finished.");
                break;
            }
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; 

            for (const line of lines) {
                if (line.startsWith('data:')) {
                    const chunkData = line.substring(5).trim();
                    if (chunkData) {
                        try {
                            const parsedChunk = JSON.parse(chunkData);
                            if (typeof parsedChunk.content === 'string') {
                                onChunk(parsedChunk.content);
                            } else {
                                console.warn("[ChatService] Received non-string content:", parsedChunk);
                            }
                        } catch (e) {
                            console.warn("[ChatService] Chunk not JSON, treating as text:", chunkData);
                            onChunk(chunkData);
                        }
                    }
                }
            }
        }
    } catch (error) {
        console.error('[ChatService] Error in sendMessageStream:', error);
        throw error; // Re-throw for mutation handler
    }
};

/**
 * Restores an archived chat session (Placeholder).
 * @param sessionId ID of the session to restore
 * @returns Promise<ChatSession> The restored session
 */
export const restoreChatSession = async (sessionId: string): Promise<ChatSession> => {
    console.log(`[ChatService] Restoring session (placeholder): ${sessionId}`);
    // Replace with actual API call to backend endpoint (e.g., PATCH /sessions/{id}/restore)
    await new Promise(resolve => setTimeout(resolve, 300)); // Simulate delay
    // Return a mock object or throw error if endpoint doesn't exist
    const mockSession: ChatSession = {
        id: sessionId,
        title: `復元済: ${sessionId.substring(0, 6)}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
    };
    return mockSession; 
    // throw new Error("Restore functionality not implemented yet.");
}; 