import {
  WSMessage,
  WSMessageType,
  ConnectionStatus,
  ConnectionState,
} from '@/types';

export type MessageHandler = (message: WSMessage) => void;
export type ConnectionStateHandler = (state: ConnectionState) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionStateHandlers: Set<ConnectionStateHandler> = new Set();
  private connectionState: ConnectionState = {
    status: ConnectionStatus.DISCONNECTED,
    reconnectAttempts: 0,
  };
  private heartbeatInterval: number | null = null;
  private reconnectTimeout: number | null = null;

  constructor(url?: string) {
    this.url = url || this.getWebSocketUrl();
  }

  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_URL || window.location.host;
    return `${protocol}//${host}/ws`;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.updateConnectionState({
      status: ConnectionStatus.CONNECTING,
      reconnectAttempts: this.reconnectAttempts,
    });

    try {
      this.ws = new WebSocket(this.url);
      this.setupEventHandlers();
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.handleConnectionError(error);
    }
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.updateConnectionState({
      status: ConnectionStatus.DISCONNECTED,
      reconnectAttempts: 0,
    });
  }

  send(message: WSMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }

  sendAudio(audioData: ArrayBuffer, callId: string, sequenceNumber: number): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      // Send metadata first
      const metadata = {
        type: WSMessageType.AUDIO_CHUNK,
        callId,
        sequenceNumber,
        timestamp: Date.now(),
      };
      this.ws.send(JSON.stringify(metadata));
      // Then send binary data
      this.ws.send(audioData);
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onConnectionStateChange(handler: ConnectionStateHandler): () => void {
    this.connectionStateHandlers.add(handler);
    // Immediately call with current state
    handler(this.connectionState);
    return () => this.connectionStateHandlers.delete(handler);
  }

  getConnectionState(): ConnectionState {
    return { ...this.connectionState };
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.updateConnectionState({
        status: ConnectionStatus.CONNECTED,
        lastConnected: new Date(),
        reconnectAttempts: 0,
      });
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);

        // Handle pong messages internally
        if (message.type === WSMessageType.PONG) {
          return;
        }

        // Notify all handlers
        this.messageHandlers.forEach((handler) => handler(message));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.handleConnectionError(error);
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.stopHeartbeat();

      if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      } else {
        this.updateConnectionState({
          status: ConnectionStatus.DISCONNECTED,
          reconnectAttempts: this.reconnectAttempts,
        });
      }
    };
  }

  private scheduleReconnect(): void {
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    this.updateConnectionState({
      status: ConnectionStatus.RECONNECTING,
      reconnectAttempts: this.reconnectAttempts,
    });

    this.reconnectTimeout = window.setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      this.connect();
    }, delay);
  }

  private handleConnectionError(error: unknown): void {
    this.updateConnectionState({
      status: ConnectionStatus.ERROR,
      reconnectAttempts: this.reconnectAttempts,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({
          type: WSMessageType.PING,
          payload: null,
          timestamp: Date.now(),
        });
      }
    }, 30000); // Send ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private updateConnectionState(state: Partial<ConnectionState>): void {
    this.connectionState = { ...this.connectionState, ...state };
    this.connectionStateHandlers.forEach((handler) =>
      handler(this.connectionState)
    );
  }
}

// Singleton instance
export const websocketService = new WebSocketService();
export default websocketService;
