"""FastAPI app: AlphaGo Coding Lab — VEX MetaHarness Playground."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import coach, export, simulation as sim, viz


app = FastAPI(title="AlphaGo Coding Lab — VEX Playground")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class EvolveRequest(BaseModel):
    generations: int = Field(50, ge=5, le=200)
    pop_size: int = Field(30, ge=5, le=80)
    seed: int = Field(42)


class EvolveResponse(BaseModel):
    policy: dict
    baseline_mean: float
    baseline_std: float
    baseline_time: float
    evolved_mean: float
    evolved_std: float
    evolved_time: float
    fitness_history: list[float]
    mean_history: list[float]
    trajectory_png_b64: str
    fitness_png_b64: str
    elapsed_secs: float


class CoachRequest(BaseModel):
    order: list[int]
    margin: list[float]
    skip_thresh: float
    baseline_score: float
    evolved_score: float
    baseline_time: float
    evolved_time: float


class CoachResponse(BaseModel):
    explanation: str


class ExportRequest(BaseModel):
    order: list[int]
    margin: list[float]
    skip_thresh: float
    baseline_mean: float
    evolved_mean: float
    evolved_time: float
    generations: int = 50
    fmt: str = Field("vexcode_py", description="vexcode_py or vexcode_blocks")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "model": os.getenv("AI_BUILDER_MODEL", "grok-4-fast"),
        "has_token": bool(os.getenv("AI_BUILDER_TOKEN")),
        "task": {
            "n_balls": sim.N_BALLS,
            "time_budget": sim.TIME_BUDGET,
            "field": sim.FIELD,
        },
    }


@app.post("/api/evolve", response_model=EvolveResponse)
def run_evolve(req: EvolveRequest):
    t0 = time.time()
    baseline = sim.baseline_policy()
    bm, bs, bt = sim.eval_policy(baseline, n_samples=200, base_seed=7)

    best, best_hist, mean_hist = sim.evolve(
        generations=req.generations,
        pop_size=req.pop_size,
        seed=req.seed,
    )
    em, es, et = sim.eval_policy(best, n_samples=200, base_seed=7)

    traj_png = viz.trajectory_compare_png(baseline, best)
    fit_png = viz.fitness_curve_png(best_hist, mean_hist)

    return EvolveResponse(
        policy=best.to_dict(),
        baseline_mean=bm,
        baseline_std=bs,
        baseline_time=bt,
        evolved_mean=em,
        evolved_std=es,
        evolved_time=et,
        fitness_history=best_hist,
        mean_history=mean_hist,
        trajectory_png_b64=traj_png,
        fitness_png_b64=fit_png,
        elapsed_secs=time.time() - t0,
    )


@app.post("/api/export")
def run_export(req: ExportRequest):
    policy = sim.Policy(
        order=tuple(req.order),
        margin=tuple(req.margin),
        skip_thresh=req.skip_thresh,
    )
    if req.fmt == "vexcode_py":
        body = export.policy_to_vexcode_python(
            policy,
            baseline_mean=req.baseline_mean,
            evolved_mean=req.evolved_mean,
            evolved_time=req.evolved_time,
            n_gen=req.generations,
        )
        return PlainTextResponse(
            body,
            headers={
                "Content-Disposition": "attachment; filename=alphago_autonomous.py",
                "Content-Type": "text/x-python",
            },
        )
    elif req.fmt == "vexcode_blocks":
        body = export.policy_to_vexcode_blocks(
            policy,
            baseline_mean=req.baseline_mean,
            evolved_mean=req.evolved_mean,
        )
        return Response(
            body,
            media_type="application/xml",
            headers={"Content-Disposition": "attachment; filename=alphago_autonomous.xml"},
        )
    else:
        raise HTTPException(400, f"unknown fmt: {req.fmt}")


@app.post("/api/coach", response_model=CoachResponse)
def run_coach(req: CoachRequest):
    if not os.getenv("AI_BUILDER_TOKEN"):
        raise HTTPException(503, "AI_BUILDER_TOKEN not configured")
    try:
        text = coach.explain_policy(
            order=req.order,
            margin=req.margin,
            skip_thresh=req.skip_thresh,
            baseline_score=req.baseline_score,
            evolved_score=req.evolved_score,
            baseline_time=req.baseline_time,
            evolved_time=req.evolved_time,
        )
    except Exception as exc:
        raise HTTPException(502, f"LLM coach failed: {exc}") from exc
    return CoachResponse(explanation=text)
