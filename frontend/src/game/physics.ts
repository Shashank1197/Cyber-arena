import { OBSTACLES } from "./constants";

/**
 * Client-side collision resolution mirroring the server for local prediction.
 * Keeps the local player from visibly clipping obstacles while waiting for the
 * next snapshot. Axis-of-least-penetration like the backend.
 */
export function resolveCollisions(x: number, y: number, radius: number): [number, number] {
  let px = x;
  let py = y;
  for (const r of OBSTACLES) {
    const left = r.x;
    const right = r.x + r.w;
    const top = r.y;
    const bottom = r.y + r.h;
    // inside rect
    if (px >= left && px <= right && py >= top && py <= bottom) {
      const pl = px - left;
      const pr = right - px;
      const pt = py - top;
      const pb = bottom - py;
      const m = Math.min(pl, pr, pt, pb);
      if (m === pl) px = left - radius;
      else if (m === pr) px = right + radius;
      else if (m === pt) py = top - radius;
      else py = bottom + radius;
    } else {
      const cx = Math.max(left, Math.min(px, right));
      const cy = Math.max(top, Math.min(py, bottom));
      const dx = px - cx;
      const dy = py - cy;
      const d2 = dx * dx + dy * dy;
      if (d2 < radius * radius && d2 > 0) {
        const d = Math.sqrt(d2);
        px = cx + (dx / d) * radius;
        py = cy + (dy / d) * radius;
      }
    }
  }
  return [px, py];
}
