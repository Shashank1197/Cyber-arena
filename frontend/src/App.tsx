import { useEffect, useState } from "react";
import { useNetwork } from "./hooks/useNetwork";
import { HomeScreen } from "./components/HomeScreen";
import { LobbyScreen } from "./components/LobbyScreen";
import { GameScreen } from "./components/GameScreen";
import { ResultsScreen } from "./components/ResultsScreen";
import type { GameSnapshot, GameState, LobbyPlayer, MatchResult } from "./types";

interface Session {
  roomCode: string;
  playerId: string;
  state: GameState;
  players: LobbyPlayer[];
  hostId: string;
}

/**
 * Top-level application state machine. Drives which screen is shown based on
 * the room's match state and the latest snapshot/messages from the server.
 */
export default function App() {
  const { client, status, lastMessage } = useNetwork();
  const [session, setSession] = useState<Session | null>(null);
  const [snapshot, setSnapshot] = useState<GameSnapshot | null>(null);
  const [results, setResults] = useState<MatchResult[] | null>(null);
  const [showLobby, setShowLobby] = useState(true);

  // React to each inbound message (state transitions only).
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case "joined_room":
        setSession({
          roomCode: lastMessage.room_code,
          playerId: lastMessage.player_id,
          state: lastMessage.state,
          players: lastMessage.players,
          hostId: lastMessage.player_id,
        });
        setResults(null);
        setShowLobby(true);
        break;
      case "room_update":
        setSession((s) =>
          s
            ? {
                ...s,
                state: lastMessage.state,
                players: lastMessage.players,
                hostId: lastMessage.host_id,
              }
            : s
        );
        break;
      case "snapshot":
        setSnapshot(lastMessage.snapshot);
        break;
      case "match_started":
        setSession((s) => (s ? { ...s, state: "playing" } : s));
        setSnapshot(null);
        setShowLobby(false);
        break;
      case "match_countdown":
        setSession((s) => (s ? { ...s, state: "countdown" } : s));
        break;
      case "match_ended":
        setResults(lastMessage.results);
        break;
      case "match_aborted":
        setResults(null);
        setShowLobby(true);
        setSession((s) => (s ? { ...s, state: "lobby" } : s));
        break;
      default:
        break;
    }
  }, [lastMessage]);

  if (!session) {
    return <HomeScreen client={client} connectionStatus={status} />;
  }

  const inLiveState =
    session.state === "playing" || session.state === "countdown";

  if (session.state === "lobby" || (showLobby && !inLiveState)) {
    return (
      <LobbyScreen
        client={client}
        roomCode={session.roomCode}
        players={session.players}
        hostId={session.hostId}
        myId={session.playerId}
      />
    );
  }

  if (results) {
    return (
      <ResultsScreen
        client={client}
        results={results}
        myId={session.playerId}
      />
    );
  }

  if (snapshot) {
    return (
      <GameScreen
        client={client}
        playerId={session.playerId}
        snapshot={snapshot}
        message={lastMessage}
      />
    );
  }

  return (
    <div className="screen">
      <div className="panel">
        <div className="logo">CYBER ARENA</div>
        <div className="hint">Waiting for match to start...</div>
      </div>
    </div>
  );
}

