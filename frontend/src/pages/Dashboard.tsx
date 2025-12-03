import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCallStore } from '@/stores/callStore';
import { useCallSession } from '@/hooks/useCallSession';
import { CallStatus } from '@/types';
import CallControls from '@/components/CallTakerDashboard/CallControls';
import CallStatus from '@/components/CallTakerDashboard/CallStatus';
import EmergencyActions from '@/components/CallTakerDashboard/EmergencyActions';
import AudioVisualizer from '@/components/AudioProcessor/AudioVisualizer';
import TranscriptView from '@/components/LiveTranscript/TranscriptView';
import EntityList from '@/components/EntityVisualizer/EntityList';

const Dashboard = () => {
  const navigate = useNavigate();
  const { currentCall } = useCallStore();
  const { endCall } = useCallSession();

  useEffect(() => {
    // Redirect if no active call
    if (!currentCall || currentCall.status === CallStatus.ENDED) {
      navigate('/scenarios');
    }
  }, [currentCall, navigate]);

  const handleEndCall = async () => {
    try {
      await endCall();
      navigate('/history');
    } catch (error) {
      console.error('Failed to end call:', error);
    }
  };

  if (!currentCall) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-gray-600">No active call. Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1920px] mx-auto">
      {/* Top Section - Call Status and Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <CallStatus />
        </div>
        <div>
          <CallControls onEndCall={handleEndCall} />
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left Column - Transcript and Audio */}
        <div className="xl:col-span-2 space-y-6">
          {/* Audio Visualizer */}
          <div className="card">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Audio Monitor</h2>
            <AudioVisualizer />
          </div>

          {/* Transcript */}
          <div className="card">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Live Transcript</h2>
            <TranscriptView />
          </div>
        </div>

        {/* Right Column - Entities and Actions */}
        <div className="space-y-6">
          {/* Emergency Actions */}
          <EmergencyActions />

          {/* Extracted Entities */}
          <div className="card">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Extracted Information</h2>
            <EntityList />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
