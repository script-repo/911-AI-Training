import { AudioConfig, AudioChunk } from '@/types';

export type AudioDataCallback = (chunk: AudioChunk) => void;

class AudioService {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private processorNode: ScriptProcessorNode | null = null;
  private analyserNode: AnalyserNode | null = null;
  private isRecording = false;
  private sequenceNumber = 0;
  private audioDataCallback: AudioDataCallback | null = null;

  private config: AudioConfig = {
    sampleRate: 16000,
    channels: 1,
    bitsPerSample: 16,
    codec: 'pcm',
  };

  async initialize(config?: Partial<AudioConfig>): Promise<void> {
    if (config) {
      this.config = { ...this.config, ...config };
    }

    try {
      // Create audio context
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: this.config.sampleRate,
      });

      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.config.sampleRate,
          channelCount: this.config.channels,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Create audio nodes
      this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);

      // Create analyser for visualization
      this.analyserNode = this.audioContext.createAnalyser();
      this.analyserNode.fftSize = 2048;
      this.analyserNode.smoothingTimeConstant = 0.8;

      // Create processor for capturing audio data
      const bufferSize = 4096;
      this.processorNode = this.audioContext.createScriptProcessor(
        bufferSize,
        this.config.channels,
        this.config.channels
      );

      this.processorNode.onaudioprocess = (e) => {
        if (!this.isRecording || !this.audioDataCallback) return;

        const inputData = e.inputBuffer.getChannelData(0);
        const audioData = this.convertToInt16(inputData);

        const chunk: AudioChunk = {
          data: audioData.buffer,
          timestamp: Date.now(),
          sequenceNumber: this.sequenceNumber++,
        };

        this.audioDataCallback(chunk);
      };

      // Connect nodes
      this.sourceNode.connect(this.analyserNode);
      this.sourceNode.connect(this.processorNode);
      this.processorNode.connect(this.audioContext.destination);

      console.log('Audio service initialized');
    } catch (error) {
      console.error('Failed to initialize audio service:', error);
      throw new Error('Microphone access denied or not available');
    }
  }

  startRecording(callback: AudioDataCallback): void {
    if (!this.audioContext || !this.processorNode) {
      throw new Error('Audio service not initialized');
    }

    this.audioDataCallback = callback;
    this.isRecording = true;
    this.sequenceNumber = 0;

    if (this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }

    console.log('Recording started');
  }

  stopRecording(): void {
    this.isRecording = false;
    this.audioDataCallback = null;
    console.log('Recording stopped');
  }

  getAnalyserNode(): AnalyserNode | null {
    return this.analyserNode;
  }

  getFrequencyData(): Uint8Array {
    if (!this.analyserNode) {
      return new Uint8Array(0);
    }

    const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);
    this.analyserNode.getByteFrequencyData(dataArray);
    return dataArray;
  }

  getTimeDomainData(): Uint8Array {
    if (!this.analyserNode) {
      return new Uint8Array(0);
    }

    const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);
    this.analyserNode.getByteTimeDomainData(dataArray);
    return dataArray;
  }

  getVolume(): number {
    if (!this.analyserNode) return 0;

    const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);
    this.analyserNode.getByteFrequencyData(dataArray);

    const sum = dataArray.reduce((acc, val) => acc + val, 0);
    const average = sum / dataArray.length;
    return average / 255; // Normalize to 0-1
  }

  async cleanup(): Promise<void> {
    this.stopRecording();

    if (this.processorNode) {
      this.processorNode.disconnect();
      this.processorNode = null;
    }

    if (this.analyserNode) {
      this.analyserNode.disconnect();
      this.analyserNode = null;
    }

    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }

    console.log('Audio service cleaned up');
  }

  isInitialized(): boolean {
    return this.audioContext !== null && this.mediaStream !== null;
  }

  isActive(): boolean {
    return this.isRecording;
  }

  getConfig(): AudioConfig {
    return { ...this.config };
  }

  private convertToInt16(float32Array: Float32Array): Int16Array {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return int16Array;
  }

  // Playback methods for received audio
  async playAudio(audioData: ArrayBuffer): Promise<void> {
    if (!this.audioContext) {
      throw new Error('Audio service not initialized');
    }

    try {
      const audioBuffer = await this.audioContext.decodeAudioData(audioData);
      const sourceNode = this.audioContext.createBufferSource();
      sourceNode.buffer = audioBuffer;
      sourceNode.connect(this.audioContext.destination);
      sourceNode.start();
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  }
}

// Singleton instance
export const audioService = new AudioService();
export default audioService;
