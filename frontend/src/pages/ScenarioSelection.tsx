import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiService } from '@/services/api.service';
import { useCallSession } from '@/hooks/useCallSession';
import { Scenario } from '@/types';
import { useState } from 'react';

const ScenarioSelection = () => {
  const navigate = useNavigate();
  const { startCall } = useCallSession();
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading, error: queryError } = useQuery({
    queryKey: ['scenarios'],
    queryFn: async () => {
      const response = await apiService.getScenarios();
      if (!response.success) {
        throw new Error(response.error || 'Failed to load scenarios');
      }
      return response.data || [];
    },
  });

  const handleStartScenario = async (scenario: Scenario) => {
    setIsStarting(true);
    setError(null);

    try {
      await startCall(scenario.id);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start scenario');
    } finally {
      setIsStarting(false);
    }
  };

  const handleStartFreeCall = async () => {
    setIsStarting(true);
    setError(null);

    try {
      await startCall();
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start call');
    } finally {
      setIsStarting(false);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'hard':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading scenarios...</p>
        </div>
      </div>
    );
  }

  if (queryError) {
    return (
      <div className="card border-l-4 border-red-500">
        <h2 className="text-xl font-bold text-red-600 mb-2">Error Loading Scenarios</h2>
        <p className="text-gray-600">{queryError.message}</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Training Scenarios</h1>
        <p className="text-gray-600">
          Select a scenario to begin your training session or start a free-form call.
        </p>
      </div>

      {error && (
        <div className="card border-l-4 border-red-500 mb-6">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Free Call Option */}
      <div className="card mb-8 border-2 border-blue-500">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Free Call Mode</h3>
            <p className="text-gray-600">
              Practice without a predefined scenario. The AI will respond to any emergency
              situation you present.
            </p>
          </div>
          <button
            onClick={handleStartFreeCall}
            disabled={isStarting}
            className="btn btn-primary px-8"
          >
            {isStarting ? 'Starting...' : 'Start Free Call'}
          </button>
        </div>
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data?.map((scenario) => (
          <div
            key={scenario.id}
            className="card hover:shadow-xl transition-shadow duration-200"
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-bold text-gray-900">{scenario.name}</h3>
              <span
                className={`px-2 py-1 text-xs font-semibold rounded ${getDifficultyColor(
                  scenario.difficulty
                )}`}
              >
                {scenario.difficulty.toUpperCase()}
              </span>
            </div>

            <p className="text-sm text-gray-600 mb-4 line-clamp-3">
              {scenario.description}
            </p>

            <div className="mb-4">
              <p className="text-xs text-gray-500 mb-2">Category: {scenario.category}</p>
              <p className="text-xs text-gray-500">
                Duration: ~{scenario.estimatedDuration} minutes
              </p>
            </div>

            {scenario.objectives && scenario.objectives.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-gray-700 mb-2">Objectives:</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  {scenario.objectives.slice(0, 3).map((obj, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-blue-600 mr-2">•</span>
                      <span className="line-clamp-1">{obj}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <button
              onClick={() => handleStartScenario(scenario)}
              disabled={isStarting}
              className="btn btn-primary w-full"
            >
              {isStarting ? 'Starting...' : 'Start Scenario'}
            </button>
          </div>
        ))}
      </div>

      {data && data.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-gray-600">No scenarios available at the moment.</p>
          <p className="text-sm text-gray-500 mt-2">Try starting a free call instead.</p>
        </div>
      )}
    </div>
  );
};

export default ScenarioSelection;
