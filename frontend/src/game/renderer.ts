import {
  ARENA_HEIGHT,
  ARENA_WIDTH,
  NODE_RENDER_RADIUS,
  OBSTACLES,
  PLAYER_RADIUS,
} from "./constants";
import type {
  GameSnapshot,
  NodeSnapshot,
  PlayerSnapshot,
  PowerUpSnapshot,
  ProjectileSnapshot,
} from "../types";

const POWERUP_COLORS: Record<string, string> = {
  speed: "#00f0ff",
  shield: "#7cff4f",
  overcharge: "#ffd23f",
};

/**
 * Pure canvas renderer. Owns the draw loop and takes a GameSnapshot + camera
 * transform each frame. No game logic lives here.
 */
export class Renderer {
  private ctx: CanvasRenderingContext2D;
  private scale: number;
  private offsetX: number;
  private offsetY: number;
  private myId: string;

  constructor(canvas: HTMLCanvasElement, myId: string) {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Canvas 2D context unavailable");
    this.ctx = ctx;
    this.myId = myId;
    this.scale = 1;
    this.offsetX = 0;
    this.offsetY = 0;
  }

  resize(width: number, height: number) {
    const canvas = this.ctx.canvas;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // Fit the whole arena to the viewport, centered.
    this.scale = Math.min(width / ARENA_WIDTH, height / ARENA_HEIGHT);
    this.offsetX = (width - ARENA_WIDTH * this.scale) / 2;
    this.offsetY = (height - ARENA_HEIGHT * this.scale) / 2;
  }

  draw(snapshot: GameSnapshot, localPlayer: PlayerSnapshot | null) {
    const ctx = this.ctx;
    const { scale, offsetX, offsetY } = this;
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    ctx.save();
    ctx.translate(offsetX, offsetY);
    ctx.scale(scale, scale);

    this.drawArena();
    this.drawNodes(snapshot.nodes, snapshot.players);
    this.drawPowerUps(snapshot.powerups);
    this.drawProjectiles(snapshot.projectiles);
    this.drawPlayers(snapshot.players);

    // Highlight the local player with a pulsing ring so their avatar is obvious.
    if (localPlayer) {
      ctx.save();
      ctx.translate(localPlayer.x, localPlayer.y);
      ctx.beginPath();
      ctx.arc(0, 0, PLAYER_RADIUS + 6, 0, Math.PI * 2);
      ctx.strokeStyle = localPlayer.color;
      ctx.globalAlpha = 0.6;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();
    }

    ctx.restore();
  }

  private drawArena() {
    const ctx = this.ctx;
    // Floor.
    ctx.fillStyle = "#070b18";
    ctx.fillRect(0, 0, ARENA_WIDTH, ARENA_HEIGHT);
    // Grid.
    ctx.strokeStyle = "rgba(0, 240, 255, 0.05)";
    ctx.lineWidth = 1;
    const step = 100;
    ctx.beginPath();
    for (let x = 0; x <= ARENA_WIDTH; x += step) {
      ctx.moveTo(x, 0);
      ctx.lineTo(x, ARENA_HEIGHT);
    }
    for (let y = 0; y <= ARENA_HEIGHT; y += step) {
      ctx.moveTo(0, y);
      ctx.lineTo(ARENA_WIDTH, y);
    }
    ctx.stroke();
    // Border.
    ctx.strokeStyle = "#1c2a4a";
    ctx.lineWidth = 3;
    ctx.strokeRect(1, 1, ARENA_WIDTH - 2, ARENA_HEIGHT - 2);
    // Obstacles.
    for (const o of OBSTACLES) {
      ctx.fillStyle = "#101a33";
      ctx.fillRect(o.x, o.y, o.w, o.h);
      ctx.strokeStyle = "#23395e";
      ctx.lineWidth = 2;
      ctx.strokeRect(o.x, o.y, o.w, o.h);
      ctx.strokeStyle = "rgba(0, 240, 255, 0.12)";
      ctx.lineWidth = 1;
      ctx.strokeRect(o.x - 3, o.y - 3, o.w + 6, o.h + 6);
    }
  }

  private drawNodes(nodes: NodeSnapshot[], players: PlayerSnapshot[]) {
    const ctx = this.ctx;
    const colorMap = new Map(players.map((p) => [p.id, p.color]));
    const ownerColor = (id: string | null) =>
      id ? colorMap.get(id) ?? "#00f0ff" : "#8a93ab";
    for (const node of nodes) {
      ctx.save();
      ctx.translate(node.x, node.y);
      // Capture zone ring.
      ctx.beginPath();
      ctx.arc(0, 0, node.progress > 0 ? 60 : NODE_RENDER_RADIUS + 6, 0, Math.PI * 2);
      ctx.strokeStyle = ownerColor(node.owner_id);
      ctx.globalAlpha = node.contested ? 0.7 : 0.3;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.globalAlpha = 1;
      // Body.
      ctx.beginPath();
      ctx.arc(0, 0, NODE_RENDER_RADIUS, 0, Math.PI * 2);
      ctx.fillStyle = ownerColor(node.owner_id);
      ctx.globalAlpha = node.owner_id ? 0.22 : 0.08;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = ownerColor(node.owner_id);
      ctx.lineWidth = 2;
      ctx.stroke();
      // Node glyph.
      ctx.beginPath();
      ctx.arc(0, 0, 7, 0, Math.PI * 2);
      ctx.fillStyle = ownerColor(node.owner_id);
      ctx.fill();
      // Capture progress arc.
      if (node.progress > 0 && node.progress < 100) {
        ctx.beginPath();
        ctx.arc(0, 0, NODE_RENDER_RADIUS + 10, -Math.PI / 2, -Math.PI / 2 + (node.progress / 100) * Math.PI * 2);
        ctx.strokeStyle = node.owner_id ? ownerColor(node.owner_id) : "#ffffff";
        ctx.lineWidth = 4;
        ctx.stroke();
      }
      // Percent label.
      ctx.fillStyle = "#d7e3ff";
      ctx.font = "bold 11px monospace";
      ctx.textAlign = "center";
      ctx.fillText(`${Math.round(node.progress)}%`, 0, NODE_RENDER_RADIUS + 28);
      ctx.restore();
    }
  }

  private drawPowerUps(powerups: PowerUpSnapshot[]) {
    const ctx = this.ctx;
    for (const pu of powerups) {
      const color = POWERUP_COLORS[pu.type] || "#fff";
      ctx.save();
      ctx.translate(pu.x, pu.y);
      ctx.beginPath();
      ctx.arc(0, 0, 12, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.25;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.font = "bold 13px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = color;
      ctx.fillText(this.icon(pu.type), 0, 1);
      ctx.restore();
    }
  }

  private drawProjectiles(projectiles: ProjectileSnapshot[]) {
    const ctx = this.ctx;
    for (const p of projectiles) {
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.angle);
      ctx.fillStyle = "#ffe066";
      ctx.beginPath();
      ctx.ellipse(0, 0, 8, 3, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }

  private drawPlayers(players: PlayerSnapshot[]) {
    const ctx = this.ctx;
    for (const p of players) {
      ctx.save();
      ctx.translate(p.x, p.y);
      // Dead -> dim ghost.
      ctx.globalAlpha = p.alive ? 1 : 0.25;
      // Shield aura.
      if (p.effects.includes("shield")) {
        ctx.beginPath();
        ctx.arc(0, 0, PLAYER_RADIUS + 6, 0, Math.PI * 2);
        ctx.strokeStyle = "#7cff4f";
        ctx.globalAlpha = 0.8;
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.globalAlpha = p.alive ? 1 : 0.25;
      }
      // Body.
      ctx.beginPath();
      ctx.arc(0, 0, PLAYER_RADIUS, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = (p.alive ? 1 : 0.25) * 0.25;
      ctx.fill();
      ctx.globalAlpha = p.alive ? 1 : 0.25;
      ctx.strokeStyle = p.color;
      ctx.lineWidth = 2;
      ctx.stroke();
      // Aim barrel.
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(Math.cos(p.angle) * (PLAYER_RADIUS + 8), Math.sin(p.angle) * (PLAYER_RADIUS + 8));
      ctx.strokeStyle = p.color;
      ctx.lineWidth = 3;
      ctx.stroke();
      // Health ring above.
      const frac = Math.max(0, p.health / 100);
      ctx.fillStyle = "rgba(6,8,18,0.7)";
      ctx.fillRect(-PLAYER_RADIUS, -PLAYER_RADIUS - 10, PLAYER_RADIUS * 2, 4);
      ctx.fillStyle = frac > 0.5 ? "#7cff4f" : frac > 0.25 ? "#ffd23f" : "#ff4d6d";
      ctx.fillRect(-PLAYER_RADIUS, -PLAYER_RADIUS - 10, PLAYER_RADIUS * 2 * frac, 4);
      ctx.restore();
      // Name + marker for self.
      ctx.save();
      ctx.fillStyle = p.id === this.myId ? "#fff" : "#9fb0d6";
      ctx.font = "bold 11px monospace";
      ctx.textAlign = "center";
      ctx.fillText(p.name, p.x, p.y - PLAYER_RADIUS - 18);
      if (p.id === this.myId) {
        ctx.fillStyle = "#00f0ff";
        ctx.font = "10px monospace";
        ctx.fillText("YOU", p.x, p.y - PLAYER_RADIUS - 30);
      }
      ctx.restore();
    }
  }

  private icon(type: string): string {
    if (type === "speed") return ">";
    if (type === "shield") return "S";
    return "!";
  }
}
