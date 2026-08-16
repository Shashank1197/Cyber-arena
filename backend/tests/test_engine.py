#!/usr/bin/env python3
"""Unit tests for the authoritative game engine."""
from app.game import constants as C
from app.game.engine import GameEngine


def _engine(players=("p1", "p2")):
    meta = [{"id": pid, "name": pid.upper()} for pid in players]
    return GameEngine("m_test", meta)


# --------------------------------------------------------------- capture
def test_capture_neutral_node():
    engine = _engine(("p1",))
    node = next(n for n in engine.nodes if n.id == "node_a")
    p1 = engine.players["p1"]
    p1.x, p1.y = node.x, node.y - 20
    for _ in range(70):  # 3.5s > 100/30
        engine.update(0.05)
    assert node.owner_id == "p1"
    assert node.progress == 100.0
    assert p1.nodes_captured == 1


def test_contest_drains_owned_node():
    engine = _engine(("p1", "p2"))
    node = next(n for n in engine.nodes if n.id == "node_a")
    p1, p2 = engine.players["p1"], engine.players["p2"]
    # p1 captures the node.
    p1.x, p1.y = node.x, node.y - 20
    for _ in range(70):
        engine.update(0.05)
    assert node.owner_id == "p1"
    # p1 leaves, p2 enters and drains ownership back toward neutral.
    p1.x, p1.y = 800, 500
    p2.x, p2.y = node.x, node.y - 20
    for _ in range(20):  # 1s of draining
        engine.update(0.05)
    assert node.progress < 100.0
    assert node.owner_id == "p1"  # not yet fully reverted


def test_contest_flag_with_two_captors():
    engine = _engine(("p1", "p2"))
    node = next(n for n in engine.nodes if n.id == "node_a")
    p1, p2 = engine.players["p1"], engine.players["p2"]
    p1.x, p1.y = node.x, node.y - 20
    p2.x, p2.y = node.x, node.y + 20
    engine.update(0.05)
    assert node.contested is True


# --------------------------------------------------------------- combat
def test_projectile_damages_target():
    engine = _engine(("p1", "p2"))
    p1, p2 = engine.players["p1"], engine.players["p2"]
    p1.x, p1.y = 200, 500
    p2.x, p2.y = 260, 500
    engine.fire("p1", 0.0)
    for _ in range(5):
        engine.update(0.05)
    assert p2.health < C.MAX_HEALTH


def test_damage_applies_and_kill_scores():
    engine = _engine(("p1", "p2"))
    p1, p2 = engine.players["p1"], engine.players["p2"]
    engine._apply_damage("p2", "p1", C.MAX_HEALTH)
    assert p2.alive is False
    assert p2.deaths == 1
    assert p1.kills == 1
    assert p1.score >= C.KILL_SCORE


def test_respawn_after_delay():
    engine = _engine(("p1", "p2"))
    p2 = engine.players["p2"]
    engine._apply_damage("p2", "p1", C.MAX_HEALTH)
    assert p2.alive is False
    for _ in range(int((C.RESPAWN_DELAY + 0.5) / 0.05)):
        engine.update(0.05)
    assert p2.alive is True
    assert p2.health == C.MAX_HEALTH


def test_fire_has_no_cooldown():
    engine = _engine(("p1",))
    engine.fire("p1", 0.0)
    engine.fire("p1", 0.0)  # continuous fire -> both shots spawn
    assert len(engine.projectiles) == 2


# --------------------------------------------------------------- score
def test_owned_node_generates_score():
    engine = _engine(("p1",))
    node = next(n for n in engine.nodes if n.id == "node_a")
    engine.players["p1"].x, engine.players["p1"].y = node.x, node.y - 20
    for _ in range(70):
        engine.update(0.05)
    before = engine.players["p1"].score
    for _ in range(40):  # 2s of node ownership
        engine.update(0.05)
    assert engine.players["p1"].score >= before + C.NODE_SCORE_RATE * 2


# --------------------------------------------------------------- state
def test_match_ends_on_timeout():
    engine = GameEngine("m_short", [{"id": "p1", "name": "P1"}], duration=0.5)
    for _ in range(10):  # 10 * 0.1s (dt clamp) = 1.0s > 0.5s
        engine.update(0.6)
    assert engine.state == "ended"


def test_match_ends_on_score_cap():
    engine = _engine(("p1",))
    engine.players["p1"].score = C.SCORE_CAP  # trigger win condition
    engine.update(0.05)
    assert engine.state == "ended"


# --------------------------------------------------------------- power-ups
def test_powerup_spawns_after_spawn_interval():
    # Regression: the first power-up spawn must not crash the simulation
    # (valid_open_position used to call circle_rect_collide on the whole
    # obstacle list, raising AttributeError at ~6s / first spawn).
    engine = _engine(("p1",))
    for _ in range(int((C.POWERUP_SPAWN_INTERVAL + 0.5) / 0.05)):
        engine.update(0.05)
    assert len(engine.powerups) >= 1
    assert engine.state == "playing"  # still alive after the spawn tick
