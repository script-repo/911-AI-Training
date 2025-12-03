import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiService } from '@/services/api.service';
import { CallStatus } from '@/types';
import { format } from 'date-fns';

const CallHistory = () => {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, error } = useQuery({
    queryKey: ['callHistory', page],
    queryFn: async () => {
      const response = await apiService.getCallHistory(page, pageSize);
      if (!response.success) {
        throw new Error(response.error || 'Failed to load call history');
      }
      return response.data;
    },
  });

  const getStatusColor = (status: CallStatus) => {
    switch (status) {
      case CallStatus.ENDED:
        return 'bg-gray-100 text-gray-800';
      case CallStatus.ACTIVE:
        return 'bg-green-100 text-green-800';
      case CallStatus.ERROR:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading call history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card border-l-4 border-red-500">
        <h2 className="text-xl font-bold text-red-600 mb-2">Error Loading Call History</h2>
        <p className="text-gray-600">{error.message}</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Call History</h1>
        <p className="text-gray-600">Review your past training sessions and performance.</p>
      </div>

      {data && data.items.length > 0 ? (
        <>
          {/* Table */}
          <div className="card overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date & Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Scenario
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.items.map((call) => (
                    <tr key={call.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {format(new Date(call.startTime), 'MMM dd, yyyy HH:mm')}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {call.scenarioName || 'Free Call'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDuration(call.duration)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded ${getStatusColor(
                            call.status
                          )}`}
                        >
                          {call.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {call.metrics ? (
                          <span className="font-semibold">{call.metrics.score}%</span>
                        ) : (
                          <span className="text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <Link
                          to={`/review/${call.callId}`}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          View Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {data.hasMore && (
            <div className="flex justify-center mt-6 space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-gray-700">
                Page {page} of {Math.ceil(data.total / pageSize)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!data.hasMore}
                className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-600 mb-4">No call history available yet.</p>
          <Link to="/scenarios" className="btn btn-primary">
            Start Your First Call
          </Link>
        </div>
      )}
    </div>
  );
};

export default CallHistory;
