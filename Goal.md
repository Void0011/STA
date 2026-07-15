# Project Goal

## Vision

Build STA-lite as an RTL-stage backend-risk warning and report-location assistant.

The current product direction is not to replace PrimeTime, Tempus, Vivado Timing Analyzer, OpenSTA signoff-style flows, or any other signoff-grade STA product. STA-lite should help RTL/FPGA/IC developers discover backend-related risks earlier, understand backend violations faster, and reduce repeated synthesis/place-route/debug cycles.

For the current version, STA-lite should be understood as:

```text
RTL source review
  -> lint and structural risk detection
  -> early backend-risk prediction
  -> optional local backend reference analysis
  -> report-to-RTL location assistance
```

It should not be described as a real physical timing model or a signoff STA engine.

## Business Logic

The GUI should provide five pages. These pages expose three analysis capabilities without duplicating their underlying engines:

```text
RTL Review = RTL Lint + RTL Timing Risk Profiling
Backend Analysis = Yosys/OpenSTA reference flow
Case Coverage = P0/P1 coverage visibility
```

### 1. RTL Review

`RTL Review` is the primary unified RTL audit page. It should execute both standalone internal capabilities against the same selected RTL project:

```text
Verilog/SystemVerilog RTL
  -> RTL Lint
  -> RTL Timing Risk Profiling
  -> merged and classified result
  -> GUI summary/detail display
```

P0 and P1 cases may belong to the lint capability, the timing-risk profiling capability, or both. `RTL Review` must aggregate their results without maintaining a separate rule implementation.

The page should show:

- combined execution status and elapsed time
- separate lint and profiling progress/status
- total lint issue count and timing-risk count
- merged result table with source capability, P0/P1 priority, severity, file, line, confidence, evidence, and Chinese suggestion
- filters for lint/risk, P0/P1, severity, category, and support state where practical
- generated report locations

### 2. RTL Lint

`RTL Lint` is the standalone detailed page for syntax, grammar, semantic-style, synthesizability, connectivity, width, driver, and related lint cases.

It should preserve the released lint_v0 behavior and expose detailed lint-specific inputs, logs, diagnostics, and reports. Cases assigned to RTL Lint remain visible in `RTL Review` through shared workflow results.

### 3. RTL Timing Risk Profiling

`RTL Timing Risk Profiling` is the standalone detailed page for source-level structural risks that may correlate with synthesis, place-route, or backend timing problems.

It should cover cases such as long combinational chains, large mux/priority structures, high fanout, gated/derived clocks, reset-release risks, simple CDC risks, and missing pipeline hints. Cases assigned to Profiling remain visible in `RTL Review` through shared workflow results.

This capability must not require synthesis or STA tools at runtime. OpenSTA/backend reports may be optional gold data for correlation.

### 4. Yosys/OpenSTA Backend Analysis

This GUI is responsible for local Yosys/OpenSTA analysis. It may use local backend tools and should preserve or optimize the existing GUI behavior:

```text
Verilog/SystemVerilog RTL
  -> Yosys synthesis
  -> OpenSTA timing report
  -> parsed result
  -> GUI display
```

This GUI should make the backend reference flow observable:

- show live compile/synthesis/STA logs
- show elapsed time during analysis
- show final WNS/TNS/risk summary
- show timing violations in a dedicated area or window
- show backend report parsing results
- support timing-path/report items that can later be mapped back to RTL source context

This workflow is allowed to depend on local Yosys, OpenSTA, Liberty, and valid SDC input. Missing backend tools should be reported clearly in Chinese.

### 5. Case Coverage

`Case Coverage` is a read-only project-status page for P0/P1 risk-case coverage.

It should display:

- total P0/P1 case counts and covered counts
- coverage percentage by priority and source capability
- each case ID, name, category, owner (`lint`, `profiling`, or `both`), support status, test status, and evidence
- status values such as `supported`, `partially_supported`, `unsupported_diagnostic`, `unsupported_by_design`, and `not_covered`
- links or paths to focused test cases, rule IDs, and latest verification results where available
- filters for P0/P1, lint/profiling, category, and support status

Coverage data should come from a shared case registry, metadata, or generated coverage matrix. It should not be duplicated as hard-coded GUI-only text.

The current long-term coverage goal is to maintain every P0/P1 case at `supported` for its documented RTL-only scope. A case may remain `partially_supported` only when a tested, useful common subset exists and the exact limitation, evidence, and next improvement are visible in Chinese.

## Standalone Product Principle

STA-lite's core product must be independently runnable. RTL Review, RTL Lint, RTL Timing Risk Profiling, Case Coverage, and their CLI flows must use STA-lite-owned parser/AST/rule infrastructure and must work without Yosys, OpenSTA, Verilator, iverilog, Surelog, sv-tests, or other external EDA software.

External tools may remain optional development-time golden/reference tools or explicitly configured Backend Analysis adapters. Their absence must not change production P0/P1 results, prevent core GUI startup, or block normal user workflows.

### Stable Distribution Principle

The standalone core should be distributed as an install-and-run application for Windows 10, Windows 11, and Ubuntu 20.04 or newer. Windows is the first-priority release platform.

Binary packages must bundle the Python runtime and all STA-lite-owned RTL Review resources. They must not bundle Yosys, OpenSTA, locally unpacked EDA tools, or third-party Liberty data. The optional Backend Analysis page may discover separately installed tools, while RTL Review, Lint, Profiling, and Case Coverage remain immediately usable after installation.

Windows builds must be produced on Windows rather than cross-compiled from Linux. Ubuntu builds should use Ubuntu 20.04 as the oldest glibc baseline. Stable tags must be backed by reproducible CI, frozen-application smoke tests, SHA-256 checksums, release notes, and clearly documented compatibility evidence.

### Shared Backend Report Reverse Location Utility

At the backend synthesis/place-route/STA stage, the tool should parse reports and help locate violations back to RTL source context.

The long-term goal is:

```text
backend violation report -> netlist path -> module/register/signal mapping -> RTL file/location -> reviewable optimization suggestion
```

For the current version, reliable report-to-RTL location assistance is a required product direction. It is not expected to prove physical timing correctness, but it should make backend report debugging easier.

The practical first step should:

- parse Yosys/OpenSTA logs and reports
- extract startpoint, endpoint, slack, path group, and warnings
- preserve enough names and files to support RTL backtracking
- build RTL source indexes for modules, instances, signals, always blocks, and assignments
- map backend report tokens to likely RTL file/line candidates with confidence and evidence

## Risk Case Roadmap

The current version should treat P0 and P1 RTL risk cases as the main feature roadmap.

P0 cases have priority over P1. When a P0 case is `partially_supported`, the next implementation pass should either:

- expand the relevant RTL Lint or RTL Timing Risk Profiling rule until the case becomes `supported`, with focused tests and golden/reference comparison where practical
- or mark the case `unsupported_by_design` / `unsupported_diagnostic` with a Chinese reason and next possible direction

### P0 Risk Cases

P0 cases are the immediate implementation target across RTL Lint and RTL Timing Risk Profiling. `RTL Review` aggregates both sets:

- syntax lint and basic grammar errors
- synthesizability risks such as delay statements, simulation-only constructs, and unsupported frontend constructs
- bit-width mismatch, truncation, and suspicious implicit extension
- latch inference from incomplete combinational assignments
- combinational loop risk
- multiple drivers
- undriven and unused signals
- long combinational logic chain
- large fanout control/reset/enable signals
- asynchronous reset release without clear synchronization
- simple cross-clock-domain signal transfer risk
- gated clock and derived clock created by RTL logic
- incomplete or suspicious `case` / `if` structures
- simple FSM robustness risks
- blocking/nonblocking assignment misuse
- large mux or long priority chain
- arithmetic chain risks such as wide add/compare/multiply paths without pipeline hints

### P1 Risk Cases

P1 cases are the next current-version roadmap across RTL Lint and RTL Timing Risk Profiling. `RTL Review` aggregates implemented P1 checks:

- RAM inference risk
- DSP inference risk
- missing pipeline around wide arithmetic, compare trees, or mux trees
- excessive reset usage on datapath registers
- high-fanout clock-enable usage
- X-propagation and `casez` / `casex` risk
- signed/unsigned mixed-expression risk
- complex `generate` / parameter elaboration risk
- invalid or suspicious parameter-derived widths
- module instance and port-connection risk
- multi-clock always blocks
- asynchronous data/control path risk beyond reset

## System Positioning

This tool is an early-risk and debug-assistance platform, not a golden timing signoff tool.

It should prioritize:

- reproducibility
- clear GUI visibility
- Chinese engineering diagnostics
- report parsing and structured summaries
- clean integration boundaries
- future extensibility toward RTL source mapping
- five clear GUI pages backed by reusable analysis workflows
- visible P0/P1 coverage status without overstating support

It should not prioritize in the first version:

- real FPGA physical interconnect delay modeling
- placement/routing estimation
- ML timing prediction
- advanced MCMM or signoff variation models
- full PrimeTime command compatibility
