"""LLM coach — explain evolved policy in plain language for kids/parents."""
from __future__ import annotations

import os

from openai import OpenAI


def _client() -> OpenAI:
    token = os.getenv("AI_BUILDER_TOKEN", "")
    base_url = os.getenv("AI_BUILDER_BASE_URL", "https://space.ai-builders.com/backend/v1")
    return OpenAI(base_url=base_url, api_key=token)


SYSTEM_PROMPT = """你是 AlphaGo Coding Lab 的小教练。
你跟 11-14 岁的 VEX IQ 选手讲话。说人话, 短句, 不堆数学术语。

你的任务: 看到一个 VEX 机器人策略, 帮孩子和家长理解为什么这个策略赢。
特别强调"AlphaGo Move 37 时刻" —— 那种"看起来怪, 但跑出来就是对"的步骤。

风格: 简体中文, 2-3 段, 每段 1-2 句话, 总共不超过 150 字。
"""


def explain_policy(
    *,
    order: list[int],
    margin: list[float],
    skip_thresh: float,
    baseline_score: float,
    evolved_score: float,
    baseline_time: float,
    evolved_time: float,
    model: str | None = None,
) -> str:
    model = model or os.getenv("AI_BUILDER_MODEL", "grok-4-fast")
    user_msg = f"""
学员刚跑完 AlphaGo Coding Lab 的训练。

环境: 7 个球 / 35 秒时限 / 30x30 inch 场地, 球位置有 ±3 inch 噪声。

Baseline (孩子硬编路径, 按 0-1-2-3-4-5-6 顺序访问): 平均 {baseline_score:.2f} / 7 球, 用时 {baseline_time:.1f} 秒
AlphaGo 式自学策略: 平均 {evolved_score:.2f} / 7 球 (+{(evolved_score - baseline_score) / max(baseline_score, 0.01) * 100:.0f}%), 用时 {evolved_time:.1f} 秒

自学出的策略:
- 访问顺序: {order} (顺着球编号 0-6 排开是 baseline)
- 每个球的 approach margin (绕开多少, 0=直接撞): {[round(m, 2) for m in margin]}
- 剩多少秒时放弃剩余球直接 deposit: {skip_thresh:.1f}

请告诉孩子和家长: 为什么这个策略赢? 哪一步是"Move 37" 那种奇怪但有效的选择?
"""
    client = _client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=400,
        temperature=0.7,
    )
    return resp.choices[0].message.content or ""
