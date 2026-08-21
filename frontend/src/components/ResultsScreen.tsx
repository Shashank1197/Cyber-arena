import type { NetworkClient } from "../services/network";
import type { MatchResult } from "../types";
import { sound } from "../services/sound";

interface Props {
  client: NetworkClient;
  results: MatchResult[];
  myId: string;
}

/**
 * Post-match results: winner, full ranking, and per-player stats with actions
 * to play again or return to the lobby.
 */
export function ResultsScreen({ client, results, myId }: Props) {
  const sorted = [...results].sort((a, b) => b.score - a.score);
  const winner = sorted[0];
  const me = sorted.find((r) => r.player_id === myId);
  const isWinner = me && winner && me.player_id === winner.player_id;

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.round(s % 60);
    return `${m}m ${sec}s`;
  };

  return (
    <div className="screen">
      <div className="panel results">
        <div className="logo">CYBER ARENA</div>
        <div className={`victory ${isWinner ? "win" : "lose"}`}>
          {isWinner ? "VICTORY" : "MATCH OVER"}
        </div>

        <div className="results-list">
          {sorted.map((r, i) => (
            <div key={r.player_id} className="res-row">
              <span className="rank">{i + 1}</span>
              <span className="nm">
                {r.player_name}
                {r.player_id === myId ? " (you)" : ""}
              </span>
              <span className="sc">{r.score}</span>
            </div>
          ))}
        </div>

        {me ? (
          <div className="res-stats">
            <div className="res-stat">
              <div className="num">{me.kills}</div>
              <div className="lbl">Kills</div>
            </div>
            <div className="res-stat">
              <div className="num">{me.deaths}</div>
              <div className="lbl">Deaths</div>
            </div>
            <div className="res-stat">
              <div className="num">{me.nodes_captured}</div>
              <div className="lbl">Nodes</div>
            </div>
          </div>
        ) : null}

        {winner ? (
          <div className="hint">
            Winner: {winner.player_name} &middot; {formatTime(winner.match_duration)}
          </div>
        ) : null}

        <div className="divider" />

        <button className="btn" onClick={() => { sound.playClick(); client.playAgain(); }}>
          PLAY AGAIN
        </button>
        <div style={{ height: 10 }} />
        <button className="btn secondary" onClick={() => { sound.playClick(); client.returnLobby(); }}>
          RETURN TO LOBBY
        </button>
      </div>
    </div>
  );
}
