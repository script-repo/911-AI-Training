import { useEffect, useCallback } from 'react';
import { websocketService } from '@/services/websocket.service';
import { useConnectionStore } from '@/stores/connectionStore';
import { WSMessage, WSMessageType } from '@/types';

export const useWebSocket = () => {
  const { setConnectionState, status } = useConnectionStore();

  useEffect(() => {
    // Subscribe to connection state changes
    const unsubscribe = websocketService.onConnectionStateChange((state) => {
      setConnectionState(state);
    });

    return () => {
      unsubscribe();
    };
  }, [setConnectionState]);

  const connect = useCallback(() => {
    websocketService.connect();
  }, []);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  const send = useCallback((message: WSMessage) => {
    websocketService.send(message);
  }, []);

  const sendAudio = useCallback(
    (audioData: ArrayBuffer, callId: string, sequenceNumber: number) => {
      websocketService.sendAudio(audioData, callId, sequenceNumber);
    },
    []
  );

  const onMessage = useCallback((handler: (message: WSMessage) => void) => {
    return websocketService.onMessage(handler);
  }, []);

  return {
    connect,
    disconnect,
    send,
    sendAudio,
    onMessage,
    isConnected: websocketService.isConnected(),
    connectionStatus: status,
  };
};

export const useWebSocketMessage = (
  messageType: WSMessageType,
  handler: (payload: any) => void
) => {
  const { onMessage } = useWebSocket();

  useEffect(() => {
    const unsubscribe = onMessage((message: WSMessage) => {
      if (message.type === messageType) {
        handler(message.payload);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [onMessage, messageType, handler]);
};
