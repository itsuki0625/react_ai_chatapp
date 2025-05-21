import { toast } from 'sonner';

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout = 1000;

  constructor(private url: string) {}

  connect() {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket接続が確立されました');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('メッセージの処理中にエラーが発生しました:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket接続が切断されました');
        this.reconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocketエラー:', error);
      };
    } catch (error) {
      console.error('WebSocket接続中にエラーが発生しました:', error);
      this.reconnect();
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`再接続を試みています (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, this.reconnectTimeout * this.reconnectAttempts);
    } else {
      console.error('最大再接続回数に達しました');
    }
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'notification':
        this.handleNotification(data.payload);
        break;
      default:
        console.warn('未知のメッセージタイプ:', data.type);
    }
  }

  private handleNotification(notification: any) {
    // 通知を表示
    toast(notification.title, {
      description: notification.message,
      action: notification.action,
    });

    // プッシュ通知が有効な場合は、プッシュ通知も表示
    if (notification.push && 'Notification' in window && Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/icon.png',
        badge: '/badge.png',
      });
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const websocketClient = new WebSocketClient(process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws'); 