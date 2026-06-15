const els = {
  statusBadge: document.querySelector("#statusBadge"),
  elapsed: document.querySelector("#elapsed"),
  top: document.querySelector("#top"),
  rtl: document.querySelector("#rtl"),
  liberty: document.querySelector("#liberty"),
  clock: document.querySelector("#clock"),
  period: document.querySelector("#period"),
  sdc: document.querySelector("#sdc"),
  outDir: document.querySelector("#outDir"),
  yosysBin: document.querySelector("#yosysBin"),
  staBin: document.querySelector("#staBin"),
  runBtn: document.querySelector("#runBtn"),
  stopBtn: document.querySelector("#stopBtn"),
  fillCounter: document.querySelector("#fillCounter"),
  fillMulti: document.querySelector("#fillMulti"),
  copyCli: document.querySelector("#copyCli"),
  cliCommand: document.querySelector("#cliCommand"),
  clearLog: document.querySelector("#clearLog"),
  message: document.querySelector("#message"),
  log: document.querySelector("#log"),
  wns: document.querySelector("#wns"),
  tns: document.querySelector("#tns"),
  risk: document.querySelector("#risk"),
  runStatus: document.querySelector("#runStatus"),
  netlistPath: document.querySelector("#netlistPath"),
  summaryPath: document.querySelector("#summaryPath"),
  checksPath: document.querySelector("#checksPath"),
  riskText: document.querySelector("#riskText"),
  violationIntro: document.querySelector("#violationIntro"),
  violationRows: document.querySelector("#violationRows"),
  riskWarnings: document.querySelector("#riskWarnings"),
  lintRtl: document.querySelector("#lintRtl"),
  lintInclude: document.querySelector("#lintInclude"),
  lintTop: document.querySelector("#lintTop"),
  lintDefines: document.querySelector("#lintDefines"),
  lintSdc: document.querySelector("#lintSdc"),
  lintRules: document.querySelector("#lintRules"),
  lintOutDir: document.querySelector("#lintOutDir"),
  lintRunBtn: document.querySelector("#lintRunBtn"),
  fillLintClean: document.querySelector("#fillLintClean"),
  lintElapsed: document.querySelector("#lintElapsed"),
  lintMessage: document.querySelector("#lintMessage"),
  lintErrors: document.querySelector("#lintErrors"),
  lintWarnings: document.querySelector("#lintWarnings"),
  lintUnsupported: document.querySelector("#lintUnsupported"),
  lintStatus: document.querySelector("#lintStatus"),
  lintSummaryPath: document.querySelector("#lintSummaryPath"),
  lintRiskText: document.querySelector("#lintRiskText"),
  lintLog: document.querySelector("#lintLog"),
  lintDiagnosticRows: document.querySelector("#lintDiagnosticRows"),
};

let currentJobId = null;
let eventSource = null;
let localTimer = null;
let localStartedAt = null;
let lintEventSource = null;

function setStatus(kind, text) {
  els.statusBadge.className = `badge ${kind}`;
  els.statusBadge.textContent = text;
  els.runStatus.textContent = text;
}

function setMessage(text, kind = "") {
  els.message.className = `message ${kind}`;
  els.message.textContent = text;
}

function appendLog(line) {
  if (!line) return;
  els.log.textContent += `${line}\n`;
  els.log.scrollTop = els.log.scrollHeight;
}

function fmt(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(4);
  return String(value);
}

function riskLabel(value) {
  if (value === "LOW") return "低风险";
  if (value === "MEDIUM") return "中风险";
  if (value === "HIGH") return "高风险";
  return "-";
}

function updateElapsed(seconds) {
  els.elapsed.textContent = `耗时 ${fmt(seconds)}s`;
}

function startLocalTimer() {
  localStartedAt = performance.now();
  clearInterval(localTimer);
  localTimer = setInterval(() => {
    if (localStartedAt) {
      updateElapsed((performance.now() - localStartedAt) / 1000);
    }
  }, 200);
}

function stopLocalTimer() {
  clearInterval(localTimer);
  localTimer = null;
  localStartedAt = null;
}

function collectPayload() {
  const rtl = els.rtl.value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
  return {
    top: els.top.value.trim(),
    rtl,
    liberty_file: els.liberty.value.trim(),
    clock: els.clock.value.trim(),
    period: els.period.value.trim(),
    sdc: els.sdc.value.trim(),
    out_dir: els.outDir.value.trim(),
    yosys_bin: els.yosysBin.value.trim() || "yosys",
    sta_bin: els.staBin.value.trim() || "sta",
    max_paths: 5,
  };
}

function splitList(value) {
  return value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function validatePayload(payload) {
  const errors = [];
  if (!payload.top) errors.push("请填写顶层模块。");
  if (!payload.rtl.length) errors.push("请至少填写一个 RTL Verilog 文件或 glob。");
  if (!payload.liberty_file) errors.push("请填写 Liberty 文件路径。");
  if (!payload.out_dir) errors.push("请填写输出目录。");
  if (!payload.yosys_bin) errors.push("请填写 Yosys 命令。");
  if (!payload.sta_bin) errors.push("请填写 OpenSTA 命令。");
  if (!payload.sdc) {
    if (!payload.clock) errors.push("未提供 SDC 时，请填写时钟名。");
    const period = Number(payload.period);
    if (!payload.period || !Number.isFinite(period) || period <= 0) {
      errors.push("未提供 SDC 时，时钟周期必须是正数。");
    }
  }
  return errors;
}

function collectLintPayload() {
  return {
    rtl: splitList(els.lintRtl.value),
    top: els.lintTop.value.trim(),
    include_dirs: splitList(els.lintInclude.value),
    defines: splitList(els.lintDefines.value),
    sdc_file: els.lintSdc.value.trim(),
    rules_file: els.lintRules.value.trim(),
    out_dir: els.lintOutDir.value.trim(),
  };
}

function validateLintPayload(payload) {
  const errors = [];
  if (!payload.rtl.length) errors.push("请至少填写一个 RTL 文件或 glob。");
  if (!payload.out_dir) errors.push("请填写 Lint 输出目录。");
  return errors;
}

function shellQuote(value) {
  const text = String(value);
  if (/^[A-Za-z0-9_./:=+-]+$/.test(text)) return text;
  return "'" + text.replace(/'/g, "'\"'\"'") + "'";
}

function buildCliCommand(payload) {
  const parts = ["./sta-lite", "analyze", "--top", shellQuote(payload.top || "<top>")];
  parts.push("--rtl");
  if (payload.rtl.length) {
    payload.rtl.forEach((item) => {
      parts.push(shellQuote(item));
    });
  } else {
    parts.push(shellQuote("<rtl.v>"));
  }
  parts.push("--lib", shellQuote(payload.liberty_file || "<liberty.lib>"));
  if (payload.sdc) {
    parts.push("--sdc", shellQuote(payload.sdc));
  } else {
    parts.push("--clock", shellQuote(payload.clock || "<clock>"));
    parts.push("--period", shellQuote(payload.period || "<period_ns>"));
  }
  parts.push("--out", shellQuote(payload.out_dir || "<out_dir>"));
  if (payload.yosys_bin && payload.yosys_bin !== "yosys") {
    parts.push("--yosys-bin", shellQuote(payload.yosys_bin));
  }
  if (payload.sta_bin && payload.sta_bin !== "sta") {
    parts.push("--sta-bin", shellQuote(payload.sta_bin));
  }
  return parts.join(" ");
}

function updateCliCommand() {
  els.cliCommand.textContent = buildCliCommand(collectPayload());
}

function resetResult() {
  els.wns.textContent = "-";
  els.tns.textContent = "-";
  els.risk.textContent = "-";
  els.netlistPath.textContent = "-";
  els.summaryPath.textContent = "-";
  els.checksPath.textContent = "-";
  els.riskText.textContent = "-";
  els.violationIntro.textContent = "分析运行中，完成后这里会显示负 slack 路径和高风险提示。";
  els.violationRows.innerHTML = "";
  els.riskWarnings.innerHTML = "";
}

function resetLintResult() {
  els.lintElapsed.textContent = "耗时 0.0s";
  els.lintErrors.textContent = "-";
  els.lintWarnings.textContent = "-";
  els.lintUnsupported.textContent = "-";
  els.lintStatus.textContent = "运行中";
  els.lintSummaryPath.textContent = "-";
  els.lintRiskText.textContent = "-";
  els.lintDiagnosticRows.innerHTML = "";
}

function renderSummary(summary) {
  if (!summary) return;
  els.wns.textContent = fmt(summary.wns);
  els.tns.textContent = fmt(summary.tns);
  els.risk.textContent = riskLabel(summary.risk_level);
  els.netlistPath.textContent = summary.generated_netlist || "-";
  els.summaryPath.textContent = summary.artifacts?.summary_json || "-";
  els.checksPath.textContent = summary.artifacts?.checks_report || "-";
  els.riskText.textContent = summary.risk_explanation_zh || "-";
  updateElapsed(summary.elapsed_seconds || 0);
  renderViolations(summary);
}

function renderViolations(summary) {
  const rows = summary.timing_violations?.length
    ? summary.timing_violations
    : (summary.worst_paths || []).filter((path) => typeof path.slack === "number" && path.slack < 0);
  els.violationRows.innerHTML = "";
  rows.forEach((path) => {
    const tr = document.createElement("tr");
    [path.startpoint, path.endpoint, path.path_group, path.slack, path.arrival_time, path.required_time].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = fmt(value);
      tr.appendChild(td);
    });
    els.violationRows.appendChild(tr);
  });

  const hardCategories = new Set([
    "negative_slack_violation",
    "missing_module_or_reference",
    "no_clock_or_missing_clock",
    "unconstrained_paths",
    "link_error",
    "missing_liberty_cell_or_pin",
    "tool_error",
  ]);
  const warnings = [...(summary.yosys_warnings || []), ...(summary.opensta_warnings || [])]
    .filter((item) => summary.risk_level === "HIGH" || hardCategories.has(item.category))
    .slice(0, 20);

  els.riskWarnings.innerHTML = "";
  warnings.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = `${item.category}: ${item.message}`;
    els.riskWarnings.appendChild(li);
  });

  if (rows.length) {
    els.violationIntro.textContent = `发现 ${rows.length} 条负 slack 路径，需优先处理。`;
  } else if (summary.risk_level === "HIGH") {
    els.violationIntro.textContent = "未解析到负 slack 路径，但存在高风险日志或约束问题。";
  } else {
    els.violationIntro.textContent = "未发现负 slack 路径。高风险提示为空时，当前报告没有独立违例项。";
  }
}

function renderLintSummary(summary) {
  if (!summary) return;
  els.lintElapsed.textContent = `耗时 ${fmt(summary.elapsed_seconds)}s`;
  els.lintErrors.textContent = fmt(summary.error_count);
  els.lintWarnings.textContent = fmt(summary.warning_count);
  els.lintUnsupported.textContent = fmt(summary.unsupported_count);
  if (summary.error_count || summary.unsupported_count) {
    els.lintStatus.textContent = "失败";
  } else if (summary.warning_count) {
    els.lintStatus.textContent = "有警告";
  } else {
    els.lintStatus.textContent = "通过";
  }
  els.lintSummaryPath.textContent = summary.artifacts?.lint_summary_json || "-";
  els.lintRiskText.textContent = summary.risk_explanation_zh || "-";
  els.lintDiagnosticRows.innerHTML = "";
  (summary.diagnostics || []).slice(0, 120).forEach((item) => {
    const tr = document.createElement("tr");
    const location = `${item.file}:${item.line}:${item.column}`;
    [item.severity, item.rule, location, item.message_zh, item.suggestion_zh].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = fmt(value);
      tr.appendChild(td);
    });
    els.lintDiagnosticRows.appendChild(tr);
  });
}

async function startRun() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  const payload = collectPayload();
  const errors = validatePayload(payload);
  if (errors.length) {
    setStatus("failure", "输入错误");
    setMessage(errors.join(" "), "error");
    return;
  }
  els.log.textContent = "";
  resetResult();
  setMessage("");
  setStatus("running", "运行中");
  els.runBtn.disabled = true;
  els.stopBtn.disabled = false;
  startLocalTimer();

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "启动失败");
    }
    currentJobId = data.job_id;
    connectEvents(currentJobId);
  } catch (err) {
    stopLocalTimer();
    setStatus("failure", "失败");
    setMessage(`启动分析失败：${err.message}`, "error");
    els.runBtn.disabled = false;
    els.stopBtn.disabled = true;
  }
}

function connectEvents(jobId) {
  eventSource = new EventSource(`/api/events?id=${encodeURIComponent(jobId)}`);

  eventSource.addEventListener("status", (event) => {
    const data = JSON.parse(event.data);
    appendLog(`[sta-lite] ${data.message || data.status}`);
  });

  eventSource.addEventListener("elapsed", (event) => {
    const data = JSON.parse(event.data);
    updateElapsed(data.elapsed_seconds || 0);
  });

  eventSource.addEventListener("log", (event) => {
    const data = JSON.parse(event.data);
    appendLog(data.line);
    if (data.elapsed_seconds !== undefined) updateElapsed(data.elapsed_seconds);
  });

  eventSource.addEventListener("summary", (event) => {
    const data = JSON.parse(event.data);
    stopLocalTimer();
    renderSummary(data.summary);
    setStatus(data.summary.risk_level === "HIGH" ? "failure" : "success", "完成");
    setMessage("分析完成，summary.json 和原始报告已保存。", "ok");
    els.runBtn.disabled = false;
    els.stopBtn.disabled = true;
    eventSource.close();
  });

  eventSource.addEventListener("error", (event) => {
    stopLocalTimer();
    if (event.data) {
      const data = JSON.parse(event.data);
      if (data.summary) renderSummary(data.summary);
      setMessage(data.message || "分析失败。", "error");
    } else {
      setMessage("日志连接中断。", "error");
    }
    setStatus("failure", "失败");
    els.runBtn.disabled = false;
    els.stopBtn.disabled = true;
    eventSource.close();
  });
}

async function stopRun() {
  if (!currentJobId) return;
  await fetch(`/api/stop/${encodeURIComponent(currentJobId)}`, { method: "POST" });
  setMessage("已请求停止当前分析。");
}

async function startLintRun() {
  if (lintEventSource) {
    lintEventSource.close();
    lintEventSource = null;
  }
  const payload = collectLintPayload();
  const errors = validateLintPayload(payload);
  if (errors.length) {
    els.lintMessage.className = "message error";
    els.lintMessage.textContent = errors.join(" ");
    return;
  }
  els.lintLog.textContent = "";
  resetLintResult();
  els.lintMessage.className = "message";
  els.lintMessage.textContent = "";
  els.lintRunBtn.disabled = true;
  try {
    const response = await fetch("/api/lint_run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "启动 RTL Lint 失败");
    }
    connectLintEvents(data.job_id);
  } catch (err) {
    els.lintMessage.className = "message error";
    els.lintMessage.textContent = `启动 RTL Lint 失败：${err.message}`;
    els.lintStatus.textContent = "失败";
    els.lintRunBtn.disabled = false;
  }
}

function connectLintEvents(jobId) {
  lintEventSource = new EventSource(`/api/lint_events?id=${encodeURIComponent(jobId)}`);

  lintEventSource.addEventListener("status", (event) => {
    const data = JSON.parse(event.data);
    els.lintLog.textContent += `[sta-lite lint] ${data.message || data.status}\n`;
    els.lintLog.scrollTop = els.lintLog.scrollHeight;
  });

  lintEventSource.addEventListener("log", (event) => {
    const data = JSON.parse(event.data);
    els.lintLog.textContent += `${data.line}\n`;
    els.lintLog.scrollTop = els.lintLog.scrollHeight;
    if (data.elapsed_seconds !== undefined) {
      els.lintElapsed.textContent = `耗时 ${fmt(data.elapsed_seconds)}s`;
    }
  });

  lintEventSource.addEventListener("elapsed", (event) => {
    const data = JSON.parse(event.data);
    els.lintElapsed.textContent = `耗时 ${fmt(data.elapsed_seconds || 0)}s`;
  });

  lintEventSource.addEventListener("summary", (event) => {
    const data = JSON.parse(event.data);
    renderLintSummary(data.summary);
    els.lintMessage.className = data.summary.error_count || data.summary.unsupported_count ? "message error" : "message ok";
    els.lintMessage.textContent = "RTL Lint 完成，lint_summary.json 已保存。";
    els.lintRunBtn.disabled = false;
    lintEventSource.close();
  });

  lintEventSource.addEventListener("error", (event) => {
    if (event.data) {
      const data = JSON.parse(event.data);
      if (data.summary) renderLintSummary(data.summary);
      els.lintMessage.textContent = data.message || "RTL Lint 失败。";
    } else {
      els.lintMessage.textContent = "RTL Lint 日志连接中断。";
    }
    els.lintMessage.className = "message error";
    els.lintStatus.textContent = "失败";
    els.lintRunBtn.disabled = false;
    lintEventSource.close();
  });
}

async function copyCliCommand() {
  const text = els.cliCommand.textContent;
  try {
    if (!navigator.clipboard?.writeText) {
      throw new Error("当前浏览器未开放剪贴板接口");
    }
    await navigator.clipboard.writeText(text);
    setMessage("等效 CLI 命令已复制。", "ok");
  } catch (err) {
    setMessage("浏览器不允许直接复制，请手动选中命令复制。", "error");
  }
}

els.runBtn.addEventListener("click", startRun);
els.stopBtn.addEventListener("click", stopRun);
els.lintRunBtn.addEventListener("click", startLintRun);
els.copyCli.addEventListener("click", copyCliCommand);
els.clearLog.addEventListener("click", () => {
  els.log.textContent = "";
});
els.fillCounter.addEventListener("click", () => {
  els.top.value = "counter";
  els.rtl.value = "examples/counter/counter.v";
  els.liberty.value = "nangate45/lib/NangateOpenCellLibrary_typical.lib";
  els.clock.value = "clk";
  els.period.value = "2.0";
  els.sdc.value = "";
  els.outDir.value = "runs/gui_counter";
  updateCliCommand();
});

els.fillMulti.addEventListener("click", () => {
  els.top.value = "multi_top";
  els.rtl.value = "examples/multi_file/rtl/*.v";
  els.liberty.value = "nangate45/lib/NangateOpenCellLibrary_typical.lib";
  els.clock.value = "clk";
  els.period.value = "2.5";
  els.sdc.value = "";
  els.outDir.value = "runs/gui_multi_file";
  updateCliCommand();
});

els.fillLintClean.addEventListener("click", () => {
  els.lintRtl.value = "examples/lint/clean_ok/clean_ok.sv";
  els.lintTop.value = "clean_ok";
  els.lintInclude.value = "";
  els.lintDefines.value = "";
  els.lintSdc.value = "";
  els.lintRules.value = "";
  els.lintOutDir.value = "runs/gui_lint_clean_ok";
});

[els.top, els.rtl, els.liberty, els.clock, els.period, els.sdc, els.outDir, els.yosysBin, els.staBin].forEach((input) => {
  input.addEventListener("input", updateCliCommand);
  input.addEventListener("change", updateCliCommand);
});

updateCliCommand();
