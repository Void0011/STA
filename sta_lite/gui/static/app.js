const els = {
  navReview: document.querySelector("#navReview"),
  navLint: document.querySelector("#navLint"),
  navProfiling: document.querySelector("#navProfiling"),
  navBackend: document.querySelector("#navBackend"),
  navCoverage: document.querySelector("#navCoverage"),
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
  backendLocationStatus: document.querySelector("#backendLocationStatus"),
  backendToolStatus: document.querySelector("#backendToolStatus"),
  reviewRtl: document.querySelector("#reviewRtl"),
  reviewInclude: document.querySelector("#reviewInclude"),
  reviewTop: document.querySelector("#reviewTop"),
  reviewDefines: document.querySelector("#reviewDefines"),
  reviewSdc: document.querySelector("#reviewSdc"),
  reviewRules: document.querySelector("#reviewRules"),
  reviewGoldDir: document.querySelector("#reviewGoldDir"),
  reviewOutDir: document.querySelector("#reviewOutDir"),
  reviewRunBtn: document.querySelector("#reviewRunBtn"),
  reviewClearBtn: document.querySelector("#reviewClearBtn"),
  reviewCopyOutDir: document.querySelector("#reviewCopyOutDir"),
  reviewCaseSelect: document.querySelector("#reviewCaseSelect"),
  reviewLoadCase: document.querySelector("#reviewLoadCase"),
  fillReviewLongComb: document.querySelector("#fillReviewLongComb"),
  reviewElapsed: document.querySelector("#reviewElapsed"),
  reviewMessage: document.querySelector("#reviewMessage"),
  reviewLintIssues: document.querySelector("#reviewLintIssues"),
  reviewRiskCount: document.querySelector("#reviewRiskCount"),
  reviewTotalIssues: document.querySelector("#reviewTotalIssues"),
  reviewLevel: document.querySelector("#reviewLevel"),
  reviewStatus: document.querySelector("#reviewStatus"),
  reviewLintStatus: document.querySelector("#reviewLintStatus"),
  reviewProfilingStatus: document.querySelector("#reviewProfilingStatus"),
  reviewLintElapsedDetail: document.querySelector("#reviewLintElapsedDetail"),
  reviewProfilingElapsedDetail: document.querySelector("#reviewProfilingElapsedDetail"),
  reviewSummaryPath: document.querySelector("#reviewSummaryPath"),
  reviewReportPath: document.querySelector("#reviewReportPath"),
  reviewLogPath: document.querySelector("#reviewLogPath"),
  reviewLintSummaryPath: document.querySelector("#reviewLintSummaryPath"),
  reviewRiskSummaryPath: document.querySelector("#reviewRiskSummaryPath"),
  reviewGoldText: document.querySelector("#reviewGoldText"),
  reviewReportLocationStatus: document.querySelector("#reviewReportLocationStatus"),
  reviewLog: document.querySelector("#reviewLog"),
  reviewRows: document.querySelector("#reviewRows"),
  reviewSourceFilter: document.querySelector("#reviewSourceFilter"),
  reviewPriorityFilter: document.querySelector("#reviewPriorityFilter"),
  reviewRuleFilter: document.querySelector("#reviewRuleFilter"),
  reviewCategoryFilter: document.querySelector("#reviewCategoryFilter"),
  reviewFileFilter: document.querySelector("#reviewFileFilter"),
  reviewSeverityFilter: document.querySelector("#reviewSeverityFilter"),
  reviewFilteredCount: document.querySelector("#reviewFilteredCount"),
  coverageRefreshBtn: document.querySelector("#coverageRefreshBtn"),
  coverageTotal: document.querySelector("#coverageTotal"),
  coverageP0: document.querySelector("#coverageP0"),
  coverageP1: document.querySelector("#coverageP1"),
  coverageLintOwner: document.querySelector("#coverageLintOwner"),
  coverageProfilingOwner: document.querySelector("#coverageProfilingOwner"),
  coverageBothOwner: document.querySelector("#coverageBothOwner"),
  coverageP0Detail: document.querySelector("#coverageP0Detail"),
  coverageP1Detail: document.querySelector("#coverageP1Detail"),
  coveragePriorityFilter: document.querySelector("#coveragePriorityFilter"),
  coverageOwnerFilter: document.querySelector("#coverageOwnerFilter"),
  coverageCategoryFilter: document.querySelector("#coverageCategoryFilter"),
  coverageStatusFilter: document.querySelector("#coverageStatusFilter"),
  coverageFilteredCount: document.querySelector("#coverageFilteredCount"),
  coverageRows: document.querySelector("#coverageRows"),
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
  riskRtl: document.querySelector("#riskRtl"),
  riskInclude: document.querySelector("#riskInclude"),
  riskTop: document.querySelector("#riskTop"),
  riskDefines: document.querySelector("#riskDefines"),
  riskSdc: document.querySelector("#riskSdc"),
  riskGoldDir: document.querySelector("#riskGoldDir"),
  riskOutDir: document.querySelector("#riskOutDir"),
  riskRunBtn: document.querySelector("#riskRunBtn"),
  riskClearBtn: document.querySelector("#riskClearBtn"),
  riskCopyOutDir: document.querySelector("#riskCopyOutDir"),
  riskCaseSelect: document.querySelector("#riskCaseSelect"),
  riskLoadCase: document.querySelector("#riskLoadCase"),
  fillRiskLongComb: document.querySelector("#fillRiskLongComb"),
  riskElapsed: document.querySelector("#riskElapsed"),
  riskMessage: document.querySelector("#riskMessage"),
  riskCount: document.querySelector("#riskCount"),
  riskLevel: document.querySelector("#riskLevel"),
  riskStatus: document.querySelector("#riskStatus"),
  riskGoldState: document.querySelector("#riskGoldState"),
  riskSummaryPath: document.querySelector("#riskSummaryPath"),
  riskReportPath: document.querySelector("#riskReportPath"),
  riskLogPath: document.querySelector("#riskLogPath"),
  riskGoldText: document.querySelector("#riskGoldText"),
  riskLog: document.querySelector("#riskLog"),
  riskRows: document.querySelector("#riskRows"),
  riskRuleFilter: document.querySelector("#riskRuleFilter"),
  riskSeverityFilter: document.querySelector("#riskSeverityFilter"),
  riskFilteredCount: document.querySelector("#riskFilteredCount"),
};

let currentJobId = null;
let eventSource = null;
let localTimer = null;
let localStartedAt = null;
let lintEventSource = null;
let riskEventSource = null;
let reviewEventSource = null;
let riskCases = [];
let lastRiskSummary = null;
let lastReviewSummary = null;
let coverageCases = [];
let coverageSummary = null;

function switchPage(name) {
  ["review", "lint", "profiling", "backend", "coverage"].forEach((page) => {
    document.body.classList.toggle(`page-${page}`, page === name);
  });
  [els.navReview, els.navLint, els.navProfiling, els.navBackend, els.navCoverage].forEach((button) => {
    button.classList.toggle("active", button.dataset.page === name);
  });
}

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

function collectRiskPayload() {
  return {
    rtl: splitList(els.riskRtl.value),
    top: els.riskTop.value.trim(),
    include_dirs: splitList(els.riskInclude.value),
    defines: splitList(els.riskDefines.value),
    sdc_file: els.riskSdc.value.trim(),
    gold_dir: els.riskGoldDir.value.trim(),
    out_dir: els.riskOutDir.value.trim(),
  };
}

function collectReviewPayload() {
  return {
    rtl: splitList(els.reviewRtl.value),
    top: els.reviewTop.value.trim(),
    include_dirs: splitList(els.reviewInclude.value),
    defines: splitList(els.reviewDefines.value),
    sdc_file: els.reviewSdc.value.trim(),
    rules_file: els.reviewRules.value.trim(),
    gold_dir: els.reviewGoldDir.value.trim(),
    out_dir: els.reviewOutDir.value.trim(),
  };
}

function validateRiskPayload(payload) {
  const errors = [];
  if (!payload.rtl.length) errors.push("请至少填写一个 RTL 文件或 glob。");
  if (!payload.out_dir) errors.push("请填写 Risk 输出目录。");
  return errors;
}

function validateReviewPayload(payload) {
  const errors = [];
  if (!payload.rtl.length) errors.push("请至少填写一个 RTL 文件或 glob。");
  if (!payload.out_dir) errors.push("请填写 RTL Review 输出目录。");
  return errors;
}

async function loadRiskCases() {
  try {
    const response = await fetch("/api/risk_cases");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "读取 risk_profile/cases/ 失败");
    }
    riskCases = Array.isArray(data.cases) ? data.cases : [];
    els.riskCaseSelect.innerHTML = '<option value="">加载 risk_profile/cases/ 用例...</option>';
    els.reviewCaseSelect.innerHTML = '<option value="">加载 risk_profile/cases/ 用例...</option>';
    riskCases.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      const risks = Array.isArray(item.expected_risks) && item.expected_risks.length ? ` / ${item.expected_risks.join(",")}` : "";
      option.textContent = `${item.category || item.id}${risks}`;
      els.riskCaseSelect.appendChild(option);
      els.reviewCaseSelect.appendChild(option.cloneNode(true));
    });
  } catch (err) {
    els.riskMessage.className = "message error";
    els.riskMessage.textContent = `读取 risk_profile/cases/ 用例失败：${err.message}`;
    els.reviewMessage.className = "message error";
    els.reviewMessage.textContent = `读取 risk_profile/cases/ 用例失败：${err.message}`;
  }
}

async function loadBackendStatus() {
  if (!els.backendToolStatus) return;
  try {
    const params = new URLSearchParams({
      yosys: els.yosysBin?.value?.trim() || "yosys",
      sta: els.staBin?.value?.trim() || "sta",
    });
    const response = await fetch(`/api/backend_status?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "检查后端工具失败");
    els.backendToolStatus.textContent = data.message_zh || "后端工具状态未知。";
    els.backendToolStatus.classList.toggle("warning-text", !data.available);
  } catch (err) {
    els.backendToolStatus.textContent = `无法检查后端工具状态：${err.message}。内部 RTL 功能仍可运行。`;
    els.backendToolStatus.classList.add("warning-text");
  }
}

async function loadReviewCoverage() {
  try {
    const response = await fetch("/api/case_coverage");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "读取 Case Coverage 失败");
    }
    coverageCases = Array.isArray(data.cases) ? data.cases : [];
    coverageSummary = data.summary || null;
    populateCoverageCategoryFilter(coverageCases);
    renderCoverageSummary();
    renderCoverageRows();
    const location = data.report_location_status || {};
    if (location.message_zh) {
      els.reviewReportLocationStatus.textContent = location.message_zh;
      if (els.backendLocationStatus) {
        els.backendLocationStatus.textContent = location.message_zh;
      }
    }
  } catch (err) {
    els.reviewMessage.className = "message error";
    els.reviewMessage.textContent = `读取 Case Coverage 失败：${err.message}`;
  }
}

function loadSelectedRiskCase() {
  const selectedId = els.riskCaseSelect.value;
  const item = riskCases.find((candidate) => candidate.id === selectedId);
  if (!item) {
    els.riskMessage.className = "message error";
    els.riskMessage.textContent = "请先选择一个 risk_profile/cases/ 用例。";
    return;
  }
  els.riskRtl.value = (item.files || []).join("\n");
  els.riskTop.value = item.top || "";
  els.riskInclude.value = "";
  els.riskDefines.value = "";
  els.riskSdc.value = item.sdc_file || "";
  els.riskGoldDir.value = "risk_profile/gold/opensta";
  els.riskOutDir.value = item.out_dir || `runs/gui_risk_${item.category || item.id}`;
  els.riskMessage.className = "message ok";
  els.riskMessage.textContent = `已加载用例：${item.description_zh || item.category || item.id}`;
}

function loadSelectedReviewCase() {
  const selectedId = els.reviewCaseSelect.value;
  const item = riskCases.find((candidate) => candidate.id === selectedId);
  if (!item) {
    els.reviewMessage.className = "message error";
    els.reviewMessage.textContent = "请先选择一个 risk_profile/cases/ 用例。";
    return;
  }
  els.reviewRtl.value = (item.files || []).join("\n");
  els.reviewTop.value = item.top || "";
  els.reviewInclude.value = "";
  els.reviewDefines.value = "";
  els.reviewSdc.value = item.sdc_file || "";
  els.reviewRules.value = "";
  els.reviewGoldDir.value = "";
  els.reviewOutDir.value = `runs/gui_review_${item.category || item.id}`;
  els.reviewMessage.className = "message ok";
  els.reviewMessage.textContent = `已加载用例：${item.description_zh || item.category || item.id}`;
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

function resetRiskResult() {
  lastRiskSummary = null;
  els.riskElapsed.textContent = "耗时 0.0s";
  els.riskCount.textContent = "-";
  els.riskLevel.textContent = "-";
  els.riskStatus.textContent = "空闲";
  els.riskGoldState.textContent = "-";
  els.riskSummaryPath.textContent = "-";
  els.riskReportPath.textContent = "-";
  els.riskLogPath.textContent = "-";
  els.riskGoldText.textContent = "-";
  els.riskRows.innerHTML = "";
  resetRiskFilters();
  updateRiskFilterCount(0, 0);
}

function resetReviewResult() {
  lastReviewSummary = null;
  els.reviewElapsed.textContent = "耗时 0.0s";
  els.reviewLintIssues.textContent = "-";
  els.reviewRiskCount.textContent = "-";
  els.reviewTotalIssues.textContent = "-";
  els.reviewLevel.textContent = "-";
  els.reviewStatus.textContent = "空闲";
  els.reviewLintStatus.textContent = "-";
  els.reviewProfilingStatus.textContent = "-";
  els.reviewLintElapsedDetail.textContent = "-";
  els.reviewProfilingElapsedDetail.textContent = "-";
  els.reviewSummaryPath.textContent = "-";
  els.reviewReportPath.textContent = "-";
  els.reviewLogPath.textContent = "-";
  els.reviewLintSummaryPath.textContent = "-";
  els.reviewRiskSummaryPath.textContent = "-";
  els.reviewGoldText.textContent = "-";
  els.reviewReportLocationStatus.textContent = "-";
  els.reviewRows.innerHTML = "";
  resetReviewFilters();
  updateReviewFilterCount(0, 0);
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

function renderRiskSummary(summary) {
  if (!summary) return;
  lastRiskSummary = summary;
  els.riskElapsed.textContent = `耗时 ${fmt(summary.elapsed_seconds)}s`;
  els.riskCount.textContent = fmt(summary.risk_count);
  els.riskLevel.textContent = riskLabel(summary.risk_level);
  els.riskStatus.textContent = "完成";
  els.riskSummaryPath.textContent = summary.artifacts?.risk_summary_json || "-";
  els.riskReportPath.textContent = summary.artifacts?.risk_report_md || "-";
  els.riskLogPath.textContent = summary.artifacts?.risk_log || "-";
  const gold = summary.gold_compare || {};
  els.riskGoldState.textContent = gold.available ? "已对比" : "已跳过";
  els.riskGoldText.textContent = gold.message_zh || "-";
  if (gold.available) {
    const categories = (gold.gold_categories || []).join(", ") || "-";
    const confirmed = (gold.confirmed_risk_rules || []).join(", ") || "-";
    els.riskGoldText.textContent = `${gold.message_zh || "已执行 gold 对比。"} gold 类别：${categories}；命中规则：${confirmed}`;
  }
  populateRiskRuleFilter(summary.risks || []);
  renderRiskRows();
}

function resetRiskFilters() {
  els.riskRuleFilter.innerHTML = '<option value="">全部规则</option>';
  els.riskSeverityFilter.value = "";
}

function populateRiskRuleFilter(risks) {
  const previous = els.riskRuleFilter.value;
  const rules = [...new Set((risks || []).map((item) => item.rule).filter(Boolean))].sort();
  els.riskRuleFilter.innerHTML = '<option value="">全部规则</option>';
  rules.forEach((rule) => {
    const option = document.createElement("option");
    option.value = rule;
    option.textContent = rule;
    els.riskRuleFilter.appendChild(option);
  });
  if (rules.includes(previous)) {
    els.riskRuleFilter.value = previous;
  }
}

function filteredRisks() {
  const risks = Array.isArray(lastRiskSummary?.risks) ? lastRiskSummary.risks : [];
  const rule = els.riskRuleFilter.value;
  const severity = els.riskSeverityFilter.value;
  return risks.filter((item) => {
    if (rule && item.rule !== rule) return false;
    if (severity && item.severity !== severity) return false;
    return true;
  });
}

function updateRiskFilterCount(visible, total) {
  els.riskFilteredCount.textContent = `当前显示 ${visible} / ${total} 条风险`;
}

function renderRiskRows() {
  const allRisks = Array.isArray(lastRiskSummary?.risks) ? lastRiskSummary.risks : [];
  const rows = filteredRisks();
  els.riskRows.innerHTML = "";
  rows.slice(0, 160).forEach((item) => {
    const tr = document.createElement("tr");
    const evidence = JSON.stringify(item.evidence || {});
    [item.rule, item.severity, item.file, item.line, item.confidence, item.message_zh, item.suggestion_zh, evidence].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = fmt(value);
      tr.appendChild(td);
    });
    els.riskRows.appendChild(tr);
  });
  updateRiskFilterCount(rows.length, allRisks.length);
}

function renderReviewSummary(summary) {
  if (!summary) return;
  lastReviewSummary = summary;
  els.reviewElapsed.textContent = `耗时 ${fmt(summary.elapsed_seconds)}s`;
  els.reviewLintIssues.textContent = fmt(summary.lint_issue_count);
  els.reviewRiskCount.textContent = fmt(summary.risk_count);
  els.reviewTotalIssues.textContent = fmt(summary.total_issue_count);
  els.reviewLevel.textContent = riskLabel(summary.risk_level);
  els.reviewStatus.textContent = runStatusLabel(summary.status);
  const lintFlow = summary.subflows?.lint || {};
  const profilingFlow = summary.subflows?.profiling || {};
  els.reviewLintStatus.textContent = subflowStatusLabel(lintFlow.status);
  els.reviewProfilingStatus.textContent = subflowStatusLabel(profilingFlow.status);
  els.reviewLintElapsedDetail.textContent = `${fmt(lintFlow.elapsed_seconds)}s / ${fmt(lintFlow.issue_count)} 条`;
  els.reviewProfilingElapsedDetail.textContent = `${fmt(profilingFlow.elapsed_seconds)}s / ${fmt(profilingFlow.issue_count)} 条`;
  els.reviewSummaryPath.textContent = summary.artifacts?.review_summary_json || "-";
  els.reviewReportPath.textContent = summary.artifacts?.review_report_md || "-";
  els.reviewLogPath.textContent = summary.artifacts?.review_log || "-";
  els.reviewLintSummaryPath.textContent = summary.artifacts?.lint_summary_json || "-";
  els.reviewRiskSummaryPath.textContent = summary.artifacts?.risk_summary_json || "-";
  const gold = summary.gold_compare || {};
  if (gold.available) {
    const categories = (gold.gold_categories || []).join(", ") || "-";
    const confirmed = (gold.confirmed_risk_rules || []).join(", ") || "-";
    els.reviewGoldText.textContent = `${gold.message_zh || "已执行 gold 对比。"} gold 类别：${categories}；命中规则：${confirmed}`;
  } else {
    els.reviewGoldText.textContent = gold.message_zh || "未配置 OpenSTA/backend gold 报告，已跳过对比。";
  }
  const location = summary.report_location_status || {};
  els.reviewReportLocationStatus.textContent = location.message_zh || "-";
  if (els.backendLocationStatus && location.message_zh) {
    els.backendLocationStatus.textContent = location.message_zh;
  }
  populateReviewRuleFilter(summary.items || []);
  populateReviewCategoryFilter(summary.items || []);
  populateReviewFileFilter(summary.items || []);
  renderReviewRows();
}

function resetReviewFilters() {
  els.reviewSourceFilter.value = "";
  els.reviewPriorityFilter.value = "";
  els.reviewRuleFilter.innerHTML = '<option value="">全部规则</option>';
  els.reviewCategoryFilter.innerHTML = '<option value="">全部类别</option>';
  els.reviewFileFilter.innerHTML = '<option value="">全部文件</option>';
  els.reviewSeverityFilter.value = "";
}

function populateReviewRuleFilter(items) {
  const previous = els.reviewRuleFilter.value;
  const rules = [...new Set((items || []).map((item) => item.rule).filter(Boolean))].sort();
  els.reviewRuleFilter.innerHTML = '<option value="">全部规则</option>';
  rules.forEach((rule) => {
    const option = document.createElement("option");
    option.value = rule;
    option.textContent = rule;
    els.reviewRuleFilter.appendChild(option);
  });
  if (rules.includes(previous)) {
    els.reviewRuleFilter.value = previous;
  }
}

function populateReviewCategoryFilter(items) {
  populateSelect(els.reviewCategoryFilter, "全部类别", items.map((item) => item.category));
}

function populateReviewFileFilter(items) {
  populateSelect(els.reviewFileFilter, "全部文件", items.map((item) => item.file));
}

function filteredReviewItems() {
  const items = Array.isArray(lastReviewSummary?.items) ? lastReviewSummary.items : [];
  const source = els.reviewSourceFilter.value;
  const priority = els.reviewPriorityFilter.value;
  const rule = els.reviewRuleFilter.value;
  const category = els.reviewCategoryFilter.value;
  const file = els.reviewFileFilter.value;
  const severity = els.reviewSeverityFilter.value;
  return items.filter((item) => {
    if (source && item.source !== source) return false;
    if (priority && item.priority !== priority) return false;
    if (rule && item.rule !== rule) return false;
    if (category && item.category !== category) return false;
    if (file && item.file !== file) return false;
    if (severity && item.severity !== severity) return false;
    return true;
  });
}

function updateReviewFilterCount(visible, total) {
  els.reviewFilteredCount.textContent = `当前显示 ${visible} / ${total} 条`;
}

function renderReviewRows() {
  const allItems = Array.isArray(lastReviewSummary?.items) ? lastReviewSummary.items : [];
  const rows = filteredReviewItems();
  els.reviewRows.innerHTML = "";
  rows.slice(0, 200).forEach((item) => {
    const tr = document.createElement("tr");
    const evidence = JSON.stringify(item.evidence || {});
    [
      item.source,
      item.priority,
      item.case_id,
      item.rule,
      item.category,
      item.severity,
      item.file,
      item.line,
      item.confidence,
      item.message_zh,
      item.suggestion_zh,
      evidence,
      `${item.correlation_id || "-"} (${item.overlap_count || 1})`,
    ].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = fmt(value);
      tr.appendChild(td);
    });
    els.reviewRows.appendChild(tr);
  });
  updateReviewFilterCount(rows.length, allItems.length);
}

function runStatusLabel(status) {
  if (status === "success") return "完成";
  if (status === "partial_success") return "部分完成";
  if (status === "failure") return "失败";
  return fmt(status);
}

function subflowStatusLabel(status) {
  if (status === "success") return "成功";
  if (status === "failure") return "失败";
  return fmt(status);
}

function populateSelect(select, placeholder, values) {
  const previous = select.value;
  const unique = [...new Set((values || []).filter(Boolean))].sort();
  select.innerHTML = `<option value="">${placeholder}</option>`;
  unique.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  if (unique.includes(previous)) {
    select.value = previous;
  }
}

function populateCoverageCategoryFilter(cases) {
  populateSelect(els.coverageCategoryFilter, "全部类别", cases.map((item) => item.category));
}

function renderCoverageSummary() {
  const summary = coverageSummary || {};
  const p0 = summary.priorities?.P0 || {};
  const p1 = summary.priorities?.P1 || {};
  const owners = summary.owner_counts || {};
  els.coverageTotal.textContent = fmt(summary.total);
  els.coverageP0.textContent = `${fmt(p0.covered)} / ${fmt(p0.total)} (${fmt(p0.coverage_percent)}%)`;
  els.coverageP1.textContent = `${fmt(p1.covered)} / ${fmt(p1.total)} (${fmt(p1.coverage_percent)}%)`;
  els.coverageLintOwner.textContent = fmt(owners.lint);
  els.coverageProfilingOwner.textContent = fmt(owners.profiling);
  els.coverageBothOwner.textContent = fmt(owners.both);
  els.coverageP0Detail.textContent = coverageDetail(p0);
  els.coverageP1Detail.textContent = coverageDetail(p1);
}

function coverageDetail(item) {
  return `总数 ${fmt(item.total)}；已覆盖 ${fmt(item.covered)}；部分覆盖 ${fmt(item.partially_supported)}；未覆盖 ${fmt(item.not_covered)}；明确 unsupported ${fmt(item.unsupported_diagnostic)}；按边界不支持 ${fmt(item.unsupported_by_design)}`;
}

function filteredCoverageCases() {
  const priority = els.coveragePriorityFilter.value;
  const owner = els.coverageOwnerFilter.value;
  const category = els.coverageCategoryFilter.value;
  const status = els.coverageStatusFilter.value;
  return coverageCases.filter((item) => {
    if (priority && item.priority !== priority) return false;
    if (owner && item.owner !== owner) return false;
    if (category && item.category !== category) return false;
    if (status && item.support_status !== status) return false;
    return true;
  });
}

function renderCoverageRows() {
  const rows = filteredCoverageCases();
  els.coverageRows.innerHTML = "";
  rows.forEach((item) => {
    const tr = document.createElement("tr");
    const rules = (item.rule_ids || []).join(", ") || "-";
    const testPaths = (item.test_paths || []).join(", ") || "-";
    const latestEvidence = item.latest_verification_evidence?.path || "-";
    const golden = item.golden_reference
      ? `${item.golden_reference.status || "-"} / ${item.golden_reference.tool || "-"}`
      : "-";
    const note = item.unsupported_reason_zh || item.support_note_zh || "-";
    [
      item.priority,
      item.case_id,
      item.name_zh,
      item.category,
      item.owner,
      item.support_status,
      item.test_status,
      rules,
      testPaths,
      latestEvidence,
      golden,
      note,
      item.next_improvement_zh,
    ].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = fmt(value);
      tr.appendChild(td);
    });
    els.coverageRows.appendChild(tr);
  });
  els.coverageFilteredCount.textContent = `当前显示 ${rows.length} / ${coverageCases.length} 个 Case`;
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

async function startRiskRun() {
  if (riskEventSource) {
    riskEventSource.close();
    riskEventSource = null;
  }
  const payload = collectRiskPayload();
  const errors = validateRiskPayload(payload);
  if (errors.length) {
    els.riskMessage.className = "message error";
    els.riskMessage.textContent = errors.join(" ");
    return;
  }
  els.riskLog.textContent = "";
  resetRiskResult();
  els.riskStatus.textContent = "运行中";
  els.riskMessage.className = "message";
  els.riskMessage.textContent = "";
  els.riskRunBtn.disabled = true;
  try {
    const response = await fetch("/api/risk_run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "启动 RTL 时序风险分析失败");
    }
    connectRiskEvents(data.job_id);
  } catch (err) {
    els.riskMessage.className = "message error";
    els.riskMessage.textContent = `启动 RTL 时序风险分析失败：${err.message}`;
    els.riskStatus.textContent = "失败";
    els.riskRunBtn.disabled = false;
  }
}

function connectRiskEvents(jobId) {
  riskEventSource = new EventSource(`/api/risk_events?id=${encodeURIComponent(jobId)}`);

  riskEventSource.addEventListener("status", (event) => {
    const data = JSON.parse(event.data);
    els.riskLog.textContent += `[sta-lite risk] ${data.message || data.status}\n`;
    els.riskLog.scrollTop = els.riskLog.scrollHeight;
  });

  riskEventSource.addEventListener("log", (event) => {
    const data = JSON.parse(event.data);
    els.riskLog.textContent += `${data.line}\n`;
    els.riskLog.scrollTop = els.riskLog.scrollHeight;
    if (data.elapsed_seconds !== undefined) {
      els.riskElapsed.textContent = `耗时 ${fmt(data.elapsed_seconds)}s`;
    }
  });

  riskEventSource.addEventListener("elapsed", (event) => {
    const data = JSON.parse(event.data);
    els.riskElapsed.textContent = `耗时 ${fmt(data.elapsed_seconds || 0)}s`;
  });

  riskEventSource.addEventListener("summary", (event) => {
    const data = JSON.parse(event.data);
    renderRiskSummary(data.summary);
    els.riskMessage.className = data.summary.risk_level === "HIGH" ? "message error" : "message ok";
    els.riskMessage.textContent = "RTL 时序风险分析完成，risk_summary.json 和 risk_report.md 已保存。";
    els.riskRunBtn.disabled = false;
    riskEventSource.close();
  });

  riskEventSource.addEventListener("error", (event) => {
    if (event.data) {
      const data = JSON.parse(event.data);
      if (data.summary) renderRiskSummary(data.summary);
      els.riskMessage.textContent = data.message || "RTL 时序风险分析失败。";
    } else {
      els.riskMessage.textContent = "Risk 日志连接中断。";
    }
    els.riskMessage.className = "message error";
    els.riskStatus.textContent = "失败";
    els.riskRunBtn.disabled = false;
    riskEventSource.close();
  });
}

async function startReviewRun() {
  if (reviewEventSource) {
    reviewEventSource.close();
    reviewEventSource = null;
  }
  const payload = collectReviewPayload();
  const errors = validateReviewPayload(payload);
  if (errors.length) {
    els.reviewMessage.className = "message error";
    els.reviewMessage.textContent = errors.join(" ");
    return;
  }
  els.reviewLog.textContent = "";
  resetReviewResult();
  els.reviewStatus.textContent = "运行中";
  els.reviewMessage.className = "message";
  els.reviewMessage.textContent = "";
  els.reviewRunBtn.disabled = true;
  try {
    const response = await fetch("/api/review_run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "启动 RTL Review 失败");
    }
    connectReviewEvents(data.job_id);
  } catch (err) {
    els.reviewMessage.className = "message error";
    els.reviewMessage.textContent = `启动 RTL Review 失败：${err.message}`;
    els.reviewStatus.textContent = "失败";
    els.reviewRunBtn.disabled = false;
  }
}

function connectReviewEvents(jobId) {
  reviewEventSource = new EventSource(`/api/review_events?id=${encodeURIComponent(jobId)}`);

  reviewEventSource.addEventListener("status", (event) => {
    const data = JSON.parse(event.data);
    els.reviewLog.textContent += `[sta-lite review] ${data.message || data.status}\n`;
    els.reviewLog.scrollTop = els.reviewLog.scrollHeight;
  });

  reviewEventSource.addEventListener("log", (event) => {
    const data = JSON.parse(event.data);
    els.reviewLog.textContent += `${data.line}\n`;
    els.reviewLog.scrollTop = els.reviewLog.scrollHeight;
    if (data.elapsed_seconds !== undefined) {
      els.reviewElapsed.textContent = `耗时 ${fmt(data.elapsed_seconds)}s`;
    }
  });

  reviewEventSource.addEventListener("elapsed", (event) => {
    const data = JSON.parse(event.data);
    els.reviewElapsed.textContent = `耗时 ${fmt(data.elapsed_seconds || 0)}s`;
  });

  reviewEventSource.addEventListener("summary", (event) => {
    const data = JSON.parse(event.data);
    renderReviewSummary(data.summary);
    if (data.summary.status === "partial_success") {
      els.reviewMessage.className = "message error";
      els.reviewMessage.textContent = "RTL Review 部分完成：一个子流程失败，另一个子流程的结果和报告已保留。";
    } else if (data.summary.status === "failure") {
      els.reviewMessage.className = "message error";
      els.reviewMessage.textContent = "RTL Review 两个子流程均失败，请查看中文错误和 review.log。";
    } else {
      els.reviewMessage.className = data.summary.risk_level === "HIGH" ? "message error" : "message ok";
      els.reviewMessage.textContent = "RTL Review 完成，review_summary.json 和 review_report.md 已保存。";
    }
    els.reviewRunBtn.disabled = false;
    reviewEventSource.close();
  });

  reviewEventSource.addEventListener("error", (event) => {
    if (event.data) {
      const data = JSON.parse(event.data);
      if (data.summary) renderReviewSummary(data.summary);
      els.reviewMessage.textContent = data.message || "RTL Review 失败。";
    } else {
      els.reviewMessage.textContent = "RTL Review 日志连接中断。";
    }
    els.reviewMessage.className = "message error";
    els.reviewStatus.textContent = "失败";
    els.reviewRunBtn.disabled = false;
    reviewEventSource.close();
  });
}

function clearRiskPanel() {
  if (riskEventSource) {
    riskEventSource.close();
    riskEventSource = null;
  }
  els.riskLog.textContent = "";
  resetRiskResult();
  els.riskMessage.className = "message";
  els.riskMessage.textContent = "";
}

function clearReviewPanel() {
  if (reviewEventSource) {
    reviewEventSource.close();
    reviewEventSource = null;
  }
  els.reviewLog.textContent = "";
  resetReviewResult();
  els.reviewMessage.className = "message";
  els.reviewMessage.textContent = "";
}

async function copyRiskOutDir() {
  const text = els.riskOutDir.value.trim();
  if (!text) {
    els.riskMessage.className = "message error";
    els.riskMessage.textContent = "Risk 输出目录为空，无法复制。";
    return;
  }
  try {
    if (!navigator.clipboard?.writeText) {
      throw new Error("当前浏览器未开放剪贴板接口");
    }
    await navigator.clipboard.writeText(text);
    els.riskMessage.className = "message ok";
    els.riskMessage.textContent = "Risk 输出目录已复制。";
  } catch (err) {
    els.riskMessage.className = "message error";
    els.riskMessage.textContent = "浏览器不允许直接复制，请手动选中输出目录复制。";
  }
}

async function copyReviewOutDir() {
  const text = els.reviewOutDir.value.trim();
  if (!text) {
    els.reviewMessage.className = "message error";
    els.reviewMessage.textContent = "RTL Review 输出目录为空，无法复制。";
    return;
  }
  try {
    if (!navigator.clipboard?.writeText) {
      throw new Error("当前浏览器未开放剪贴板接口");
    }
    await navigator.clipboard.writeText(text);
    els.reviewMessage.className = "message ok";
    els.reviewMessage.textContent = "RTL Review 输出目录已复制。";
  } catch (err) {
    els.reviewMessage.className = "message error";
    els.reviewMessage.textContent = "浏览器不允许直接复制，请手动选中输出目录复制。";
  }
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
els.navReview.addEventListener("click", () => switchPage("review"));
els.navLint.addEventListener("click", () => switchPage("lint"));
els.navProfiling.addEventListener("click", () => switchPage("profiling"));
els.navBackend.addEventListener("click", () => {
  switchPage("backend");
  loadBackendStatus();
});
els.navCoverage.addEventListener("click", () => switchPage("coverage"));
els.lintRunBtn.addEventListener("click", startLintRun);
els.riskRunBtn.addEventListener("click", startRiskRun);
els.reviewRunBtn.addEventListener("click", startReviewRun);
els.reviewClearBtn.addEventListener("click", clearReviewPanel);
els.reviewCopyOutDir.addEventListener("click", copyReviewOutDir);
els.reviewLoadCase.addEventListener("click", loadSelectedReviewCase);
els.reviewSourceFilter.addEventListener("change", renderReviewRows);
els.reviewPriorityFilter.addEventListener("change", renderReviewRows);
els.reviewRuleFilter.addEventListener("change", renderReviewRows);
els.reviewCategoryFilter.addEventListener("change", renderReviewRows);
els.reviewFileFilter.addEventListener("change", renderReviewRows);
els.reviewSeverityFilter.addEventListener("change", renderReviewRows);
els.coverageRefreshBtn.addEventListener("click", loadReviewCoverage);
els.coveragePriorityFilter.addEventListener("change", renderCoverageRows);
els.coverageOwnerFilter.addEventListener("change", renderCoverageRows);
els.coverageCategoryFilter.addEventListener("change", renderCoverageRows);
els.coverageStatusFilter.addEventListener("change", renderCoverageRows);
els.riskClearBtn.addEventListener("click", clearRiskPanel);
els.riskCopyOutDir.addEventListener("click", copyRiskOutDir);
els.riskLoadCase.addEventListener("click", loadSelectedRiskCase);
els.riskRuleFilter.addEventListener("change", renderRiskRows);
els.riskSeverityFilter.addEventListener("change", renderRiskRows);
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

els.fillRiskLongComb.addEventListener("click", () => {
  els.riskRtl.value = "risk_profile/cases/long_comb_path/long_comb_path.v";
  els.riskTop.value = "top";
  els.riskInclude.value = "";
  els.riskDefines.value = "";
  els.riskSdc.value = "";
  els.riskGoldDir.value = "risk_profile/gold/opensta";
  els.riskOutDir.value = "runs/gui_risk_long_comb";
  const longComb = riskCases.find((item) => item.category === "long_comb_path");
  if (longComb) {
    els.riskCaseSelect.value = longComb.id;
  }
});

els.fillReviewLongComb.addEventListener("click", () => {
  els.reviewRtl.value = "risk_profile/cases/long_comb_path/long_comb_path.v";
  els.reviewTop.value = "top";
  els.reviewInclude.value = "";
  els.reviewDefines.value = "";
  els.reviewSdc.value = "";
  els.reviewRules.value = "";
  els.reviewGoldDir.value = "";
  els.reviewOutDir.value = "runs/gui_review_long_comb";
  const longComb = riskCases.find((item) => item.category === "long_comb_path");
  if (longComb) {
    els.reviewCaseSelect.value = longComb.id;
  }
});

[els.top, els.rtl, els.liberty, els.clock, els.period, els.sdc, els.outDir, els.yosysBin, els.staBin].forEach((input) => {
  input.addEventListener("input", updateCliCommand);
  input.addEventListener("change", updateCliCommand);
});

updateCliCommand();
switchPage("review");
loadRiskCases();
loadReviewCoverage();
loadBackendStatus();
updateRiskFilterCount(0, 0);
updateReviewFilterCount(0, 0);
