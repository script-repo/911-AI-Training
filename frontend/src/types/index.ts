// Call-related types
export enum CallStatus {
  IDLE = 'idle',
  CONNECTING = 'connecting',
  ACTIVE = 'active',
  ON_HOLD = 'on_hold',
  ENDED = 'ended',
  ERROR = 'error',
}

export enum CallPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export interface Call {
  id: string;
  sessionId: string;
  status: CallStatus;
  priority: CallPriority;
  startTime: Date;
  endTime?: Date;
  duration: number;
  operatorId: string;
  scenarioId?: string;
}

// Transcript types
export enum SpeakerType {
  OPERATOR = 'operator',
  CALLER = 'caller',
  SYSTEM = 'system',
}

export interface TranscriptSegment {
  id: string;
  speaker: SpeakerType;
  text: string;
  timestamp: Date;
  confidence?: number;
  isFinal: boolean;
}

export interface Transcript {
  callId: string;
  segments: TranscriptSegment[];
  updatedAt: Date;
}

// Entity types
export enum EntityType {
  LOCATION = 'location',
  PERSON = 'person',
  VEHICLE = 'vehicle',
  WEAPON = 'weapon',
  INJURY = 'injury',
  MEDICAL_CONDITION = 'medical_condition',
  TIME = 'time',
  PHONE_NUMBER = 'phone_number',
  ADDRESS = 'address',
}

export interface Entity {
  id: string;
  type: EntityType;
  value: string;
  confidence: number;
  segmentId: string;
  startIndex: number;
  endIndex: number;
  metadata?: Record<string, unknown>;
}

export interface ExtractedEntities {
  callId: string;
  entities: Entity[];
  updatedAt: Date;
}

// Audio types
export interface AudioConfig {
  sampleRate: number;
  channels: number;
  bitsPerSample: number;
  codec: 'pcm' | 'opus';
}

export interface AudioChunk {
  data: ArrayBuffer;
  timestamp: number;
  sequenceNumber: number;
}

// WebSocket message types
export enum WSMessageType {
  CALL_START = 'call_start',
  CALL_END = 'call_end',
  AUDIO_CHUNK = 'audio_chunk',
  TRANSCRIPT_UPDATE = 'transcript_update',
  ENTITY_UPDATE = 'entity_update',
  STATUS_UPDATE = 'status_update',
  ERROR = 'error',
  PING = 'ping',
  PONG = 'pong',
}

export interface WSMessage {
  type: WSMessageType;
  payload: unknown;
  timestamp: number;
  callId?: string;
}

export interface CallStartPayload {
  callId: string;
  sessionId: string;
  scenarioId?: string;
  audioConfig: AudioConfig;
}

export interface TranscriptUpdatePayload {
  callId: string;
  segment: TranscriptSegment;
}

export interface EntityUpdatePayload {
  callId: string;
  entities: Entity[];
}

export interface StatusUpdatePayload {
  callId: string;
  status: CallStatus;
  message?: string;
}

// Scenario types
export interface Scenario {
  id: string;
  name: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: string;
  estimatedDuration: number;
  objectives: string[];
}

// Metrics types
export interface CallMetrics {
  callId: string;
  responseTime: number;
  callDuration: number;
  entitiesExtracted: number;
  accuracy: number;
  completionRate: number;
  criticalInfoGathered: string[];
  missedInformation: string[];
  score: number;
}

// WebSocket connection types
export enum ConnectionStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

export interface ConnectionState {
  status: ConnectionStatus;
  lastConnected?: Date;
  reconnectAttempts: number;
  error?: string;
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// User types
export interface User {
  id: string;
  username: string;
  email: string;
  role: 'operator' | 'admin' | 'trainee';
  firstName?: string;
  lastName?: string;
}

// Call history types
export interface CallHistoryItem {
  id: string;
  callId: string;
  sessionId: string;
  scenarioName?: string;
  startTime: Date;
  endTime: Date;
  duration: number;
  status: CallStatus;
  metrics?: CallMetrics;
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: Date;
}
