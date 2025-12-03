# 911 Operator Training Simulator - Frontend

A modern React + TypeScript frontend application for the 911 Operator Training Simulator with real-time audio streaming, live transcription, and entity extraction visualization.

## Features

- **Real-time Audio Streaming**: WebRTC-based audio capture with Web Audio API
- **Live Transcription**: Real-time speech-to-text display with speaker differentiation
- **Entity Extraction**: Visual highlighting of extracted entities (locations, persons, weapons, etc.)
- **Call Controls**: Mute, hold, transfer, and terminate call functionality
- **Audio Visualization**: Real-time waveform and volume level display
- **Scenario Selection**: Choose from predefined training scenarios
- **Call History**: Review past training sessions with metrics and scores
- **WebSocket Communication**: Bi-directional real-time communication with backend
- **Responsive Design**: Mobile-friendly layout with Tailwind CSS

## Tech Stack

- **React 18** with TypeScript
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Zustand** - Lightweight state management
- **React Query** - Server state management
- **React Router** - Client-side routing
- **Web Audio API** - Audio processing and visualization
- **WebSocket** - Real-time communication
- **Axios** - HTTP client

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── CallTakerDashboard/
│   │   │   ├── CallControls.tsx
│   │   │   ├── CallStatus.tsx
│   │   │   └── EmergencyActions.tsx
│   │   ├── AudioProcessor/
│   │   │   ├── AudioVisualizer.tsx
│   │   │   └── MicrophoneInput.tsx
│   │   ├── LiveTranscript/
│   │   │   ├── TranscriptView.tsx
│   │   │   └── SpeakerLabels.tsx
│   │   ├── EntityVisualizer/
│   │   │   ├── EntityList.tsx
│   │   │   ├── EntityHighlight.tsx
│   │   │   └── ConfidenceIndicator.tsx
│   │   └── Layout.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── ScenarioSelection.tsx
│   │   ├── CallHistory.tsx
│   │   └── CallReview.tsx
│   ├── services/
│   │   ├── websocket.service.ts
│   │   ├── audio.service.ts
│   │   └── api.service.ts
│   ├── stores/
│   │   ├── callStore.ts
│   │   ├── entityStore.ts
│   │   └── connectionStore.ts
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useAudioStream.ts
│   │   ├── useCallSession.ts
│   │   └── useTranscript.ts
│   ├── types/
│   │   └── index.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── package.json
├── nginx.conf
└── Dockerfile
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Update `.env` with your backend URLs:
```env
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

### Building for Production

Build the application:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

### Docker Deployment

Build the Docker image:
```bash
docker build -t 911-operator-frontend .
```

Run the container:
```bash
docker run -p 80:80 911-operator-frontend
```

## Key Features Implementation

### WebSocket Communication

The application uses a WebSocket service with automatic reconnection logic:
- Heartbeat/ping mechanism to keep connection alive
- Exponential backoff for reconnection attempts
- Connection state management with Zustand

### Audio Streaming

Audio is captured using the Web Audio API:
- 16kHz sample rate, mono channel
- Real-time conversion to Int16 PCM format
- Chunked streaming via WebSocket
- Visual feedback with waveform and level meters

### State Management

Three main stores manage application state:
- **callStore**: Current call state, transcript, and call controls
- **entityStore**: Extracted entities with highlighting
- **connectionStore**: WebSocket connection status

### Custom Hooks

Reusable hooks encapsulate complex logic:
- **useWebSocket**: WebSocket connection and messaging
- **useAudioStream**: Audio capture and processing
- **useCallSession**: Complete call lifecycle management
- **useTranscript**: Transcript data access and search

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| VITE_API_URL | Backend API URL | http://localhost:8000/api |
| VITE_WS_URL | WebSocket URL | ws://localhost:8000/ws |
| VITE_ENV | Environment | development |
| VITE_ENABLE_DEBUG_MODE | Enable debug logging | true |
| VITE_AUDIO_SAMPLE_RATE | Audio sample rate | 16000 |
| VITE_AUDIO_CHANNELS | Audio channels | 1 |

### Nginx Configuration

The included `nginx.conf` provides:
- SPA routing support
- API and WebSocket proxying
- Static file caching
- Gzip compression
- Security headers

## Browser Requirements

- Modern browser with WebRTC support
- Microphone access permission
- WebSocket support
- ES2020+ JavaScript support

### Recommended Browsers

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development Tips

### Hot Module Replacement

Vite provides instant HMR. Changes to React components will reflect immediately without full page reload.

### TypeScript

All code is fully typed. Run type checking:
```bash
npm run build
```

### Linting

Lint the codebase:
```bash
npm run lint
```

## Troubleshooting

### Microphone Access Issues

If microphone access is denied:
1. Check browser permissions in settings
2. Ensure HTTPS in production (required for getUserMedia)
3. Check console for specific error messages

### WebSocket Connection Issues

If WebSocket fails to connect:
1. Verify backend is running
2. Check VITE_WS_URL environment variable
3. Inspect browser console for connection errors
4. Verify CORS configuration on backend

### Audio Not Streaming

If audio capture works but doesn't stream:
1. Check WebSocket connection status
2. Verify call is in ACTIVE state
3. Check browser console for errors
4. Ensure backend WebSocket handler is working

## Performance Optimization

The application includes several optimizations:
- Code splitting with dynamic imports
- Lazy loading of routes
- React.memo for expensive components
- Debounced audio chunk streaming
- Efficient re-renders with Zustand

## Security Considerations

- API calls include authentication tokens
- WebSocket connections validate sessions
- XSS protection via React's built-in escaping
- CSRF tokens for state-changing operations
- Content Security Policy headers via Nginx

## Contributing

1. Follow TypeScript best practices
2. Use functional components with hooks
3. Implement proper error boundaries
4. Write meaningful component names
5. Keep components small and focused
6. Document complex logic with comments

## License

Copyright © 2025 911 Operator Training Simulator
