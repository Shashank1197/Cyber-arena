import type { NetworkClient } from "../services/network";
import type { GameSnapshot, PlayerSnapshot } from "../types";

const MOVE_SEND_INTERVAL = 1 / 15; // ~15 movement updates/sec

interface InputState {
  up: boolean;
  down: boolean;
  left: boolean;
  right: boolean;
}

/**
 * Client-side engine for the *local* player and input sampling.
 *
 * Movement input is sampled from the keyboard, normalized, and sent to the
 * server. The local player's visual position is reconciled from the latest
 * server snapshot (server-authoritative) with light smoothing so it feels
 * responsive without trusting the client for position.
 */
export class ClientEngine {
  private net: NetworkClient;
  private input: InputState = { up: false, down: false, left: false, right: false };
  private aimAngle = 0;
  private moveAccum = 0;
  private myId: string;
  private latestPlayers: PlayerSnapshot[] = [];
  lastSnapshot: GameSnapshot | null = null;

  constructor(net: NetworkClient, myId: string) {
    this.net = net;
    this.myId = myId;
  }

  keydown(e: KeyboardEvent) {
    switch (e.key.toLowerCase()) {
      case "w": case "arrowup": this.input.up = true; break;
      case "s": case "arrowdown": this.input.down = true; break;
      case "a": case "arrowleft": this.input.left = true; break;
      case "d": case "arrowright": this.input.right = true; break;
      default: return;
    }
    e.preventDefault();
  }

  keyup(e: KeyboardEvent) {
    switch (e.key.toLowerCase()) {
      case "w": case "arrowup": this.input.up = false; break;
      case "s": case "arrowdown": this.input.down = false; break;
      case "a": case "arrowleft": this.input.left = false; break;
      case "d": case "arrowright": this.input.right = false; break;
      default: return;
    }
  }

  setAim(angle: number) {
    this.aimAngle = angle;
  }

  /** Fire a single shot on click. */
  fireOnce() {
    this.net.shoot(this.aimAngle);
  }

  /** Apply the latest authoritative snapshot (players only). */
  applySnapshot(snap: GameSnapshot) {
    this.latestPlayers = snap.players;
  }

  /** Advance local input -> server in a fixed-throttle cadence. */
  update(dt: number) {
    // Movement vector.
    let mx = 0;
    let my = 0;
    if (this.input.left) mx -= 1;
    if (this.input.right) mx += 1;
    if (this.input.up) my -= 1;
    if (this.input.down) my += 1;
    if (mx !== 0 || my !== 0) {
      const len = Math.hypot(mx, my);
      mx /= len;
      my /= len;
    }

    this.moveAccum += dt;
    if (this.moveAccum >= MOVE_SEND_INTERVAL) {
      this.moveAccum = 0;
      this.net.move(mx, my, this.aimAngle);
    }
  }

  /** Interpolate the local player's rendered position toward the server value. */
  interpolateSelf(): PlayerSnapshot | null {
    const self = this.latestPlayers.find((p) => p.id === this.myId);
    if (!self) return null;
    return { ...self };
  }
}
