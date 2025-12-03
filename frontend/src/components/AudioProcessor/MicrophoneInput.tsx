import { useEffect, useState } from 'react';
import { useAudioStream } from '@/hooks/useAudioStream';

interface MicrophoneInputProps {
  onAudioData?: (data: ArrayBuffer) => void;
  autoStart?: boolean;
}

const MicrophoneInput = ({ onAudioData, autoStart = false }: MicrophoneInputProps) => {
  const {
    isInitialized,
    isRecording,
    error,
    initialize,
    startRecording,
    stopRecording,
  } = useAudioStream({
    onAudioData: (chunk) => {
      onAudioData?.(chunk.data);
    },
  });

  const [permissionStatus, setPermissionStatus] = useState<'prompt' | 'granted' | 'denied'>('prompt');

  useEffect(() => {
    // Check microphone permission status
    if (navigator.permissions) {
      navigator.permissions.query({ name: 'microphone' as PermissionName }).then((result) => {
        setPermissionStatus(result.state as 'prompt' | 'granted' | 'denied');
        result.onchange = () => {
          setPermissionStatus(result.state as 'prompt' | 'granted' | 'denied');
        };
      });
    }
  }, []);

  useEffect(() => {
    if (autoStart && !isInitialized && permissionStatus !== 'denied') {
      handleInitialize();
    }
  }, [autoStart, isInitialized, permissionStatus]);

  const handleInitialize = async () => {
    try {
      await initialize();
    } catch (err) {
      console.error('Failed to initialize microphone:', err);
    }
  };

  const handleStart = () => {
    if (!isInitialized) {
      handleInitialize().then(() => {
        startRecording();
      });
    } else {
      startRecording();
    }
  };

  const handleStop = () => {
    stopRecording();
  };

  if (error) {
    return (
      <div className="card border-l-4 border-red-500">
        <div className="flex items-start space-x-3">
          <svg
            className="w-6 h-6 text-red-500 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <h3 className="font-semibold text-red-800">Microphone Error</h3>
            <p className="text-sm text-red-600 mt-1">{error}</p>
            <button onClick={handleInitialize} className="btn btn-secondary mt-3 text-sm">
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-3 rounded-full ${isRecording ? 'bg-red-100' : 'bg-gray-100'}`}>
            <svg
              className={`w-6 h-6 ${isRecording ? 'text-red-600' : 'text-gray-600'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
              />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Microphone</h3>
            <p className="text-sm text-gray-600">
              {isRecording ? 'Recording...' : isInitialized ? 'Ready' : 'Not initialized'}
            </p>
          </div>
        </div>

        <div className="flex space-x-2">
          {!isRecording ? (
            <button onClick={handleStart} className="btn btn-success">
              Start
            </button>
          ) : (
            <button onClick={handleStop} className="btn btn-danger">
              Stop
            </button>
          )}
        </div>
      </div>

      {permissionStatus === 'denied' && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            Microphone access is blocked. Please enable it in your browser settings.
          </p>
        </div>
      )}
    </div>
  );
};

export default MicrophoneInput;
