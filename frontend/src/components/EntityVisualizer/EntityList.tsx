import { useEntityStore } from '@/stores/entityStore';
import { EntityType } from '@/types';
import ConfidenceIndicator from './ConfidenceIndicator';

const EntityList = () => {
  const { entities, highlightEntity, selectEntity } = useEntityStore();

  const getEntityIcon = (type: EntityType) => {
    const icons: Record<EntityType, string> = {
      [EntityType.LOCATION]: '📍',
      [EntityType.PERSON]: '👤',
      [EntityType.VEHICLE]: '🚗',
      [EntityType.WEAPON]: '⚠️',
      [EntityType.INJURY]: '🩹',
      [EntityType.MEDICAL_CONDITION]: '🏥',
      [EntityType.TIME]: '⏰',
      [EntityType.PHONE_NUMBER]: '📞',
      [EntityType.ADDRESS]: '🏠',
    };
    return icons[type] || '📋';
  };

  const getEntityColor = (type: EntityType) => {
    const colors: Record<EntityType, string> = {
      [EntityType.LOCATION]: 'bg-blue-50 border-blue-200 text-blue-800',
      [EntityType.PERSON]: 'bg-purple-50 border-purple-200 text-purple-800',
      [EntityType.VEHICLE]: 'bg-green-50 border-green-200 text-green-800',
      [EntityType.WEAPON]: 'bg-red-50 border-red-200 text-red-800',
      [EntityType.INJURY]: 'bg-orange-50 border-orange-200 text-orange-800',
      [EntityType.MEDICAL_CONDITION]: 'bg-pink-50 border-pink-200 text-pink-800',
      [EntityType.TIME]: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      [EntityType.PHONE_NUMBER]: 'bg-indigo-50 border-indigo-200 text-indigo-800',
      [EntityType.ADDRESS]: 'bg-teal-50 border-teal-200 text-teal-800',
    };
    return colors[type] || 'bg-gray-50 border-gray-200 text-gray-800';
  };

  const formatEntityType = (type: EntityType) => {
    return type
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  const groupedEntities = entities?.entities.reduce((acc, entity) => {
    if (!acc[entity.type]) {
      acc[entity.type] = [];
    }
    acc[entity.type].push(entity);
    return acc;
  }, {} as Record<EntityType, typeof entities.entities>);

  if (!entities || entities.entities.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-400 mb-3">
          <svg
            className="w-12 h-12 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <p className="text-gray-500 text-sm">No entities extracted yet</p>
        <p className="text-xs text-gray-400 mt-1">
          Information will be extracted from the conversation
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto">
      {Object.entries(groupedEntities || {}).map(([type, items]) => (
        <div key={type}>
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center space-x-2">
            <span>{getEntityIcon(type as EntityType)}</span>
            <span>{formatEntityType(type as EntityType)}</span>
            <span className="text-xs text-gray-500">({items.length})</span>
          </h3>
          <div className="space-y-2">
            {items.map((entity) => (
              <div
                key={entity.id}
                className={`p-3 border rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md ${getEntityColor(
                  entity.type
                )}`}
                onMouseEnter={() => highlightEntity(entity.id)}
                onMouseLeave={() => highlightEntity(null)}
                onClick={() => selectEntity(entity)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{entity.value}</p>
                    {entity.metadata && Object.keys(entity.metadata).length > 0 && (
                      <div className="mt-1 text-xs space-y-0.5">
                        {Object.entries(entity.metadata).map(([key, value]) => (
                          <div key={key} className="flex items-center space-x-1">
                            <span className="text-gray-600">{key}:</span>
                            <span className="font-medium">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <ConfidenceIndicator confidence={entity.confidence} size="sm" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Summary */}
      <div className="pt-4 border-t">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-gray-700">Total Entities:</span>
          <span className="font-bold text-gray-900">{entities.entities.length}</span>
        </div>
      </div>
    </div>
  );
};

export default EntityList;
