/**
 * Dynamic retro/cyber synthesizer service using Web Audio API.
 * Synthesizes all sound effects in code to avoid loading audio assets.
 */
class SoundManager {
  private ctx: AudioContext | null = null;

  /** Initialize or fetch the active audio context. */
  private getContext(): AudioContext | null {
    if (!this.ctx) {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioContextClass) {
        this.ctx = new AudioContextClass();
      }
    }
    // Resume context if suspended (browser security policy restriction)
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  /** Play a crisp futuristic UI click sound. */
  playClick() {
    const ctx = this.getContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(900, now);
    osc.frequency.exponentialRampToValueAtTime(150, now + 0.05);

    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.05);
  }

  /** Play a sci-fi laser shooting sound. */
  playShoot(isSelf: boolean) {
    const ctx = this.getContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = isSelf ? "triangle" : "sine";
    const startFreq = isSelf ? 880 : 550;
    const endFreq = isSelf ? 110 : 80;
    const duration = isSelf ? 0.12 : 0.09;
    const volume = isSelf ? 0.1 : 0.025;

    osc.frequency.setValueAtTime(startFreq, now);
    osc.frequency.exponentialRampToValueAtTime(endFreq, now + duration);

    gain.gain.setValueAtTime(volume, now);
    gain.gain.linearRampToValueAtTime(0.001, now + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + duration);
  }

  /** Play a crisp high-frequency chirp when hitting an opponent. */
  playHitmarker() {
    const ctx = this.getContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "triangle";
    osc.frequency.setValueAtTime(1800, now);
    osc.frequency.exponentialRampToValueAtTime(2400, now + 0.04);

    gain.gain.setValueAtTime(0.07, now);
    gain.gain.linearRampToValueAtTime(0.001, now + 0.04);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.04);
  }

  /** Play a heavy distorted damage sound when the local player is hurt. */
  playHurt() {
    const ctx = this.getContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const osc2 = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(180, now);
    osc.frequency.linearRampToValueAtTime(50, now + 0.18);

    osc2.type = "square";
    osc2.frequency.setValueAtTime(110, now);
    osc2.frequency.linearRampToValueAtTime(30, now + 0.18);

    gain.gain.setValueAtTime(0.12, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);

    osc.connect(gain);
    osc2.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc2.start(now);
    osc.stop(now + 0.18);
    osc2.stop(now + 0.18);
  }

  /** Play a minor impact rumble when other players are hit. */
  playImpact() {
    const ctx = this.getContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(120, now);
    osc.frequency.exponentialRampToValueAtTime(30, now + 0.08);

    gain.gain.setValueAtTime(0.03, now);
    gain.gain.linearRampToValueAtTime(0.001, now + 0.08);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.08);
  }

  /** Play a beautiful major sweep when capturing a node. */
  playCapture() {
    const ctx = this.getContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const freqs = [261.63, 329.63, 392.00, 523.25]; // C4, E4, G4, C5 (C Major)

    freqs.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      const noteDelay = idx * 0.05;
      osc.frequency.setValueAtTime(freq, now + noteDelay);

      gain.gain.setValueAtTime(0, now);
      gain.gain.setValueAtTime(0.04, now + noteDelay);
      gain.gain.exponentialRampToValueAtTime(0.001, now + noteDelay + 0.25);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now + noteDelay);
      osc.stop(now + noteDelay + 0.25);
    });
  }

  /** Play an 8-bit retro power-up collection sound. */
  playPowerup() {
    const ctx = this.getContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const freqs = [329.63, 392.00, 523.25, 659.25, 783.99, 1046.50]; // E4, G4, C5, E5, G5, C6

    freqs.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "triangle";
      const noteDelay = idx * 0.035;
      osc.frequency.setValueAtTime(freq, now + noteDelay);

      gain.gain.setValueAtTime(0, now);
      gain.gain.setValueAtTime(0.05, now + noteDelay);
      gain.gain.exponentialRampToValueAtTime(0.001, now + noteDelay + 0.15);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now + noteDelay);
      osc.stop(now + noteDelay + 0.15);
    });
  }

  /** Play a dramatic game over low chime or clean death sound. */
  playDeath(isSelf: boolean) {
    const ctx = this.getContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    if (isSelf) {
      // Glitchy explosion-like sound
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(100, now);
      osc.frequency.linearRampToValueAtTime(20, now + 0.4);
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.4);
    } else {
      // Small kill pop
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(300, now);
      osc.frequency.exponentialRampToValueAtTime(50, now + 0.2);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.linearRampToValueAtTime(0.001, now + 0.2);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.2);
    }
  }

  /** Play countdown sounds (short ticks and a final GO buzzer). */
  playCountdown(seconds: number) {
    const ctx = this.getContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    if (seconds <= 0) {
      // GO buzzer sound
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(330, now);
      osc.frequency.linearRampToValueAtTime(660, now + 0.35);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.35);
    } else {
      // Normal countdown tick
      osc.type = "sine";
      osc.frequency.setValueAtTime(seconds === 1 ? 1000 : 800, now);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.12);
    }
  }
}

export const sound = new SoundManager();
