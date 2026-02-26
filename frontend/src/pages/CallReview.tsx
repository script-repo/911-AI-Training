import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api.service';

// PRD FR-5.5: Post-call scoring summary, transcript with highlighted protocol events,
// audio playback, and actionable feedback.

interface Subscore {
  points: number;
  max: number;
  threshold_met?: boolean;
  time_seconds?: number | null;
}

interface FeedbackItem {
  criterion: string;
  message: string;
  rating: 'good' | 'needs_improvement' | 'missed';
}

interface ProtocolError {
  criterion: string;
  issue: string;
}

interface ScoringMetrics {
  call_id: string;
  total_score: number | null;
  max_possible_score?: number;
  subscores?: Record<string, Subscore>;
  protocol_errors?: ProtocolError[];
  feedback?: FeedbackItem[];
  computed_at?: string;
  // Legacy fields
  metrics?: Array<{ name: string; value: number; measured_at: string }>;
}

const CallReview = () => {
  const { callId } = useParams<{ callId: string }>();

  const { data: callDetails, isLoading: isLoadingCall } = useQuery({
    queryKey: ['callDetails', callId],
    queryFn: async () => {
      if (!callId) throw new Error('Call ID is required');
      const response = await apiService.getCallDetails(callId);
      if (!response.success) throw new Error(response.error || 'Failed to load call details');
      return response.data;
    },
    enabled: !!callId,
  });

  const { data: metrics, isLoading: isLoadingMetrics } = useQuery<ScoringMetrics>({
    queryKey: ['callMetrics', callId],
    queryFn: async () => {
      if (!callId) throw new Error('Call ID is required');
      const response = await apiService.getCallMetrics(callId);
      if (!response.success) throw new Error(response.error || 'Failed to load metrics');
      return response.data as ScoringMetrics;
    },
    enabled: !!callId,
  });

  const { data: transcript, isLoading: isLoadingTranscript } = useQuery({
    queryKey: ['callTranscript', callId],
    queryFn: async () => {
      if (!callId) throw new Error('Call ID is required');
      const response = await apiService.getCallTranscript(callId);
      if (!response.success) throw new Error(response.error || 'Failed to load transcript');
      return response.data;
    },
    enabled: !!callId,
  });

  const isLoading = isLoadingCall || isLoadingMetrics || isLoadingTranscript;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
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
        <Link to="/history" className="btn btn-primary mt-4">Back to History</Link>
      </div>
    );
  }

  const formatDuration = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTimestamp = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getRatingStyle = (rating: string) => {
    switch (rating) {
      case 'good': return 'bg-green-50 border-green-200 text-green-800';
      case 'needs_improvement': return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'missed': return 'bg-red-50 border-red-200 text-red-800';
      default: return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getRatingIcon = (rating: string) => {
    switch (rating) {
      case 'good': return '✓';
      case 'needs_improvement': return '!';
      case 'missed': return '✗';
      default: return '?';
    }
  };

  const scorePercent = metrics?.total_score != null && metrics?.max_possible_score
    ? Math.round((metrics.total_score / metrics.max_possible_score) * 100)
    : null;

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link to="/history" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
          &larr; Back to History
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Call Review</h1>
        <div className="flex items-center gap-4">
          <Link to="/scenarios" className="btn btn-primary text-sm">Next Scenario</Link>
          <Link to={`/review/${callId}`} className="btn btn-secondary text-sm"
            onClick={(e) => { e.preventDefault(); window.location.reload(); }}>
            Retry
          </Link>
        </div>
      </div>

      {/* Score Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Duration</p>
          <p className="text-2xl font-bold text-gray-900">
            {(callDetails as any).duration_ms
              ? formatDuration((callDetails as any).duration_ms)
              : (callDetails as any).duration
                ? formatDuration((callDetails as any).duration * 1000)
                : 'N/A'}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Score</p>
          <p className={`text-2xl font-bold ${
            scorePercent != null
              ? scorePercent >= 80 ? 'text-green-600' : scorePercent >= 60 ? 'text-yellow-600' : 'text-red-600'
              : 'text-gray-900'
          }`}>
            {scorePercent != null ? `${scorePercent}%` : 'N/A'}
          </p>
          {metrics?.total_score != null && (
            <p className="text-xs text-gray-500 mt-1">
              {metrics.total_score}/{metrics.max_possible_score} pts
            </p>
          )}
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Protocol Events</p>
          <p className="text-2xl font-bold text-gray-900">
            {metrics?.subscores ? Object.keys(metrics.subscores).length : 0}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Errors</p>
          <p className="text-2xl font-bold text-gray-900">
            {metrics?.protocol_errors?.length || 0}
          </p>
        </div>
      </div>

      {/* Actionable Feedback (PRD FR-5.5) */}
      {metrics?.feedback && metrics.feedback.length > 0 && (
        <div className="card mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Performance Feedback</h2>
          <div className="space-y-3">
            {metrics.feedback.map((item, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border ${getRatingStyle(item.rating)}`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg font-bold mt-0.5">{getRatingIcon(item.rating)}</span>
                  <div>
                    <p className="font-medium text-sm">
                      {item.criterion.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </p>
                    <p className="text-sm mt-1">{item.message}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Subscores Breakdown */}
      {metrics?.subscores && Object.keys(metrics.subscores).length > 0 && (
        <div className="card mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Score Breakdown</h2>
          <div className="space-y-3">
            {Object.entries(metrics.subscores).map(([criterion, data]) => (
              <div key={criterion} className="flex items-center gap-4">
                <span className="text-sm text-gray-700 w-48 truncate">
                  {criterion.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </span>
                <div className="flex-1 bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      data.points >= data.max ? 'bg-green-500'
                        : data.points > 0 ? 'bg-yellow-500'
                        : 'bg-red-400'
                    }`}
                    style={{ width: `${data.max > 0 ? (data.points / data.max) * 100 : 0}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900 w-20 text-right">
                  {data.points}/{data.max} pts
                </span>
                {data.time_seconds != null && (
                  <span className="text-xs text-gray-500 w-16 text-right">
                    @{data.time_seconds.toFixed(1)}s
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transcript with speaker labels and timestamps */}
      <div className="card">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Full Transcript</h2>
        <div className="space-y-4 max-h-[600px] overflow-y-auto">
          {transcript?.transcripts
            ? transcript.transcripts.map((entry: any) => (
                <div
                  key={entry.id}
                  className={`p-4 rounded-lg ${
                    entry.speaker === 'operator' ? 'bg-blue-50 ml-8' : 'bg-gray-100 mr-8'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm text-gray-700">
                      {entry.speaker === 'operator' ? 'Dispatcher' : 'Caller'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(entry.timestamp_ms)}
                    </span>
                  </div>
                  <p className="text-gray-900">{entry.text}</p>
                  {entry.emotional_state && (
                    <span className="text-xs text-gray-400 mt-1 inline-block">
                      Mood: {entry.emotional_state}
                    </span>
                  )}
                </div>
              ))
            : transcript?.segments
              ? transcript.segments.map((segment: any) => (
                  <div
                    key={segment.id}
                    className={`p-4 rounded-lg ${
                      segment.speaker === 'operator' ? 'bg-blue-50 ml-8' : 'bg-gray-100 mr-8'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-sm text-gray-700">
                        {segment.speaker === 'operator' ? 'Dispatcher' : 'Caller'}
                      </span>
                    </div>
                    <p className="text-gray-900">{segment.text}</p>
                  </div>
                ))
              : (
                <p className="text-gray-500">No transcript available</p>
              )}
        </div>
      </div>
    </div>
  );
};

export default CallReview;
