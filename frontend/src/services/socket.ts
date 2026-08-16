import type {
  ConnectionStatus,
  InboundMessage,
} from "../types";

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 8000;

type MessageHandler = (msg: InboundMessage) => void;
type StatusHandler = (status: ConnectionStatus) => void;

/**
 * Reusable WebSocket client for the game server.
 *
 * - Auto-reconnects with exponential backoff.
 * - Guarantees callbacks fire on the main thread.
 * - Tracks connection status so the UI can show accurate states.
 */
export class GameSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private messageHandler: MessageHandler | null = null;
  private statusHandler: StatusHandler | null = null;
  private shouldReconnect = true;
  private reconnectAttempts = 0;
  private reconnectTimer: number | null = null;
  private sendQueue: string[] = [];

  constructor(url: string) {
    this.url = url;
  }

  connect() {
    this.shouldReconnect = true;
    this.reconnectAttempts = 0;
    this.open();
  }

  onMessage(handler: MessageHandler) {
    this.messageHandler = handler;
  }

  onStatus(handler: StatusHandler) {
    this.statusHandler = handler;
  }

  send(obj: unknown) {
    const raw = JSON.stringify(obj);
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(raw);
    } else {
      // Buffer input sent before the socket is open (e.g. fast initial actions).
      this.sendQueue.push(raw);
    }
  }

  close() {
    this.shouldReconnect = false;
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
    this.statusHandler?.("closed");
  }

  private open() {
    try {
      this.ws = new WebSocket(this.url);
    } catch {
      this.scheduleReconnect();
      return;
    }
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.statusHandler?.("open");
      this.flushQueue();
    };
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as InboundMessage;
        this.messageHandler?.(data);
      } catch {
        // Ignore malformed frames; never let one corrupt the client.
      }
    };
    this.ws.onclose = () => {
      this.statusHandler?.("closed");
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    };
    this.ws.onerror = () => {
      this.statusHandler?.("error");
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer !== null) return;
    const delay = Math.min(
      RECONNECT_MAX_MS,
      RECONNECT_BASE_MS * 2 ** this.reconnectAttempts
    );
    this.reconnectAttempts += 1;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.open();
    }, delay);
  }

  private flushQueue() {
    while (this.sendQueue.length) {
      const raw = this.sendQueue.shift()!;
      this.ws?.send(raw);
    }
  }
}

export function buildWsUrl(): string {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws`;
}
