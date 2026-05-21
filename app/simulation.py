"""VEX IQ-like task + GA optimizer. stdlib only."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, asdict


FIELD = 30
GOAL = (28.0, 28.0)
BALL_POS = [(3, 4), (20, 6), (10, 16), (26, 18), (6, 24), (15, 27), (28, 4)]
N_BALLS = len(BALL_POS)
TIME_BUDGET = 35.0
TIME_MOVE = 0.25
TIME_TURN = 0.8
TIME_PICKUP = 0.4
TIME_DEPOSIT = 0.5
PENALTY_WALL = 1.5
NOISE_SIGMA = 3.0


@dataclass(frozen=True)
class Policy:
    order: tuple
    margin: tuple
    skip_thresh: float

    def to_dict(self):
        return {
            "order": list(self.order),
            "margin": [round(m, 3) for m in self.margin],
            "skip_thresh": round(self.skip_thresh, 3),
        }


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def sample_field(seed: int):
    rng = random.Random(seed)
    return [
        (x + rng.gauss(0, NOISE_SIGMA), y + rng.gauss(0, NOISE_SIGMA))
        for x, y in BALL_POS
    ]


def simulate(policy: Policy, balls):
    pos = (0.0, 0.0)
    path = [pos]
    scored = 0
    elapsed = 0.0
    for idx in policy.order:
        if elapsed >= TIME_BUDGET - policy.skip_thresh:
            break
        bx, by = balls[idx]
        norm = math.hypot(bx, by) or 1e-3
        margin = policy.margin[idx]
        target = (bx - margin * bx / norm, by - margin * by / norm)
        if not (0 <= target[0] <= FIELD and 0 <= target[1] <= FIELD):
            elapsed += PENALTY_WALL
            continue
        elapsed += _dist(target, pos) * TIME_MOVE + TIME_TURN + TIME_PICKUP
        pos = target
        path.append(pos)
        if elapsed >= TIME_BUDGET:
            break
        elapsed += _dist(GOAL, pos) * TIME_MOVE + TIME_TURN + TIME_DEPOSIT
        pos = GOAL
        path.append(pos)
        if elapsed <= TIME_BUDGET:
            scored += 1
        else:
            break
    return path, scored, elapsed


def eval_policy(policy: Policy, n_samples: int = 100, base_seed: int = 0):
    scores = []
    times = []
    for s in range(n_samples):
        balls = sample_field(base_seed * 10000 + s)
        _, sc, t = simulate(policy, balls)
        scores.append(sc)
        times.append(t)
    mean = sum(scores) / len(scores)
    var = sum((x - mean) ** 2 for x in scores) / len(scores)
    return mean, math.sqrt(var), sum(times) / len(times)


def baseline_policy() -> Policy:
    return Policy(
        order=tuple(range(N_BALLS)),
        margin=(0.0,) * N_BALLS,
        skip_thresh=0.0,
    )


def random_policy(rng: random.Random) -> Policy:
    order = list(range(N_BALLS))
    rng.shuffle(order)
    margin = tuple(rng.uniform(0, 2) for _ in range(N_BALLS))
    skip = rng.uniform(0, 15)
    return Policy(order=tuple(order), margin=margin, skip_thresh=skip)


def mutate(p: Policy, rng: random.Random, rate: float = 0.15) -> Policy:
    order = list(p.order)
    if rng.random() < rate:
        i, j = rng.sample(range(N_BALLS), 2)
        order[i], order[j] = order[j], order[i]
    margin = tuple(
        max(0, min(2, m + rng.gauss(0, 0.2))) if rng.random() < rate else m
        for m in p.margin
    )
    skip = (
        max(0, min(15, p.skip_thresh + rng.gauss(0, 1)))
        if rng.random() < rate
        else p.skip_thresh
    )
    return Policy(order=tuple(order), margin=margin, skip_thresh=skip)


def fitness(p: Policy) -> float:
    mean, std, t = eval_policy(p, n_samples=40, base_seed=1)
    return mean - 0.35 * std - 0.003 * t


def evolve(
    generations: int = 50,
    pop_size: int = 30,
    seed: int = 42,
) -> tuple[Policy, list[float], list[float]]:
    rng = random.Random(seed)
    pop = [random_policy(rng) for _ in range(pop_size)]
    best_history = []
    mean_history = []
    for gen in range(generations):
        scored = sorted(pop, key=fitness, reverse=True)
        fits = [fitness(p) for p in scored]
        best_history.append(fits[0])
        mean_history.append(sum(fits) / len(fits))
        elite = scored[: pop_size // 5]
        children = []
        while len(children) < pop_size - len(elite):
            parent = rng.choice(elite)
            children.append(mutate(parent, rng))
        pop = elite + children
    best = max(pop, key=fitness)
    return best, best_history, mean_history
