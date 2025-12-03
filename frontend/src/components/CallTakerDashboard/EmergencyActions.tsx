import { useState } from 'react';

const EmergencyActions = () => {
  const [dispatched, setDispatched] = useState<string[]>([]);

  const emergencyServices = [
    { id: 'police', name: 'Police', icon: '🚔', color: 'blue' },
    { id: 'fire', name: 'Fire Department', icon: '🚒', color: 'red' },
    { id: 'ems', name: 'EMS/Ambulance', icon: '🚑', color: 'green' },
    { id: 'rescue', name: 'Rescue Team', icon: '⛑️', color: 'orange' },
  ];

  const handleDispatch = (serviceId: string) => {
    if (dispatched.includes(serviceId)) {
      setDispatched(dispatched.filter((id) => id !== serviceId));
    } else {
      setDispatched([...dispatched, serviceId]);
    }
  };

  const getButtonStyle = (serviceId: string, color: string) => {
    const isDispatched = dispatched.includes(serviceId);
    const colorMap: Record<string, string> = {
      blue: isDispatched
        ? 'bg-blue-600 text-white border-blue-700'
        : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
      red: isDispatched
        ? 'bg-red-600 text-white border-red-700'
        : 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100',
      green: isDispatched
        ? 'bg-green-600 text-white border-green-700'
        : 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100',
      orange: isDispatched
        ? 'bg-orange-600 text-white border-orange-700'
        : 'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100',
    };
    return colorMap[color] || colorMap.blue;
  };

  return (
    <div className="card">
      <h2 className="text-lg font-bold text-gray-900 mb-4">Emergency Services</h2>
      <p className="text-sm text-gray-600 mb-4">
        Quick dispatch actions for emergency services
      </p>

      <div className="space-y-3">
        {emergencyServices.map((service) => {
          const isDispatched = dispatched.includes(service.id);
          return (
            <button
              key={service.id}
              onClick={() => handleDispatch(service.id)}
              className={`w-full p-4 border-2 rounded-lg transition-all duration-200 ${getButtonStyle(
                service.id,
                service.color
              )}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{service.icon}</span>
                  <span className="font-semibold">{service.name}</span>
                </div>
                {isDispatched && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">Dispatched</span>
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {dispatched.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm text-gray-700 font-medium">
            {dispatched.length} service{dispatched.length !== 1 ? 's' : ''} dispatched
          </p>
        </div>
      )}
    </div>
  );
};

export default EmergencyActions;
