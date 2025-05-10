import { useEffect, useRef, useState, useCallback } from 'react';

// サーバーからのメッセージの型定義 (より具体的にする)
export interface WebSocketMessage {
  type: 'chunk' | 'done' | 'error' | 'info' | string; // string は予期せぬ型も許容するため
  content?: string;       // For 'chunk'
  detail?: string;        // For 'error'
  message?: string;       // For 'info'
  session_id?: string;
  error?: boolean;        // For 'done' with error
  // 他にもサーバーが送る可能性のあるフィールドがあれば追加
}

interface UseChatWebSocketOptions {
  socketUrl: string;
  token: string | null;
  onMessageReceived: (message: WebSocketMessage) => void;
  onError: (event: Event | Error) => void; // Errorオブジェクトも受け付けるように
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
}

export const useChatWebSocket = ({
  socketUrl,
  token,
  onMessageReceived,
  onError,
  onOpen,
  onClose,
}: UseChatWebSocketOptions) => {
  const webSocketRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  // 再接続試行の管理用 (オプション)
  // const [retryCount, setRetryCount] = useState(0);

  // コールバックをrefで管理
  const onMessageReceivedRef = useRef(onMessageReceived);
  const onErrorRef = useRef(onError);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onMessageReceivedRef.current = onMessageReceived;
  }, [onMessageReceived]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    onOpenRef.current = onOpen;
  }, [onOpen]);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  const connect = useCallback(() => {
    if (!socketUrl || !token) {
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
      setIsConnected(false);
      return;
    }

    // 既存の接続があれば閉じる (重複接続防止)
    if (webSocketRef.current && webSocketRef.current.readyState !== WebSocket.CLOSED) {
        webSocketRef.current.close();
    }

    const fullSocketUrl = `${socketUrl}?token=${token}`;
    console.log(`Attempting to connect to WebSocket: ${fullSocketUrl}`);
    const ws = new WebSocket(fullSocketUrl);
    webSocketRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connection established');
      setIsConnected(true);
      // setRetryCount(0); // 接続成功でリトライカウントリセット
      if (onOpenRef.current) {
        onOpenRef.current();
      }
    };

    ws.onmessage = (event) => {
      try {
        const messageData = JSON.parse(event.data as string) as WebSocketMessage;
        if (onMessageReceivedRef.current) {
          onMessageReceivedRef.current(messageData);
        }
      } catch (e) {
        console.error('Failed to parse message data:', event.data, e);
        if (onErrorRef.current) {
          onErrorRef.current(e instanceof Error ? e : new Error('Failed to parse message data'));
        }
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setIsConnected(false);
      // 接続エラーは Event 型なので、より詳細なエラー情報が欲しい場合はラップする
      if (onErrorRef.current) {
        onErrorRef.current(event instanceof Error ? event : new Error('WebSocket error occurred'));
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket connection closed: ${event.reason} (Code: ${event.code})`);
      setIsConnected(false);
      // webSocketRef.current が現在のインスタンスと一致する場合のみ null 化
      if (webSocketRef.current === ws) {
        webSocketRef.current = null;
      }
      if (onCloseRef.current) {
        onCloseRef.current(event);
      }
      // 自動再接続ロジック (必要であれば)
      // if (event.code !== 1000 && retryCount < MAX_RETRIES) { // 1000は正常終了
      //   setTimeout(() => {
      //     setRetryCount(prev => prev + 1);
      //     connect(); 
      //   }, RETRY_INTERVAL);
      // }
    };
  }, [socketUrl, token]);

  useEffect(() => {
    connect(); // 初回接続

    return () => {
      if (webSocketRef.current) {
        // onclose ハンドラ内で webSocketRef.current を null にするため、ここでは状態を見るだけ
        if (webSocketRef.current.readyState === WebSocket.OPEN || webSocketRef.current.readyState === WebSocket.CONNECTING) {
            console.log('Closing WebSocket connection on unmount');
            webSocketRef.current.close(1000, 'Component unmounted'); // 正常終了コードで閉じる
        }
        // webSocketRef.current = null; // onclose で処理
      }
      setIsConnected(false); // アンマウント時は非接続状態に
    };
  }, [connect]); // connect が useCallback でラップされているため、依存関係は適切

  const sendMessage = useCallback((message: string | Record<string, any>) => {
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
      const messageToSend = typeof message === 'string' ? message : JSON.stringify(message);
      console.log('Sending message via WebSocket:', messageToSend);
      webSocketRef.current.send(messageToSend);
    } else {
      console.error('WebSocket is not connected or not open. Cannot send message.');
      if (onErrorRef.current) {
        onErrorRef.current(new Error('WebSocket is not connected. Cannot send message.'));
      }
      // UIにフィードバックする (例: トースト通知)
    }
  }, []); // onErrorRef に依存させる場合は [onErrorRef] -> 今回は呼ばない方針で空

  return { sendMessage, isConnected, webSocketRef }; // webSocketRef も返すように変更
}; 