const $ = (id) => document.getElementById(id);

let lastResult = null;

async function runEvolve() {
  const btn = $("run-btn");
  btn.disabled = true;
  $("status").textContent = "训练中… (10-30 秒)";
  const body = {
    generations: parseInt($("generations").value, 10),
    pop_size: parseInt($("pop_size").value, 10),
    seed: parseInt($("seed").value, 10),
  };
  try {
    const resp = await fetch("/api/evolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    lastResult = data;
    renderResults(data);
    $("status").textContent = `完成. 后端用时 ${data.elapsed_secs.toFixed(1)} 秒.`;
    $("results").classList.remove("hidden");
    $("coach-section").classList.remove("hidden");
  } catch (err) {
    $("status").textContent = `错误: ${err.message}`;
  } finally {
    btn.disabled = false;
  }
}

function renderResults(d) {
  $("b-mean").textContent = d.baseline_mean.toFixed(2);
  $("b-time").textContent = d.baseline_time.toFixed(1);
  $("e-mean").textContent = d.evolved_mean.toFixed(2);
  $("e-time").textContent = d.evolved_time.toFixed(1);

  const pct = ((d.evolved_mean - d.baseline_mean) / Math.max(d.baseline_mean, 0.01)) * 100;
  const tpct = ((d.evolved_time - d.baseline_time) / Math.max(d.baseline_time, 0.01)) * 100;
  $("delta-pct").textContent = `${pct >= 0 ? "+" : ""}${pct.toFixed(0)}%`;
  $("delta-time").textContent = `${tpct >= 0 ? "+" : ""}${tpct.toFixed(0)}%`;

  $("traj-img").src = "data:image/png;base64," + d.trajectory_png_b64;
  $("fitness-img").src = "data:image/png;base64," + d.fitness_png_b64;
  $("policy-json").textContent = JSON.stringify(d.policy, null, 2);
}

async function runCoach() {
  if (!lastResult) return;
  const btn = $("coach-btn");
  btn.disabled = true;
  $("coach-status").textContent = "教练思考中…";
  $("coach-text").textContent = "";
  try {
    const resp = await fetch("/api/coach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        order: lastResult.policy.order,
        margin: lastResult.policy.margin,
        skip_thresh: lastResult.policy.skip_thresh,
        baseline_score: lastResult.baseline_mean,
        evolved_score: lastResult.evolved_mean,
        baseline_time: lastResult.baseline_time,
        evolved_time: lastResult.evolved_time,
      }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status} ${await resp.text()}`);
    const data = await resp.json();
    $("coach-text").textContent = data.explanation;
    $("coach-status").textContent = "";
  } catch (err) {
    $("coach-status").textContent = `错误: ${err.message}`;
  } finally {
    btn.disabled = false;
  }
}

$("run-btn").addEventListener("click", runEvolve);
$("coach-btn").addEventListener("click", runCoach);
