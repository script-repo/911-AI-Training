import { useCallback, useEffect, useRef } from 'react';
import { useCallStore } from '@/stores/callStore';
import { useEntityStore } from '@/stores/entityStore';
import { useWebSocket, useWebSocketMessage } from './useWebSocket';
import { useAudioStream } from './useAudioStream';
import { apiService } from '@/services/api.service';
import {
  WSMessageType,
  CallStatus,
  TranscriptUpdatePayload,
  EntityUpdatePayload,
  StatusUpdatePayload,
} from '@/types';

export const useCallSession = () => {
  const {
    currentCall,
    startCall: startCallState,
    endCall: endCallState,
    updateCallStatus,
    addTranscriptSegment,
    reset: resetCall,
  } = useCallStore();

  const { setEntities, clearEntities } = useEntityStore();
  const { connect, disconnect, send, sendAudio, isConnected } = useWebSocket();
  const durationIntervalRef = useRef<number | null>(null);

  // Audio streaming
  const { initialize, startRecording, stopRecording, isInitialized, isRecording } =
    useAudioStream({
      onAudioData: (chunk) => {
        if (currentCall && isConnected) {
          sendAudio(chunk.data, currentCall.id, chunk.sequenceNumber);
        }
      },
    });

  // Handle transcript updates
  useWebSocketMessage(
    WSMessageType.TRANSCRIPT_UPDATE,
    useCallback(
      (payload: TranscriptUpdatePayload) => {
        if (payload.callId === currentCall?.id) {
          addTranscriptSegment(payload.segment);
        }
      },
      [currentCall?.id, addTranscriptSegment]
    )
  );

  // Handle entity updates
  useWebSocketMessage(
    WSMessageType.ENTITY_UPDATE,
    useCallback(
      (payload: EntityUpdatePayload) => {
        if (payload.callId === currentCall?.id) {
          setEntities(payload.entities, payload.callId);
        }
      },
      [currentCall?.id, setEntities]
    )
  );

  // Handle status updates
  useWebSocketMessage(
    WSMessageType.STATUS_UPDATE,
    useCallback(
      (payload: StatusUpdatePayload) => {
        if (payload.callId === currentCall?.id) {
          updateCallStatus(payload.status);
        }
      },
      [currentCall?.id, updateCallStatus]
    )
  );

  // Start a new call session
  const startCall = useCallback(
    async (scenarioId?: string) => {
      try {
        // Initialize audio if not already done
        if (!isInitialized) {
          await initialize();
        }

        // Connect WebSocket
        if (!isConnected) {
          connect();
        }

        // Start call via API
        const response = await apiService.startCall(scenarioId);
        if (!response.success || !response.data) {
          throw new Error(response.error || 'Failed to start call');
        }

        const { callId, sessionId } = response.data;

        // Update local state
        startCallState(callId, sessionId, scenarioId);

        // Send call start message via WebSocket
        send({
          type: WSMessageType.CALL_START,
          payload: {
            callId,
            sessionId,
            scenarioId,
            audioConfig: {
              sampleRate: 16000,
              channels: 1,
              bitsPerSample: 16,
              codec: 'pcm',
            },
          },
          timestamp: Date.now(),
        });

        // Start recording
        startRecording();

        // Start duration timer
        durationIntervalRef.current = window.setInterval(() => {
          useCallStore.getState().updateCallDuration(
            Math.floor((Date.now() - new Date(currentCall?.startTime || Date.now()).getTime()) / 1000)
          );
        }, 1000);

        return callId;
      } catch (error) {
        console.error('Failed to start call:', error);
        throw error;
      }
    },
    [
      isInitialized,
      isConnected,
      initialize,
      connect,
      startCallState,
      send,
      startRecording,
      currentCall?.startTime,
    ]
  );

  // End the current call session
  const endCall = useCallback(async () => {
    if (!currentCall) return;

    try {
      // Stop recording
      stopRecording();

      // Stop duration timer
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }

      // Send call end message via WebSocket
      send({
        type: WSMessageType.CALL_END,
        payload: { callId: currentCall.id },
        timestamp: Date.now(),
      });

      // End call via API
      await apiService.endCall(currentCall.id);

      // Update local state
      endCallState();
    } catch (error) {
      console.error('Failed to end call:', error);
      throw error;
    }
  }, [currentCall, stopRecording, send, endCallState]);

  // Reset session
  const resetSession = useCallback(() => {
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }
    stopRecording();
    resetCall();
    clearEntities();
  }, [stopRecording, resetCall, clearEntities]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, []);

  return {
    currentCall,
    isConnected,
    isRecording,
    startCall,
    endCall,
    resetSession,
  };
};
