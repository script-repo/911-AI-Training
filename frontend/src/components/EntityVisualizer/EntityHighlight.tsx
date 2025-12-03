import { useMemo } from 'react';
import { useEntityStore } from '@/stores/entityStore';
import { EntityType } from '@/types';

interface EntityHighlightProps {
  text: string;
  segmentId: string;
}

const EntityHighlight = ({ text, segmentId }: EntityHighlightProps) => {
  const { entities, highlightEntity } = useEntityStore();

  const getEntityColor = (type: EntityType) => {
    const colors: Record<EntityType, string> = {
      [EntityType.LOCATION]: 'bg-blue-200 text-blue-900',
      [EntityType.PERSON]: 'bg-purple-200 text-purple-900',
      [EntityType.VEHICLE]: 'bg-green-200 text-green-900',
      [EntityType.WEAPON]: 'bg-red-200 text-red-900',
      [EntityType.INJURY]: 'bg-orange-200 text-orange-900',
      [EntityType.MEDICAL_CONDITION]: 'bg-pink-200 text-pink-900',
      [EntityType.TIME]: 'bg-yellow-200 text-yellow-900',
      [EntityType.PHONE_NUMBER]: 'bg-indigo-200 text-indigo-900',
      [EntityType.ADDRESS]: 'bg-teal-200 text-teal-900',
    };
    return colors[type] || 'bg-gray-200 text-gray-900';
  };

  const highlightedText = useMemo(() => {
    if (!entities || entities.entities.length === 0) {
      return <span>{text}</span>;
    }

    // Get entities for this segment
    const segmentEntities = entities.entities.filter(
      (e) => e.segmentId === segmentId
    );

    if (segmentEntities.length === 0) {
      return <span>{text}</span>;
    }

    // Sort entities by start index to process them in order
    const sortedEntities = [...segmentEntities].sort(
      (a, b) => a.startIndex - b.startIndex
    );

    const parts: JSX.Element[] = [];
    let lastIndex = 0;

    sortedEntities.forEach((entity, idx) => {
      // Add text before entity
      if (entity.startIndex > lastIndex) {
        parts.push(
          <span key={`text-${idx}`}>{text.slice(lastIndex, entity.startIndex)}</span>
        );
      }

      // Add highlighted entity
      parts.push(
        <span
          key={`entity-${entity.id}`}
          className={`px-1 py-0.5 rounded cursor-pointer transition-all duration-200 ${getEntityColor(
            entity.type
          )} hover:shadow-md`}
          onMouseEnter={() => highlightEntity(entity.id)}
          onMouseLeave={() => highlightEntity(null)}
          title={`${entity.type} (${Math.round(entity.confidence * 100)}% confidence)`}
        >
          {text.slice(entity.startIndex, entity.endIndex)}
        </span>
      );

      lastIndex = entity.endIndex;
    });

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(<span key="text-end">{text.slice(lastIndex)}</span>);
    }

    return <>{parts}</>;
  }, [text, entities, segmentId, highlightEntity]);

  return <div className="leading-relaxed">{highlightedText}</div>;
};

export default EntityHighlight;
