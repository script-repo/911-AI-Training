import { create } from 'zustand';
import { ConnectionState, ConnectionStatus } from '@/types';

interface ConnectionStoreState extends ConnectionState {
  setConnectionState: (state: ConnectionState) => void;
  reset: () => void;
}

const initialState: ConnectionState = {
  status: ConnectionStatus.DISCONNECTED,
  reconnectAttempts: 0,
};

export const useConnectionStore = create<ConnectionStoreState>((set) => ({
  ...initialState,

  setConnectionState: (state) => {
    set(state);
  },

  reset: () => {
    set(initialState);
  },
}));
