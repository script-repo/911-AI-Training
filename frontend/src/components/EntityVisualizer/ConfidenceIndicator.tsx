interface ConfidenceIndicatorProps {
  confidence: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const ConfidenceIndicator = ({
  confidence,
  size = 'md',
  showLabel = true,
}: ConfidenceIndicatorProps) => {
  const getColor = () => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getSize = () => {
    switch (size) {
      case 'sm':
        return 'w-12 h-12 text-xs';
      case 'lg':
        return 'w-20 h-20 text-xl';
      default:
        return 'w-16 h-16 text-base';
    }
  };

  const percentage = Math.round(confidence * 100);

  return (
    <div className="flex flex-col items-center space-y-1">
      <div
        className={`${getSize()} rounded-full ${getColor()} flex items-center justify-center font-bold transition-all duration-200`}
      >
        {percentage}%
      </div>
      {showLabel && (
        <span className="text-xs text-gray-600 font-medium">Confidence</span>
      )}
    </div>
  );
};

export default ConfidenceIndicator;
