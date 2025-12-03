import { useEffect, useRef } from 'react';
import { useTranscript } from '@/hooks/useTranscript';
import { useEntityStore } from '@/stores/entityStore';
import { SpeakerType } from '@/types';
import { format } from 'date-fns';
import EntityHighlight from '../EntityVisualizer/EntityHighlight';

const TranscriptView = () => {
  const { segments } = useTranscript();
  const { highlightedEntityId } = useEntityStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef(true);

  // Auto-scroll to bottom when new segments arrive
  useEffect(() => {
    if (autoScrollRef.current && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [segments]);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    // Enable auto-scroll if user is near the bottom
    autoScrollRef.current = scrollHeight - scrollTop - clientHeight < 100;
  };

  const getSpeakerColor = (speaker: SpeakerType) => {
    switch (speaker) {
      case SpeakerType.OPERATOR:
        return 'bg-blue-50 border-blue-200';
      case SpeakerType.CALLER:
        return 'bg-gray-100 border-gray-200';
      case SpeakerType.SYSTEM:
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getSpeakerLabel = (speaker: SpeakerType) => {
    switch (speaker) {
      case SpeakerType.OPERATOR:
        return 'Operator';
      case SpeakerType.CALLER:
        return 'Caller';
      case SpeakerType.SYSTEM:
        return 'System';
      default:
        return 'Unknown';
    }
  };

  const getSpeakerIcon = (speaker: SpeakerType) => {
    switch (speaker) {
      case SpeakerType.OPERATOR:
        return '👤';
      case SpeakerType.CALLER:
        return '📞';
      case SpeakerType.SYSTEM:
        return '🔔';
      default:
        return '❓';
    }
  };

  if (segments.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 mb-4">
          <svg
            className="w-16 h-16 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <p className="text-gray-500">Waiting for conversation to begin...</p>
        <p className="text-sm text-gray-400 mt-2">Transcript will appear here in real-time</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="space-y-4 max-h-[600px] overflow-y-auto pr-2"
    >
      {segments.map((segment) => (
        <div
          key={segment.id}
          className={`p-4 border rounded-lg transition-all duration-200 ${getSpeakerColor(
            segment.speaker
          )} ${
            highlightedEntityId && segment.text.includes(highlightedEntityId)
              ? 'ring-2 ring-blue-400'
              : ''
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-lg">{getSpeakerIcon(segment.speaker)}</span>
              <span className="font-semibold text-sm text-gray-700">
                {getSpeakerLabel(segment.speaker)}
              </span>
              {!segment.isFinal && (
                <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded">
                  Interim
                </span>
              )}
            </div>
            <span className="text-xs text-gray-500">
              {format(new Date(segment.timestamp), 'HH:mm:ss')}
            </span>
          </div>

          <div className="text-gray-900">
            <EntityHighlight text={segment.text} segmentId={segment.id} />
          </div>

          {segment.confidence !== undefined && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">Confidence:</span>
                <div className="flex-1 max-w-[200px] bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      segment.confidence > 0.8
                        ? 'bg-green-500'
                        : segment.confidence > 0.6
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${segment.confidence * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-600 font-medium">
                  {Math.round(segment.confidence * 100)}%
                </span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default TranscriptView;
