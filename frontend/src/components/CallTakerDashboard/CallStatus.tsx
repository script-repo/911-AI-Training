import { useEffect, useState } from 'react';
import { useCallStore } from '@/stores/callStore';
import { CallStatus as CallStatusEnum, CallPriority } from '@/types';
import { format } from 'date-fns';

const CallStatus = () => {
  const { currentCall } = useCallStore();
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    if (!currentCall || currentCall.status !== CallStatusEnum.ACTIVE) {
      return;
    }

    const interval = setInterval(() => {
      const elapsed = Math.floor(
        (Date.now() - new Date(currentCall.startTime).getTime()) / 1000
      );
      setElapsedTime(elapsed);
    }, 1000);

    return () => clearInterval(interval);
  }, [currentCall]);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs
        .toString()
        .padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: CallStatusEnum) => {
    switch (status) {
      case CallStatusEnum.ACTIVE:
        return 'bg-green-500';
      case CallStatusEnum.ON_HOLD:
        return 'bg-yellow-500';
      case CallStatusEnum.CONNECTING:
        return 'bg-blue-500';
      case CallStatusEnum.ERROR:
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getPriorityColor = (priority: CallPriority) => {
    switch (priority) {
      case CallPriority.CRITICAL:
        return 'bg-red-100 text-red-800 border-red-300';
      case CallPriority.HIGH:
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case CallPriority.MEDIUM:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case CallPriority.LOW:
        return 'bg-green-100 text-green-800 border-green-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (!currentCall) {
    return (
      <div className="card">
        <p className="text-gray-500">No active call</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div
            className={`w-4 h-4 rounded-full ${getStatusColor(
              currentCall.status
            )} animate-pulse`}
          />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Active Call</h2>
            <p className="text-sm text-gray-600">
              Call ID: {currentCall.id.slice(0, 8)}...
            </p>
          </div>
        </div>
        <div
          className={`px-4 py-2 border-2 rounded-lg font-semibold ${getPriorityColor(
            currentCall.priority
          )}`}
        >
          {currentCall.priority.toUpperCase()} PRIORITY
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div>
          <p className="text-sm text-gray-600 mb-1">Call Duration</p>
          <p className="text-3xl font-bold text-gray-900 tabular-nums">
            {formatTime(elapsedTime)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600 mb-1">Started At</p>
          <p className="text-lg font-semibold text-gray-900">
            {format(new Date(currentCall.startTime), 'HH:mm:ss')}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600 mb-1">Status</p>
          <p className="text-lg font-semibold text-gray-900 capitalize">
            {currentCall.status.replace('_', ' ')}
          </p>
        </div>
      </div>

      {currentCall.scenarioId && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm text-gray-600">Training Scenario Active</p>
        </div>
      )}
    </div>
  );
};

export default CallStatus;
