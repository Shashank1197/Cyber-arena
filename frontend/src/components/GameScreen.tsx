import { useEffect, useRef, useState } from "react";
import type { NetworkClient } from "../services/network";
import { ClientEngine } from "../game/engine";
import { Renderer } from "../game/renderer";
import { CONTROLS_TEXT } from "../game/constants";
import type { GameSnapshot, InboundMessage, PlayerSnapshot } from "../types";

interface Props {
  client: NetworkClient;
  playerId: string;
  snapshot: GameSnapshot;
  message: InboundMessage | null;
}

interface Toast {
  id: number;
  text: string;
  kind: "kill" | "capture" | "info";
}

let toastId = 0;

/**
 * Renders the live match: canvas, HUD, and event notifications. Keeps all
 * input + rendering concerns local and pushes events up via callback-free
 * notification toasts shown here.
 */
export function GameScreen({ client, playerId, snapshot, message }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<ClientEngine | null>(null);
  const rendererRef = useRef<Renderer | null>(null);
  const myNameRef = useRef("");
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [self, setSelf] = useState<PlayerSnapshot | null>(null);
  const [leaderboard, setLeaderboard] = useState<PlayerSnapshot[]>([]);

  const pushToast = (text: string, kind: Toast["kind"]) => {
    const id = ++toastId;
    setToasts((prev) => [...prev.slice(-3), { id, text, kind }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const engine = new ClientEngine(client, playerId);
    const renderer = new Renderer(canvas, playerId);
    engineRef.current = engine;
    rendererRef.current = renderer;

    const resize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      renderer.resize(w, h);
    };
    resize();
    window.addEventListener("resize", resize);

    const keydown = (e: KeyboardEvent) => engine.keydown(e);
    const keyup = (e: KeyboardEvent) => engine.keyup(e);
    const mousemove = (e: MouseEvent) => {
      const me = engine.interpolateSelf();
      if (!me) return;
      const { x, y } = renderer.screenToWorld(e.clientX, e.clientY);
      engine.setAim(Math.atan2(y - me.y, x - me.x));
    };
    const mousedown = (e: MouseEvent) => {
      if (e.button === 0) engine.setFiring(true);
    };
    const mouseup = (e: MouseEvent) => {
      if (e.button === 0) engine.setFiring(false);
    };
    const onBlur = () => engine.resetInput();
    window.addEventListener("keydown", keydown);
    window.addEventListener("keyup", keyup);
    window.addEventListener("mousemove", mousemove);
    window.addEventListener("mousedown", mousedown);
    window.addEventListener("mouseup", mouseup);
    window.addEventListener("blur", onBlur);

    let raf = 0;
    let last = performance.now();
    const loop = (now: number) => {
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      engine.update(dt);
      const snap = engineRef.current?.lastSnapshot ?? snapshot;
      const local = engine.interpolateSelf();
      renderer.draw(snap, local);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("keydown", keydown);
      window.removeEventListener("keyup", keyup);
      window.removeEventListener("mousemove", mousemove);
      window.removeEventListener("mousedown", mousedown);
      window.removeEventListener("mouseup", mouseup);
      window.removeEventListener("blur", onBlur);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!engineRef.current) return;
    engineRef.current.applySnapshot(snapshot);
    engineRef.current.lastSnapshot = snapshot;
    const me = snapshot.players.find((p) => p.id === playerId);
    setSelf(me ?? null);
    const sorted = [...snapshot.players].sort((a, b) => b.score - a.score);
    setLeaderboard(sorted);
  }, [snapshot, playerId]);

  useEffect(() => {
    if (snapshot.players.length && !myNameRef.current) {
      myNameRef.current = snapshot.players[0].name;
    }
  }, [snapshot]);

  // React to live event messages (countdown, kills, captures, power-ups).
  useEffect(() => {
    if (!message) return;
    if (message.type === "match_countdown") {
      setCountdown(message.seconds);
      if (message.seconds <= 0) setCountdown(null);
    } else if (message.type === "event") {
      const ev = message.event;
      if (ev.type === "player_killed") {
        const killerName =
          snapshot.players.find((p) => p.id === ev.killer_id)?.name ?? "?";
        const victimName =
          snapshot.players.find((p) => p.id === ev.victim_id)?.name ?? "?";
        pushToast(`${killerName} eliminated ${victimName}`, "kill");
      } else if (ev.type === "node_captured") {
        const ownerName =
          snapshot.players.find((p) => p.id === ev.owner_id)?.name ?? "?";
        pushToast(`${ownerName} captured node ${ev.node_id}`, "capture");
      } else if (ev.type === "powerup_collected") {
        const pName =
          snapshot.players.find((p) => p.id === ev.player_id)?.name ?? "?";
        pushToast(`${pName} picked up ${ev.powerup_type}`, "info");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [message]);

  const minutes = Math.floor(snapshot.time_left / 60);
  const seconds = String(Math.round(snapshot.time_left % 60)).padStart(2, "0");

  return (
    <div className="game-root">
      <canvas ref={canvasRef} className="game-canvas" />

      {countdown !== null && (
        <div className="countdown">{countdown}</div>
      )}

      <div className="hud">
        <div className="hud-top">
          <div className="timer">{minutes}:{seconds}</div>
        </div>

        <div className="hud-left">
          <div className="health-label">{self?.name ?? "YOU"}</div>
          <div className="health-bar">
            <div className="health-fill" style={{ width: `${self?.health ?? 0}%` }} />
          </div>
          <div className="hud-stat">
            <span className="k">SCORE</span>
            <span className="v">{Math.round(self?.score ?? 0)}</span>
          </div>
          <div className="hud-stat">
            <span className="k">KILLS</span>
            <span className="v">{self?.kills ?? 0}</span>
          </div>
          <div className="hud-stat">
            <span className="k">DEATHS</span>
            <span className="v">{self?.deaths ?? 0}</span>
          </div>
          {self && self.effects.length > 0 && (
            <div className="hud-stat">
              <span className="k">POWER</span>
              <span className="v">{self.effects.join("+")}</span>
            </div>
          )}
        </div>

        <div className="hud-right">
          <div className="leaderboard-title">LEADERBOARD</div>
          {leaderboard.map((p, i) => (
            <div key={p.id} className={`lb-row ${p.id === playerId ? "me" : ""}`}>
              <span className="rank">{i + 1}</span>
              <span style={{ color: p.color }}>●</span>
              <span>{p.name}</span>
              <span className="score">{Math.round(p.score)}</span>
            </div>
          ))}
        </div>

        <div className="hud-bottom">
          <div className="controls">{CONTROLS_TEXT}</div>
        </div>
      </div>

      <div className="notifications">
        {toasts.map((t) => (
          <div key={t.id} className={`notif ${t.kind}`}>
            {t.text}
          </div>
        ))}
      </div>
    </div>
  );
}
