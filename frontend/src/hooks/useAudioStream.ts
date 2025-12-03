import { useState, useEffect, useCallback, useRef } from 'react';
import { audioService } from '@/services/audio.service';
import { AudioConfig, AudioChunk } from '@/types';

interface UseAudioStreamOptions {
  onAudioData?: (chunk: AudioChunk) => void;
  config?: Partial<AudioConfig>;
}

export const useAudioStream = (options: UseAudioStreamOptions = {}) => {
  const { onAudioData, config } = options;
  const [isInitialized, setIsInitialized] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [volume, setVolume] = useState(0);
  const volumeIntervalRef = useRef<number | null>(null);

  // Initialize audio service
  const initialize = useCallback(async () => {
    try {
      await audioService.initialize(config);
      setIsInitialized(true);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize audio');
      setIsInitialized(false);
    }
  }, [config]);

  // Start recording
  const startRecording = useCallback(() => {
    if (!isInitialized) {
      setError('Audio service not initialized');
      return;
    }

    try {
      audioService.startRecording((chunk) => {
        onAudioData?.(chunk);
      });
      setIsRecording(true);
      setError(null);

      // Start monitoring volume
      volumeIntervalRef.current = window.setInterval(() => {
        const vol = audioService.getVolume();
        setVolume(vol);
      }, 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start recording');
    }
  }, [isInitialized, onAudioData]);

  // Stop recording
  const stopRecording = useCallback(() => {
    audioService.stopRecording();
    setIsRecording(false);

    // Stop monitoring volume
    if (volumeIntervalRef.current) {
      clearInterval(volumeIntervalRef.current);
      volumeIntervalRef.current = null;
    }
    setVolume(0);
  }, []);

  // Get analyser node for visualization
  const getAnalyserNode = useCallback(() => {
    return audioService.getAnalyserNode();
  }, []);

  // Get frequency data for visualization
  const getFrequencyData = useCallback(() => {
    return audioService.getFrequencyData();
  }, []);

  // Get time domain data for waveform
  const getTimeDomainData = useCallback(() => {
    return audioService.getTimeDomainData();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (volumeIntervalRef.current) {
        clearInterval(volumeIntervalRef.current);
      }
      audioService.cleanup();
    };
  }, []);

  return {
    isInitialized,
    isRecording,
    error,
    volume,
    initialize,
    startRecording,
    stopRecording,
    getAnalyserNode,
    getFrequencyData,
    getTimeDomainData,
  };
};
