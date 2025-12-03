import { useMemo } from 'react';
import { useCallStore } from '@/stores/callStore';
import { SpeakerType, TranscriptSegment } from '@/types';

export const useTranscript = () => {
  const { transcript } = useCallStore();

  const segments = useMemo(() => {
    return transcript?.segments || [];
  }, [transcript]);

  const operatorSegments = useMemo(() => {
    return segments.filter((s) => s.speaker === SpeakerType.OPERATOR);
  }, [segments]);

  const callerSegments = useMemo(() => {
    return segments.filter((s) => s.speaker === SpeakerType.CALLER);
  }, [segments]);

  const lastSegment = useMemo(() => {
    return segments[segments.length - 1] || null;
  }, [segments]);

  const getSegmentById = (id: string): TranscriptSegment | undefined => {
    return segments.find((s) => s.id === id);
  };

  const searchTranscript = (query: string): TranscriptSegment[] => {
    const lowerQuery = query.toLowerCase();
    return segments.filter((s) => s.text.toLowerCase().includes(lowerQuery));
  };

  return {
    transcript,
    segments,
    operatorSegments,
    callerSegments,
    lastSegment,
    getSegmentById,
    searchTranscript,
  };
};
