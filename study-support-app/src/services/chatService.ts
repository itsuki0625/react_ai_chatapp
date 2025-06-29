import { fetchWithAuth } from '@/lib/fetchWithAuth';
import { ChatSession, ChatMessage, ChatTypeEnum, type ChatTypeValue } from '@/types/chat'; // Ensure types are correctly defined and imported
import { apiClient } from '@/lib/api';
import { API_BASE_URL } from '@/lib/config';

const CHAT_API_URL = `${API_BASE_URL}/api/v1/chat`;

/**
 * Fetches active chat sessions.
 * @param sessionType Type of session (e.g., "CONSULTATION")
 * @returns Promise<ChatSession[]>
 */
export const getChatSessions = async (sessionType: string = "CONSULTATION"): Promise<ChatSession[]> => {
    try {
        console.log(`[ChatService] Fetching active sessions for type: ${sessionType}`);
        const response = await apiClient.get('/api/v1/chat/sessions', { 
            params: { session_type: sessionType } 
        });
        return response.data;
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
 * @param sessionId ID of the session (null for new session)
 * @param messageContent The message content
 * @param chatType The type of chat (e.g., ChatType.ADMISSION)
 * @param onChunk Callback function called with each received chunk of the AI response
 * @param onSessionInitialized Optional callback function called when a new session ID is initialized
 */
export const sendMessageStream = async (
    sessionId: string | null,
    messageContent: string,
    chatType: ChatTypeValue,
    onChunk: (chunk: string) => void,
    onSessionInitialized?: (newSessionId: string, initialTitle?: string) => void
): Promise<void> => {
    const url = `${CHAT_API_URL}/stream`;
    console.log(`[ChatService] Sending message stream to: ${url}. Session ID: ${sessionId}, Chat Type: ${chatType}, Message: "${messageContent}"`);

    const requestBody: {
        message: string;
        chat_type: ChatTypeValue;
        session_id?: string;
    } = {
        message: messageContent,
        chat_type: chatType,
    };

    if (sessionId) {
        requestBody.session_id = sessionId;
    }

    try {
        const response = await fetchWithAuth(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[ChatService] HTTP error ${response.status}: ${errorText}`);
            // より詳細なエラー情報を取得試行
            let detail = errorText;
            try {
                const errorJson = JSON.parse(errorText);
                detail = errorJson.detail || errorText;
            } catch (e) {
                // JSONパース失敗時はそのままテキストを使用
            }
            throw new Error(`メッセージの送信に失敗しました。(サーバーエラー: ${response.status} ${detail})`);
        }

        if (!response.body) {
            throw new Error('ストリーミング応答のボディがありません。');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let newSessionIdReceived = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                console.log("[ChatService] Stream finished.");
                if (buffer.trim()) { // バッファに残りがあれば処理
                    // 最後のチャンクがJSON形式である可能性も考慮 (ただし通常はプレーンテキスト)
                     try {
                        const parsedChunk = JSON.parse(buffer.trim());
                        if (parsedChunk.event === 'session_initialized' && parsedChunk.session_id && onSessionInitialized && !newSessionIdReceived) {
                            onSessionInitialized(parsedChunk.session_id, parsedChunk.title);
                            newSessionIdReceived = true;
                        } else if (parsedChunk.content) {
                            onChunk(parsedChunk.content);
                        } else {
                             onChunk(buffer.trim()); // JSONだが期待した形式でない場合はそのまま
                        }
                    } catch (_e) {
                        onChunk(buffer.trim()); // JSONでなければそのままテキストとして処理
                    }
                }
                break;
            }
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data:')) {
                    const chunkData = line.substring(5).trim();
                    if (chunkData) {
                        if (chunkData === "[DONE]") { // バックエンドが [DONE] を送る場合
                            console.log("[ChatService] Received [DONE] signal from stream.");
                            // done フラグが true になるので、通常はこのループの外で break
                            continue;
                        }
                        try {
                            const parsedEvent = JSON.parse(chunkData);
                            if (parsedEvent.event === 'session_initialized' && parsedEvent.session_id && onSessionInitialized && !newSessionIdReceived) {
                                console.log(`[ChatService] New session initialized from stream: ${parsedEvent.session_id}, Title: ${parsedEvent.title}`);
                                onSessionInitialized(parsedEvent.session_id, parsedEvent.title);
                                newSessionIdReceived = true;
                                if (parsedEvent.content) { // 初期化イベントにメッセージチャンクが含まれる場合
                                    onChunk(parsedEvent.content);
                                }
                            } else if (parsedEvent.event === 'chunk' && typeof parsedEvent.content === 'string') {
                                onChunk(parsedEvent.content);
                            } else if (parsedEvent.event === 'error') {
                                console.error("[ChatService] Received error event from stream:", parsedEvent.detail);
                                throw new Error(parsedEvent.detail || "ストリームからのエラーイベント");
                            } else if (typeof parsedEvent.content === 'string') { // eventタイプがないがcontentがある場合
                                onChunk(parsedEvent.content);
                            }
                             else {
                                // 上記のどれにも当てはまらないJSONだが、とりあえずそのまま送ってみる (デバッグ用)
                                // 本来はバックエンドの出力形式を固定すべき
                                console.warn("[ChatService] Received unhandled JSON structure in stream, treating as plain text:", chunkData);
                                onChunk(chunkData);
                            }
                        } catch (_e) {
                            // JSONパースに失敗した場合、そのままテキストとして扱う
                            onChunk(chunkData);
                        }
                    }
                } else if (line.trim()) { // "data:" プレフィックスなしの行 (稀だが念のため)
                    onChunk(line.trim());
                }
            }
        }
    } catch (error) {
        console.error('[ChatService] Error in sendMessageStream:', error);
        // エラーを onChunk 経由ではなく、呼び出し元にスローして処理させる
        throw error;
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
        chat_type: ChatTypeEnum.GENERAL,
    };
    return mockSession; 
    // throw new Error("Restore functionality not implemented yet.");
}; 