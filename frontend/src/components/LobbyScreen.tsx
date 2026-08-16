import type { NetworkClient } from "../services/network";
import type { LobbyPlayer } from "../types";

interface Props {
  client: NetworkClient;
  roomCode: string;
  players: LobbyPlayer[];
  hostId: string;
  myId: string;
}

/**
 * Pre-match lobby: shows the joinable room code, the roster, and lets the host
 * start the match once enough players are present.
 */
export function LobbyScreen({ client, roomCode, players, hostId, myId }: Props) {
  const isHost = hostId === myId;
  const canStart = players.filter((p) => p.connected).length >= 2;

  const handleStart = () => {
    client.startMatch();
  };

  const handleCopy = () => {
    navigator.clipboard?.writeText(roomCode);
  };

  return (
    <div className="screen">
      <div className="panel lobby">
        <div className="logo">CYBER ARENA</div>
        <div className="tagline">Capture. Attack. Defend. Dominate.</div>

        <div className="room-code" onClick={handleCopy} title="Click to copy">
          {roomCode}
        </div>

        <div className="players-list">
          {players.map((p) => (
            <div key={p.id} className="player-row">
              <span
                className="dot"
                style={{ background: p.connected ? "#7cff4f" : "#4a5570" }}
              />
              <span className="name">
                {p.name}
                {p.id === myId ? " (you)" : ""}
              </span>
              {p.id === hostId ? <span className="role">HOST</span> : null}
              <span className="status">{p.connected ? "connected" : "disconnected"}</span>
            </div>
          ))}
        </div>

        <div className="divider" />

        {isHost ? (
          <button className="btn" onClick={handleStart} disabled={!canStart}>
            START MATCH
          </button>
        ) : (
          <div className="hint">Waiting for the host to start the match...</div>
        )}

        <div className="hint">
          Share this room code so friends can join. A match needs 2-4 players.
        </div>
      </div>
    </div>
  );
}
