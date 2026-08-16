import { GameSocket, buildWsUrl } from "./socket";
import type { InboundMessage } from "../types";

/**
 * Thin wrapper that presents the socket with a typed send API and lets the app
 * subscribe to decoded inbound messages.
 */
export class NetworkClient {
  readonly socket: GameSocket;

  constructor() {
    this.socket = new GameSocket(buildWsUrl());
  }

  connect() {
    this.socket.connect();
  }

  onMessage(handler: (msg: InboundMessage) => void) {
    this.socket.onMessage(handler);
  }

  onStatus(handler: (status: string) => void) {
    this.socket.onStatus(handler);
  }

  send(type: string, payload: Record<string, unknown> = {}) {
    this.socket.send({ type, ...payload });
  }

  // ---- specific messages ----
  createRoom(name: string, playerId: string) {
    this.send("create_room", { name, player_id: playerId });
  }
  joinRoom(name: string, roomCode: string, playerId: string) {
    this.send("join_room", { name, room_code: roomCode, player_id: playerId });
  }
  reconnect(playerId: string, roomCode: string) {
    this.send("reconnect", { player_id: playerId, room_code: roomCode });
  }
  leaveRoom() {
    this.send("leave_room", {});
  }
  startMatch() {
    this.send("start_match", {});
  }
  playAgain() {
    this.send("play_again", {});
  }
  returnLobby() {
    this.send("return_lobby", {});
  }
  move(x: number, y: number, angle: number) {
    this.send("move", { x, y, angle });
  }
  setAim(angle: number) {
    this.send("aim", { angle });
  }
  shoot(angle: number) {
    this.send("shoot", { angle });
  }
  ping(clientTime: number) {
    this.send("ping", { client_time: clientTime });
  }
}
