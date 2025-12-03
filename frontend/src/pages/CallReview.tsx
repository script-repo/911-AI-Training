import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api.service';
import { format } from 'date-fns';
import { EntityType } from '@/types';

const CallReview = () => {
  const { callId } = useParams<{ callId: string }>();

  const { data: callDetails, isLoading: isLoadingCall } = useQuery({
    queryKey: ['callDetails', callId],
    queryFn: async () => {
      if (!callId) throw new Error('Call ID is required');
      const response = await apiService.getCallDetails(callId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to load call details');
      }
      return response.data;
    },
    enabled: !!callId,
  });

  const { data: metrics, isLoading: isLoadingMetrics } = useQuery({
    queryKey: ['callMetrics', callId],
    queryFn: async () => {
      if (!callId) throw new Error('Call ID is required');
      const response = await apiService.getCallMetrics(callId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to load metrics');
      }
      return response.data;
    },
    enabled: !!callId,
  });

  const { data: transcript, isLoading: isLoadingTranscript } = useQuery({
    queryKey: ['callTranscript', callId],
    queryFn: async () => {
      if (!callId) throw new Error('Call ID is required');
      const response = await apiService.getCallTranscript(callId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to load transcript');
      }
      return response.data;
    },
    enabled: !!callId,
  });

  const isLoading = isLoadingCall || isLoadingMetrics || isLoadingTranscript;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading call review...</p>
        </div>
      </div>
    );
  }

  if (!callDetails) {
    return (
      <div className="card border-l-4 border-red-500">
        <h2 className="text-xl font-bold text-red-600 mb-2">Call Not Found</h2>
        <p className="text-gray-600">The requested call could not be found.</p>
        <Link to="/history" className="btn btn-primary mt-4">
          Back to History
        </Link>
      </div>
    );
  }

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link to="/history" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
          ← Back to History
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Call Review</h1>
        <p className="text-gray-600">
          {format(new Date(callDetails.startTime), 'MMMM dd, yyyy at HH:mm')}
        </p>
      </div>

      {/* Call Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Duration</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatDuration(callDetails.duration)}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Score</p>
          <p className="text-2xl font-bold text-gray-900">
            {metrics?.score || 'N/A'}
            {metrics?.score && '%'}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Response Time</p>
          <p className="text-2xl font-bold text-gray-900">
            {metrics?.responseTime ? `${metrics.responseTime}s` : 'N/A'}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Entities Found</p>
          <p className="text-2xl font-bold text-gray-900">
            {metrics?.entitiesExtracted || 0}
          </p>
        </div>
      </div>

      {/* Metrics Details */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Critical Information */}
          <div className="card">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              Critical Information Gathered
            </h2>
            {metrics.criticalInfoGathered && metrics.criticalInfoGathered.length > 0 ? (
              <ul className="space-y-2">
                {metrics.criticalInfoGathered.map((info, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    <span className="text-gray-700">{info}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No critical information recorded</p>
            )}
          </div>

          {/* Missed Information */}
          <div className="card">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Missed Information</h2>
            {metrics.missedInformation && metrics.missedInformation.length > 0 ? (
              <ul className="space-y-2">
                {metrics.missedInformation.map((info, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-red-500 mr-2">✗</span>
                    <span className="text-gray-700">{info}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-green-600">All critical information was gathered!</p>
            )}
          </div>
        </div>
      )}

      {/* Transcript */}
      {transcript && transcript.segments && (
        <div className="card">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Full Transcript</h2>
          <div className="space-y-4 max-h-[600px] overflow-y-auto">
            {transcript.segments.map((segment: any) => (
              <div
                key={segment.id}
                className={`p-4 rounded-lg ${
                  segment.speaker === 'operator'
                    ? 'bg-blue-50 ml-8'
                    : 'bg-gray-100 mr-8'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-sm text-gray-700">
                    {segment.speaker === 'operator' ? 'Operator' : 'Caller'}
                  </span>
                  <span className="text-xs text-gray-500">
                    {format(new Date(segment.timestamp), 'HH:mm:ss')}
                  </span>
                </div>
                <p className="text-gray-900">{segment.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CallReview;
