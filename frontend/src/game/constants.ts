// Mirrors backend/app/game/constants.py for rendering & local prediction.
// The server remains the source of truth for gameplay.

export const ARENA_WIDTH = 1600;
export const ARENA_HEIGHT = 1000;

export const PLAYER_RADIUS = 16;
export const PROJECTILE_RADIUS = 5;
export const MAX_HEALTH = 100;

export const NODE_CAPTURE_RADIUS = 70;
export const NODE_RENDER_RADIUS = 34;

// Static obstacle layout (Rect: x,y,w,h). Matches backend map.build_obstacles.
export const OBSTACLES = [
  { x: 400, y: 380, w: 120, h: 240 },
  { x: 1080, y: 380, w: 120, h: 240 },
  { x: 700, y: 110, w: 200, h: 110 },
  { x: 700, y: 780, w: 200, h: 110 },
  { x: 748, y: 458, w: 104, h: 84 },
  { x: 170, y: 170, w: 70, h: 70 },
  { x: 1360, y: 170, w: 70, h: 70 },
  { x: 170, y: 760, w: 70, h: 70 },
  { x: 1360, y: 760, w: 70, h: 70 },
];

export const CONTROLS_TEXT = "WASD  MOVE      MOUSE  AIM      CLICK  SHOOT";
