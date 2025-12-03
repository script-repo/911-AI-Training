import { SpeakerType } from '@/types';

interface SpeakerLabelsProps {
  activeSpeaker?: SpeakerType;
}

const SpeakerLabels = ({ activeSpeaker }: SpeakerLabelsProps) => {
  const speakers = [
    {
      type: SpeakerType.OPERATOR,
      label: 'Operator',
      icon: '👤',
      color: 'blue',
    },
    {
      type: SpeakerType.CALLER,
      label: 'Caller',
      icon: '📞',
      color: 'gray',
    },
  ];

  const getColorClasses = (color: string, isActive: boolean) => {
    const baseClasses = 'transition-all duration-200';
    if (isActive) {
      return `${baseClasses} bg-${color}-100 border-${color}-500 scale-105`;
    }
    return `${baseClasses} bg-${color}-50 border-${color}-200 opacity-60`;
  };

  return (
    <div className="flex items-center justify-center space-x-4 p-4 bg-white rounded-lg shadow-sm">
      <span className="text-sm font-medium text-gray-600">Active Speaker:</span>
      {speakers.map((speaker) => {
        const isActive = activeSpeaker === speaker.type;
        return (
          <div
            key={speaker.type}
            className={`flex items-center space-x-2 px-4 py-2 border-2 rounded-lg ${
              isActive
                ? speaker.color === 'blue'
                  ? 'bg-blue-100 border-blue-500 scale-105'
                  : 'bg-gray-100 border-gray-500 scale-105'
                : speaker.color === 'blue'
                ? 'bg-blue-50 border-blue-200 opacity-60'
                : 'bg-gray-50 border-gray-200 opacity-60'
            }`}
          >
            <span className="text-xl">{speaker.icon}</span>
            <span className="text-sm font-medium text-gray-700">{speaker.label}</span>
            {isActive && (
              <span className="flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default SpeakerLabels;
