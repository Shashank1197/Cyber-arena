export type GameState = "lobby" | "countdown" | "playing" | "ended";

export interface LobbyPlayer {
  id: string;
  name: string;
  connected: boolean;
  is_host: boolean;
}

export interface RoomSnapshot {
  room_code: string;
  state: GameState;
  players: LobbyPlayer[];
  host_id: string;
}

export interface PlayerSnapshot {
  id: string;
  name: string;
  x: number;
  y: number;
  angle: number;
  health: number;
  alive: boolean;
  respawn_in: number;
  score: number;
  kills: number;
  deaths: number;
  color: string;
  effects: string[];
}

export interface NodeSnapshot {
  id: string;
  x: number;
  y: number;
  owner_id: string | null;
  progress: number;
  contested: boolean;
}

export interface PowerUpSnapshot {
  id: string;
  x: number;
  y: number;
  type: string;
}

export interface ProjectileSnapshot {
  id: string;
  owner_id: string;
  x: number;
  y: number;
  angle: number;
  damage: number;
}

export interface GameSnapshot {
  t: number;
  state: string;
  time_left: number;
  players: PlayerSnapshot[];
  nodes: NodeSnapshot[];
  powerups: PowerUpSnapshot[];
  projectiles: ProjectileSnapshot[];
}

export interface MatchResult {
  player_id: string;
  player_name: string;
  score: number;
  kills: number;
  deaths: number;
  nodes_captured: number;
  match_duration: number;
}

export type InboundMessage =
  | { type: "welcome"; client_id: string; server_time: number }
  | { type: "joined_room"; room_code: string; state: GameState; player_id: string; players: LobbyPlayer[] }
  | { type: "room_update"; room_code: string; state: GameState; players: LobbyPlayer[]; host_id: string }
  | { type: "error"; code: string; message: string }
  | { type: "match_countdown"; seconds: number }
  | { type: "match_started"; match_id: string; duration: number; arena: { width: number; height: number } }
  | { type: "match_aborted"; reason: string }
  | { type: "snapshot"; snapshot: GameSnapshot }
  | { type: "event"; event: GameEvent }
  | { type: "match_ended"; results: MatchResult[] }
  | { type: "pong"; client_time?: number };

export interface GameEvent {
  type: string;
  [key: string]: unknown;
}

export type ConnectionStatus = "connecting" | "open" | "closed" | "error";

export const POWERUP_LABELS: Record<string, string> = {
  speed: "SPEED BOOST",
  shield: "SHIELD",
  overcharge: "OVERCHARGE",
};
