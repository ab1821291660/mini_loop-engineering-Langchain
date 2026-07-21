const $ = (id) => document.getElementById(id);

let seedDocs = {};
let initialConfig = null;

function setStatus(msg, isError = false) {
  const el = $("status");
  el.textContent = msg;
  el.style.color = isError ? "var(--fail)" : "var(--muted)";
}

function renderCapabilities(harness) {
  const root = $("capabilities");
  const caps = harness.capabilities || [];
  const tools = (harness.filesystem_tools || []).map((t) => `<code>${t}</code>`).join(" ");
  root.innerHTML = `
    ${caps
      .map(
        (c) => `
      <article class="part fixed">
        <header>
          <span class="part-tag">built-in</span>
          <h3>${c.title}</h3>
        </header>
        <p class="part-note">${c.detail}</p>
      </article>`
      )
      .join("")}
    <article class="part fixed">
      <header>
        <span class="part-tag">built-in</span>
        <h3>Tools</h3>
      </header>
      <p class="part-body tools-inline">${tools}</p>
    </article>
  `;
}

function renderTasks(tasks) {
  $("tasks").innerHTML = tasks
    .map(
      (t) => `
      <article class="task-card">
        <strong>${t.id}</strong>
        <p class="hint-line">${t.title || ""}</p>
        <p>${t.request}</p>
        <p class="hint-line">verify: <code>${t.test_path}</code> · ${t.failure_hint}</p>
      </article>`
    )
    .join("");
}

function renderDocs(docs) {
  seedDocs = docs;
  const select = $("doc-select");
  const paths = Object.keys(docs).sort();
  select.innerHTML = paths.map((p) => `<option value="${p}">${p}</option>`).join("");
  $("doc-view").textContent = docs[paths[0]] || "";
  select.onchange = () => {
    $("doc-view").textContent = seedDocs[select.value] || "";
  };
}

function renderRepoFiles(repo) {
  if (!repo?.files || !Object.keys(repo.files).length) {
    return `<div class="repo-empty">No file edits this ticket.</div>`;
  }
  return Object.entries(repo.files)
    .map(([path, file]) => {
      const before = file.before ?? "(file did not exist)";
      const after = file.after ?? "(file deleted)";
      return `
        <details class="repo-file" open>
          <summary>
            <code>${escapeHtml(path)}</code>
            <span class="chip muted">${file.changed ? "changed" : "same"}</span>
          </summary>
          <div class="repo-diff">
            <div>
              <h4>Before (seed)</h4>
              <pre>${escapeHtml(before)}</pre>
            </div>
            <div>
              <h4>After (this iteration)</h4>
              <pre>${escapeHtml(after)}</pre>
            </div>
          </div>
        </details>`;
    })
    .join("");
}

function renderHistory(history) {
  const root = $("history");
  if (!history?.length) {
    root.className = "history empty";
    root.innerHTML = "<p>No iterations yet.</p>";
    return;
  }
  root.className = "history";
  root.innerHTML = history
    .map((iter) => {
      const rows = (iter.task_results || [])
        .map(
          (t) => `
        <div class="task-row">
          <div class="verdict ${t.verdict}">${t.verdict}</div>
          <div>
            <strong>${t.task_id}</strong>
            <div>${escapeHtml(t.feedback || "")}</div>
            <div class="meta">
              tools: ${(t.tools_called || []).join(", ") || "none"}
              · read: ${(t.read_paths || []).join(", ") || "—"}
              · edited: ${(t.edited_paths || []).join(", ") || "—"}
            </div>
            ${
              (t.execute_commands || []).length
                ? `<div class="meta">execute: ${escapeHtml(
                    (t.execute_commands || []).join(" | ")
                  )}</div>`
                : ""
            }
            ${
              t.pytest_output
                ? `<pre class="pytest-tail">${escapeHtml(t.pytest_output).slice(0, 600)}</pre>`
                : ""
            }
            <div class="repo-block">
              <div class="repo-block-head">Repo after this ticket</div>
              ${renderRepoFiles(t.repo)}
            </div>
          </div>
        </div>`
        )
        .join("");
      const rationale = iter.improve_rationale
        ? `<div class="rationale"><strong>Config rewrite</strong> — ${escapeHtml(
            iter.improve_rationale
          )}</div>`
        : `<div class="rationale muted">No config rewrite this iteration.</div>`;
      return `
        <article class="iteration">
          <div class="iteration-head">
            <strong>Iteration ${iter.iteration}</strong>
            <span>${iter.passed}/${iter.total} · ${(iter.pass_rate * 100).toFixed(0)}%</span>
          </div>
          ${rows}
          ${rationale}
        </article>`;
    })
    .join("");
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function formatConfig(cfg) {
  if (!cfg) return "";
  return `enable_shell: ${Boolean(cfg.enable_shell)}\n\n${cfg.system_prompt || ""}`;
}

async function bootstrap() {
  const res = await fetch("/api/bootstrap");
  if (!res.ok) throw new Error("Failed to load bootstrap");
  const data = await res.json();

  initialConfig = data.config;
  if (data.definition) $("definition").textContent = data.definition;
  if (data.use_case) $("use-case").textContent = data.use_case;
  $("harness-chip").textContent = data.harness.factory || "create_deep_agent";
  renderCapabilities(data.harness);
  $("system_prompt").value = data.config.system_prompt;
  $("enable_shell").checked = Boolean(data.config.enable_shell);
  $("model-line").textContent = `Model: ${data.model}`;
  $("max_iterations").value = data.max_iterations;
  $("target_pass_rate").value = data.target_pass_rate;
  $("config-before").textContent = formatConfig(data.config);
  $("config-after").textContent = "After a run, the rewritten config appears here.";
  renderTasks(data.tasks);
  renderDocs(data.seed_docs);
}

async function runLoop() {
  const btn = $("btn-run");
  btn.disabled = true;
  setStatus("Running weak config → pytest fail → improve… (a few minutes)");
  $("iter-chip").textContent = "running…";
  $("pass-fill").style.width = "0%";
  $("pass-label").textContent = "…";

  try {
    const res = await fetch("/api/run-loop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_prompt: $("system_prompt").value,
        enable_shell: $("enable_shell").checked,
        max_iterations: Number($("max_iterations").value),
        target_pass_rate: Number($("target_pass_rate").value),
        reset_traces: true,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Run failed");

    const rate = Math.round((data.final_pass_rate || 0) * 100);
    $("pass-fill").style.width = `${rate}%`;
    $("pass-label").textContent = `${rate}%`;
    $("stop-reason").textContent = data.stop_reason || "";
    $("iter-chip").textContent = `${data.history?.length || 0} iteration(s)`;
    $("config-before").textContent = formatConfig(data.initial_config);
    $("config-after").textContent = formatConfig(data.final_config);
    $("system_prompt").value = data.final_config.system_prompt;
    $("enable_shell").checked = Boolean(data.final_config.enable_shell);
    renderHistory(data.history);
    setStatus(`Done. ${data.stop_reason}`);
  } catch (err) {
    setStatus(String(err.message || err), true);
    $("iter-chip").textContent = "error";
  } finally {
    btn.disabled = false;
  }
}

function resetConfig() {
  if (!initialConfig) return;
  $("system_prompt").value = initialConfig.system_prompt;
  $("enable_shell").checked = Boolean(initialConfig.enable_shell);
  $("config-before").textContent = formatConfig(initialConfig);
  $("config-after").textContent = "After a run, the rewritten config appears here.";
  setStatus("Restored weak starter config (no shell).");
}

$("btn-run").addEventListener("click", runLoop);
$("btn-reset").addEventListener("click", resetConfig);
bootstrap().catch((err) => setStatus(String(err.message || err), true));
