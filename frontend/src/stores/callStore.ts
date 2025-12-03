import { create } from 'zustand';
import {
  Call,
  CallStatus,
  CallPriority,
  Transcript,
  TranscriptSegment,
} from '@/types';

interface CallState {
  // Current call
  currentCall: Call | null;
  transcript: Transcript | null;

  // Call control
  isMuted: boolean;
  isOnHold: boolean;

  // Actions
  startCall: (callId: string, sessionId: string, scenarioId?: string) => void;
  endCall: () => void;
  updateCallStatus: (status: CallStatus) => void;
  updateCallDuration: (duration: number) => void;
  addTranscriptSegment: (segment: TranscriptSegment) => void;
  updateTranscriptSegment: (segmentId: string, updates: Partial<TranscriptSegment>) => void;
  clearTranscript: () => void;
  toggleMute: () => void;
  toggleHold: () => void;
  setMuted: (muted: boolean) => void;
  setOnHold: (onHold: boolean) => void;
  reset: () => void;
}

export const useCallStore = create<CallState>((set, get) => ({
  currentCall: null,
  transcript: null,
  isMuted: false,
  isOnHold: false,

  startCall: (callId, sessionId, scenarioId) => {
    const call: Call = {
      id: callId,
      sessionId,
      status: CallStatus.ACTIVE,
      priority: CallPriority.MEDIUM,
      startTime: new Date(),
      duration: 0,
      operatorId: 'current-user', // TODO: Get from auth
      scenarioId,
    };

    set({
      currentCall: call,
      transcript: {
        callId,
        segments: [],
        updatedAt: new Date(),
      },
      isMuted: false,
      isOnHold: false,
    });
  },

  endCall: () => {
    const { currentCall } = get();
    if (currentCall) {
      set({
        currentCall: {
          ...currentCall,
          status: CallStatus.ENDED,
          endTime: new Date(),
        },
      });
    }
  },

  updateCallStatus: (status) => {
    const { currentCall } = get();
    if (currentCall) {
      set({
        currentCall: {
          ...currentCall,
          status,
        },
      });
    }
  },

  updateCallDuration: (duration) => {
    const { currentCall } = get();
    if (currentCall) {
      set({
        currentCall: {
          ...currentCall,
          duration,
        },
      });
    }
  },

  addTranscriptSegment: (segment) => {
    const { transcript } = get();
    if (transcript) {
      set({
        transcript: {
          ...transcript,
          segments: [...transcript.segments, segment],
          updatedAt: new Date(),
        },
      });
    }
  },

  updateTranscriptSegment: (segmentId, updates) => {
    const { transcript } = get();
    if (transcript) {
      set({
        transcript: {
          ...transcript,
          segments: transcript.segments.map((seg) =>
            seg.id === segmentId ? { ...seg, ...updates } : seg
          ),
          updatedAt: new Date(),
        },
      });
    }
  },

  clearTranscript: () => {
    const { transcript } = get();
    if (transcript) {
      set({
        transcript: {
          ...transcript,
          segments: [],
          updatedAt: new Date(),
        },
      });
    }
  },

  toggleMute: () => {
    set((state) => ({ isMuted: !state.isMuted }));
  },

  toggleHold: () => {
    set((state) => ({ isOnHold: !state.isOnHold }));
  },

  setMuted: (muted) => {
    set({ isMuted: muted });
  },

  setOnHold: (onHold) => {
    set({ isOnHold: onHold });
  },

  reset: () => {
    set({
      currentCall: null,
      transcript: null,
      isMuted: false,
      isOnHold: false,
    });
  },
}));
