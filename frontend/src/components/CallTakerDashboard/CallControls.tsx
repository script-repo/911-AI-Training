import { useState } from 'react';
import { useCallStore } from '@/stores/callStore';

interface CallControlsProps {
  onEndCall: () => void;
}

const CallControls = ({ onEndCall }: CallControlsProps) => {
  const { isMuted, isOnHold, toggleMute, toggleHold } = useCallStore();
  const [showEndConfirm, setShowEndConfirm] = useState(false);

  const handleEndCall = () => {
    if (!showEndConfirm) {
      setShowEndConfirm(true);
      setTimeout(() => setShowEndConfirm(false), 5000);
      return;
    }
    onEndCall();
  };

  return (
    <div className="card space-y-4">
      <h2 className="text-lg font-bold text-gray-900 mb-4">Call Controls</h2>

      {/* Mute Button */}
      <button
        onClick={toggleMute}
        className={`w-full btn ${
          isMuted
            ? 'bg-red-100 text-red-800 hover:bg-red-200 border-2 border-red-300'
            : 'btn-secondary'
        }`}
      >
        <div className="flex items-center justify-center space-x-2">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            {isMuted ? (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
              />
            ) : (
              <>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </>
            )}
          </svg>
          <span className="font-semibold">{isMuted ? 'Unmute' : 'Mute'}</span>
        </div>
      </button>

      {/* Hold Button */}
      <button
        onClick={toggleHold}
        className={`w-full btn ${
          isOnHold
            ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200 border-2 border-yellow-300'
            : 'btn-secondary'
        }`}
      >
        <div className="flex items-center justify-center space-x-2">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="font-semibold">{isOnHold ? 'Resume' : 'Hold'}</span>
        </div>
      </button>

      {/* Transfer Button (Placeholder) */}
      <button className="w-full btn btn-secondary" disabled>
        <div className="flex items-center justify-center space-x-2">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
            />
          </svg>
          <span className="font-semibold">Transfer</span>
        </div>
      </button>

      {/* End Call Button */}
      <div className="pt-4 border-t">
        <button
          onClick={handleEndCall}
          className={`w-full btn ${
            showEndConfirm
              ? 'bg-red-600 text-white hover:bg-red-700 animate-pulse'
              : 'btn-danger'
          }`}
        >
          <div className="flex items-center justify-center space-x-2">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            <span className="font-semibold">
              {showEndConfirm ? 'Click Again to Confirm' : 'End Call'}
            </span>
          </div>
        </button>
        {showEndConfirm && (
          <p className="text-xs text-center text-gray-600 mt-2">
            This will end the call and save the session
          </p>
        )}
      </div>
    </div>
  );
};

export default CallControls;
