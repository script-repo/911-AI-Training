import { useEffect, useRef, useState } from 'react';
import { useAudioStream } from '@/hooks/useAudioStream';

const AudioVisualizer = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const { getTimeDomainData, isRecording, volume } = useAudioStream();
  const [mode, setMode] = useState<'waveform' | 'level'>('waveform');

  useEffect(() => {
    if (!isRecording || !canvasRef.current) {
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const width = canvas.width;
      const height = canvas.height;

      // Clear canvas
      ctx.fillStyle = '#f3f4f6';
      ctx.fillRect(0, 0, width, height);

      if (mode === 'waveform') {
        // Draw waveform
        const dataArray = getTimeDomainData();
        const bufferLength = dataArray.length;

        ctx.lineWidth = 2;
        ctx.strokeStyle = '#3b82f6';
        ctx.beginPath();

        const sliceWidth = width / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const v = dataArray[i] / 128.0;
          const y = (v * height) / 2;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }

          x += sliceWidth;
        }

        ctx.lineTo(width, height / 2);
        ctx.stroke();
      } else {
        // Draw level meter
        const barWidth = 40;
        const barHeight = height * volume;
        const x = (width - barWidth) / 2;
        const y = height - barHeight;

        // Background bar
        ctx.fillStyle = '#e5e7eb';
        ctx.fillRect(x, 0, barWidth, height);

        // Volume level
        const gradient = ctx.createLinearGradient(0, height, 0, 0);
        gradient.addColorStop(0, '#22c55e');
        gradient.addColorStop(0.5, '#eab308');
        gradient.addColorStop(1, '#ef4444');
        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth, barHeight);

        // Border
        ctx.strokeStyle = '#9ca3af';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, 0, barWidth, height);

        // Level markers
        ctx.strokeStyle = '#6b7280';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 10; i++) {
          const markerY = (height / 10) * i;
          ctx.beginPath();
          ctx.moveTo(x - 5, markerY);
          ctx.lineTo(x, markerY);
          ctx.stroke();
        }

        // Volume text
        ctx.fillStyle = '#1f2937';
        ctx.font = '14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${Math.round(volume * 100)}%`, width / 2, height - 10);
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRecording, mode, getTimeDomainData, volume]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div
              className={`w-3 h-3 rounded-full ${
                isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-400'
              }`}
            />
            <span className="text-sm font-medium text-gray-700">
              {isRecording ? 'Recording' : 'Not Recording'}
            </span>
          </div>
          {isRecording && (
            <div className="text-sm text-gray-600">
              Level: {Math.round(volume * 100)}%
            </div>
          )}
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => setMode('waveform')}
            className={`px-3 py-1 text-sm rounded ${
              mode === 'waveform'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Waveform
          </button>
          <button
            onClick={() => setMode('level')}
            className={`px-3 py-1 text-sm rounded ${
              mode === 'level'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Level
          </button>
        </div>
      </div>

      <div className="bg-gray-100 rounded-lg overflow-hidden">
        <canvas
          ref={canvasRef}
          width={800}
          height={200}
          className="w-full"
          style={{ maxHeight: '200px' }}
        />
      </div>

      {!isRecording && (
        <div className="text-center py-8">
          <p className="text-gray-500 text-sm">
            Audio visualization will appear when call is active
          </p>
        </div>
      )}
    </div>
  );
};

export default AudioVisualizer;
