import { create } from 'zustand';
import { Entity, EntityType, ExtractedEntities } from '@/types';

interface EntityState {
  entities: ExtractedEntities | null;
  selectedEntity: Entity | null;
  highlightedEntityId: string | null;

  // Actions
  setEntities: (entities: Entity[], callId: string) => void;
  addEntity: (entity: Entity) => void;
  updateEntity: (entityId: string, updates: Partial<Entity>) => void;
  removeEntity: (entityId: string) => void;
  selectEntity: (entity: Entity | null) => void;
  highlightEntity: (entityId: string | null) => void;
  getEntitiesByType: (type: EntityType) => Entity[];
  clearEntities: () => void;
}

export const useEntityStore = create<EntityState>((set, get) => ({
  entities: null,
  selectedEntity: null,
  highlightedEntityId: null,

  setEntities: (entities, callId) => {
    set({
      entities: {
        callId,
        entities,
        updatedAt: new Date(),
      },
    });
  },

  addEntity: (entity) => {
    const { entities } = get();
    if (entities) {
      set({
        entities: {
          ...entities,
          entities: [...entities.entities, entity],
          updatedAt: new Date(),
        },
      });
    }
  },

  updateEntity: (entityId, updates) => {
    const { entities } = get();
    if (entities) {
      set({
        entities: {
          ...entities,
          entities: entities.entities.map((e) =>
            e.id === entityId ? { ...e, ...updates } : e
          ),
          updatedAt: new Date(),
        },
      });
    }
  },

  removeEntity: (entityId) => {
    const { entities } = get();
    if (entities) {
      set({
        entities: {
          ...entities,
          entities: entities.entities.filter((e) => e.id !== entityId),
          updatedAt: new Date(),
        },
      });
    }
  },

  selectEntity: (entity) => {
    set({ selectedEntity: entity });
  },

  highlightEntity: (entityId) => {
    set({ highlightedEntityId: entityId });
  },

  getEntitiesByType: (type) => {
    const { entities } = get();
    if (!entities) return [];
    return entities.entities.filter((e) => e.type === type);
  },

  clearEntities: () => {
    set({
      entities: null,
      selectedEntity: null,
      highlightedEntityId: null,
    });
  },
}));
