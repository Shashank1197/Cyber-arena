import { useState } from "react";
import type { NetworkClient } from "../services/network";
import { sound } from "../services/sound";

interface Props {
  client: NetworkClient;
  connectionStatus: string;
}

/**
 * First-time entry: enter a display name, then either create a room or join one
 * with a 6-character code.
 */
export function HomeScreen({ client, connectionStatus }: Props) {
  const [name, setName] = useState("");
  const [roomCode, setRoomCode] = useState("");
  const [mode, setMode] = useState<"menu" | "create" | "join">("menu");
  const [error, setError] = useState<string | null>(null);

  const sanitized = name.trim();

  const handleCreate = () => {
    sound.playClick();
    if (!sanitized) {
      setError("Enter a display name first.");
      return;
    }
    setError(null);
    client.createRoom(sanitized, crypto.randomUUID());
  };

  const handleJoin = () => {
    sound.playClick();
    if (!sanitized) {
      setError("Enter a display name first.");
      return;
    }
    if (roomCode.trim().length < 6) {
      setError("Enter a 6-character room code.");
      return;
    }
    setError(null);
    client.joinRoom(sanitized, roomCode.trim().toUpperCase(), crypto.randomUUID());
  };

  return (
    <div className="screen">
      <div className="panel">
        <div className="logo">CYBER ARENA</div>
        <div className="tagline">Capture. Attack. Defend. Dominate.</div>

        <div className="field">
          <label>Display Name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            maxLength={16}
            autoFocus
          />
        </div>

        {mode === "create" && (
          <>
            <button className="btn" onClick={handleCreate} disabled={connectionStatus !== "open"}>
              CREATE ROOM
            </button>
            <div className="hint">
              A new room with a shareable code will be created for you.
            </div>
          </>
        )}

        {mode === "join" && (
          <>
            <div className="field">
              <label>Room Code</label>
              <input
                value={roomCode}
                onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                placeholder="CYB42X"
                maxLength={6}
              />
            </div>
            <button className="btn" onClick={handleJoin} disabled={connectionStatus !== "open"}>
              JOIN ROOM
            </button>
            <div className="hint">
              Enter the 6-character code shared by the room host.
            </div>
          </>
        )}

        {mode === "menu" && (
          <>
            <div className="row">
              <button className="btn" onClick={() => { sound.playClick(); setMode("create"); }}>
                CREATE ROOM
              </button>
              <button className="btn secondary" onClick={() => { sound.playClick(); setMode("join"); }}>
                JOIN ROOM
              </button>
            </div>
            <div className="hint">
              Play with up to 4 players in a live multiplayer arena.
            </div>
          </>
        )}

        <div className="error">{error}</div>

        {connectionStatus !== "open" && (
          <div className="hint" style={{ color: "var(--danger)" }}>
            {connectionStatus === "connecting"
              ? "Connecting to server..."
              : "Server unreachable. Make sure the backend is running."}
          </div>
        )}
      </div>
    </div>
  );
}
