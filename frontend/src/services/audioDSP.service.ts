/**
 * Audio DSP service for telephone band-limiting and background noise.
 * Implements PRD FR-1.6: telephone band-pass filter (300-3400 Hz),
 * compression, and optional background noise injection for realism.
 */

export interface TelephoneFilterOptions {
  /** Enable telephone band-pass filter (300-3400 Hz) */
  bandPass: boolean;
  /** Enable dynamic compression */
  compression: boolean;
  /** Background noise type (null = no noise) */
  backgroundNoise: 'traffic' | 'sirens' | 'crowd' | 'wind' | null;
  /** Background noise volume (0.0 - 1.0) */
  noiseVolume: number;
}

const DEFAULT_OPTIONS: TelephoneFilterOptions = {
  bandPass: true,
  compression: true,
  backgroundNoise: null,
  noiseVolume: 0.1,
};

/**
 * Creates a telephone-quality audio processing chain on the given AudioContext.
 * Returns a { input, output } pair that can be connected into the Web Audio graph.
 */
export function createTelephoneFilter(
  ctx: AudioContext,
  options: Partial<TelephoneFilterOptions> = {}
): { input: AudioNode; output: AudioNode } {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  let head: AudioNode;
  let tail: AudioNode;

  // High-pass at 300 Hz (remove low rumble like a phone line)
  const highPass = ctx.createBiquadFilter();
  highPass.type = 'highpass';
  highPass.frequency.value = 300;
  highPass.Q.value = 0.7;

  // Low-pass at 3400 Hz (telephone bandwidth ceiling)
  const lowPass = ctx.createBiquadFilter();
  lowPass.type = 'lowpass';
  lowPass.frequency.value = 3400;
  lowPass.Q.value = 0.7;

  if (opts.bandPass) {
    highPass.connect(lowPass);
    head = highPass;
    tail = lowPass;
  } else {
    // Pass-through: just use a gain node
    const passthrough = ctx.createGain();
    passthrough.gain.value = 1.0;
    head = passthrough;
    tail = passthrough;
  }

  // Dynamic compressor for telephone-like loudness
  if (opts.compression) {
    const compressor = ctx.createDynamicsCompressor();
    compressor.threshold.value = -24;
    compressor.knee.value = 12;
    compressor.ratio.value = 4;
    compressor.attack.value = 0.003;
    compressor.release.value = 0.25;
    tail.connect(compressor);
    tail = compressor;
  }

  return { input: head, output: tail };
}

/**
 * Generates a simple noise buffer that can be used as ambient background.
 * Uses filtered white noise shaped to sound like distant environmental audio.
 */
export function createBackgroundNoiseSource(
  ctx: AudioContext,
  type: 'traffic' | 'sirens' | 'crowd' | 'wind',
  volume: number = 0.1
): { source: AudioBufferSourceNode; gain: GainNode } {
  // Create 2 seconds of white noise
  const bufferSize = ctx.sampleRate * 2;
  const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) {
    data[i] = Math.random() * 2 - 1;
  }

  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.loop = true;

  // Shape the noise based on type
  const filter = ctx.createBiquadFilter();
  switch (type) {
    case 'traffic':
      filter.type = 'lowpass';
      filter.frequency.value = 800;
      break;
    case 'sirens':
      filter.type = 'bandpass';
      filter.frequency.value = 1500;
      filter.Q.value = 2;
      break;
    case 'crowd':
      filter.type = 'bandpass';
      filter.frequency.value = 1000;
      filter.Q.value = 0.5;
      break;
    case 'wind':
      filter.type = 'lowpass';
      filter.frequency.value = 400;
      break;
  }

  const gain = ctx.createGain();
  gain.gain.value = Math.max(0, Math.min(1, volume));

  source.connect(filter);
  filter.connect(gain);

  return { source, gain };
}
