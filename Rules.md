# Technical Rules

## Codex Execution Rules

- Before making changes, read `AGENTS.md`, `Goal.md`, `Task.md`, `Rules.md`, and existing source/tests/examples.
- Ask fewer questions. Inspect the repository, infer the current state, and implement directly unless progress would be unsafe or impossible.
- All user-facing progress logs, error messages, README/report text, verification summaries, and final summaries must be in Simplified Chinese.
- Keep final summaries concise and include: changed files, executed commands, verification results, remaining gaps, and next suggested step.
- Prefer completing implementation plus verification in one pass instead of only proposing a plan.
- If verification is blocked by missing local tools, GUI display, or environment variables, explain the blocker in Chinese and leave the code ready for the expected environment.
- When a task asks for GitHub submission, perform implementation, verification, `.gitignore` cleanup, commit, and push if the remote/authentication are available.
- When a task requires open-source golden/reference tools, search current official sources or package repositories, install only what is needed, record versions and commands, and keep user-facing logs in Chinese.

## Tech Stack

- Prefer Python for the MVP.
- Use standard-library Python where practical.
- Use `tkinter` for GUI work unless the repository already has PySide/PyQt or a clear C++ GUI convention.
- Do not download dependencies unless strictly required.

## Project Structure

If no stronger existing convention exists, use:

```text
sta_lite/
  lint/          # internal preprocessor, lexer, parser, lint rules
  risk/          # RTL timing-risk profiling rules and workflows
  core/          # reusable workflows and run models
  parsers/       # report/log parsers for later STA/backend reports
  mapping/       # RTL source indexes and backend report-to-RTL location helpers
  models/        # diagnostics and shared data models
  gui/           # GUI windows, widgets, controllers
  utils/         # shared helpers
lint/
  README.md
  verilog_error_example/
  verilog_warning_example/
  system_verilog_error_examplr/
  system_verilog_warning_example/
examples/        # normal positive examples and demos
risk_profile/    # RTL timing-risk corpus, docs, optional gold reports
tests/           # regression tests
reports/         # generated outputs, gitignored when practical
README.md
```

Do not put all logic into a single GUI file or a single linter file. GUI code should call reusable core/lint services.

## Current Product Boundary

- STA-lite current version is not a signoff STA product.
- The current product target is RTL-stage backend-risk warning plus backend report-location assistance.
- Keep five GUI pages clearly separated:
  - `RTL Review`: combined execution and aggregation of RTL Lint plus RTL Timing Risk Profiling.
  - `RTL Lint`: standalone lint execution and detailed diagnostics.
  - `RTL Timing Risk Profiling`: standalone structural/timing-risk execution and detailed diagnostics.
  - `Yosys/OpenSTA Backend Analysis`: local backend reference analysis.
  - `Case Coverage`: read-only P0/P1 coverage status.
- Do not make Yosys/OpenSTA/OpenROAD/Vivado/Quartus mandatory for RTL Review.
- Backend reports and OpenSTA results may be optional gold/reference data for correlation, but not the production engine for RTL Review.
- User-facing UI labels and documents must avoid implying that RTL risk findings are signoff timing results.
- `RTL Review` must reuse and aggregate the standalone Lint and Profiling workflows; it must not own a third copy of their rules.
- Optional golden/reference tools such as iverilog, Verilator, Yosys, Surelog/UHDM, or sv-tests must stay development/test dependencies and must not become mandatory production runtime dependencies.

## Lint Strategy

- The production lint capability should be implemented inside STA-lite.
- Verilog support should be improved toward near IEEE 1364 practical compliance.
- SystemVerilog syntax-check support should be added incrementally and kept separate from Verilog corpus data.
- `iverilog` may be used as a development-time golden reference for Verilog tests and regression only.
- Do not use `iverilog` as the production lint engine.
- Do not assume `iverilog` is a complete SystemVerilog golden.
- Do not run `vvp` for lint regression. `vvp` is the Icarus Verilog simulation runtime for executing compiled simulation output; lint regression should stop at compile/golden diagnostics and must not execute simulation.
- Preserve the current zero-miss lint baseline as a regression invariant when expanding corpus coverage.
- New lint coverage should prefer minimal, focused examples with `case.json` metadata.
- Generated reports are verification artifacts and should not be committed unless explicitly requested.

## RTL Timing Risk Strategy

- The production RTL timing-risk feature must run directly on RTL and STA-lite's own parser/AST/rule infrastructure.
- Do not require Yosys, OpenSTA, OpenROAD, Vivado, Quartus, or commercial tools to run RTL risk profiling.
- OpenSTA/backend reports may be used only as optional offline gold/reference data.
- Risk diagnostics are early warnings, not signoff timing results.
- Risk rules should report confidence (`high`, `medium`, `low`) and evidence fields when practical.
- Keep risk cases small, focused, and documented under `risk_profile/cases/`.
- GUI integrations must call the reusable risk workflow instead of duplicating risk rules in GUI code.

## RTL Risk Case Priorities

P0 cases are the immediate implementation target for RTL Review:

- syntax lint and basic grammar errors
- synthesizability risks such as delay statements, simulation-only constructs, and unsupported synthesis constructs
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

P1 cases are the next current-version roadmap after P0 is stable:

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

When a listed case is not implemented, document its coverage status explicitly. Do not silently present roadmap items as fully supported checks.

P0 support hardening priority:

- First discover every P0 case whose support status is `partially_supported`.
- Upgrade supportable P0 partial cases to `supported` by extending the owned lint/profiling rule, adding focused examples, and passing automated tests.
- If a P0 case cannot be supported within STA-lite's RTL-only scope, mark it explicitly as unsupported with a Chinese reason and next possible direction.
- Do not promote any case to `supported` unless there is executable verification evidence.

P1 coverage priority:

- Current target cases are `P1_EXCESSIVE_RESET`, `P1_XPROP_CASEX_CASEZ`, `P1_SIGNED_UNSIGNED`, and `P1_MULTI_CLOCK_ALWAYS`.
- Upgrade each target from `not_covered` to `supported` when the documented minimum scope, focused tests, and golden/reference or expected-metadata comparison pass.
- If only a reliable common subset is possible, use `partially_supported` and expose the exact limitation, evidence, and next improvement in Chinese.
- Do not use `unsupported_by_design` merely because an implementation is difficult; reserve it for checks that genuinely require data beyond the RTL-only product boundary.

## P0/P1 Long-Term Coverage Rules

- Maintain an evidence-backed status for every P0/P1 case; review stale `supported`, `partially_supported`, and `not_covered` entries rather than trusting old labels.
- The default target for every case is `supported` for a documented RTL-only minimum scope.
- A `supported` status requires internal STA-lite implementation, focused positive/negative tests, and golden/reference or justified expected-metadata comparison.
- A `partially_supported` status requires a useful implemented subset, executable tests, a Chinese limitation, evidence path, and next improvement. Do not use it as a placeholder with no working behavior.
- `not_covered` may remain only while active implementation work is in progress and must include a next action in Case Coverage.
- Coverage updates must be atomic: rule behavior, tests, corpus metadata, registry/matrix, CLI result, and GUI status are updated together.

## Standalone Product Runtime Rules

- Production P0/P1 lint and profiling results must be produced entirely by STA-lite-owned code.
- The normal core application must run with Yosys, OpenSTA, Verilator, iverilog, Surelog/UHDM, sv-tests, and other external EDA tools absent from the system.
- Production code for RTL Review, RTL Lint, RTL Timing Risk Profiling, Case Coverage, and core CLI flows must not invoke external-tool subprocesses or use external-tool output as primary diagnostics.
- Keep golden/reference adapters isolated in development/test modules or explicitly optional integrations.
- The presence or absence of optional golden tools must not change STA-lite production diagnostics for the same RTL input.
- The Backend Analysis page may use explicitly configured external tools, but it must show a Chinese unavailable state when they are missing and must never block core application startup or core RTL workflows.
- Document the supported standalone runtime/packaging path and verify it with external golden tools unavailable.

Every P0/P1 case must declare an owner:

- `lint`
- `profiling`
- `both`

Syntax, grammar, synthesizability, width, driver, declaration, connectivity, and assignment-style cases normally belong to lint. Combinational-depth, mux/priority, fanout, clock/reset structure, simple CDC, arithmetic-chain, and pipeline cases normally belong to profiling. Cross-cutting cases may use `both`, but duplicate diagnostics must be normalized or correlated.

## Released lint_v0 Protection Rules

- lint_v0 has already been released and must be treated as a stable baseline.
- Do not change lint_v0 parser/rule/diagnostic behavior while implementing unrelated features unless the task explicitly requests it.
- If shared code must change, run lint_v0 regression or smoke tests and report the result in Chinese.
- Final summaries for tasks touching GUI/risk code must state whether lint_v0 files or behavior were changed.

## Corpus Directory Rules

Use these canonical corpus roots:

```text
lint/verilog_error_example/
lint/verilog_warning_example/
lint/system_verilog_error_examplr/
lint/system_verilog_warning_example/
```

Rules:

- Error examples and warning examples must be separated.
- Verilog examples and SystemVerilog examples must be separated.
- Keep one small focused bug per example whenever practical.
- Each case should include metadata, preferably `case.json`.
- README files must be in Chinese.
- The directory `system_verilog_error_examplr` intentionally follows the user-specified spelling for this milestone.

## Iverilog Golden Rules

Use this command shape for Verilog golden checking:

```bash
iverilog -g2005 -Wall -tnull -s <top> <files>
```

Capture:

- command
- exit code
- stdout
- stderr
- elapsed time

Store normalized results under `reports/lint_diff/`.

Do not use this command as the production lint implementation.

## SystemVerilog Reference Rules

- STA-lite's own diagnostics are the required SystemVerilog product output.
- External SystemVerilog-capable tools may be supported as optional reference adapters only if already available.
- No external SystemVerilog reference tool may be mandatory.
- If no reference tool exists, compare STA-lite output against `case.json` metadata expectations.

## Standalone Lint Runtime Rules

- Unsupported constructs should produce clear diagnostics instead of crashes or silent acceptance.
- For unsupported Verilog constructs, use an `UNSUPPORTED_VERILOG`-style diagnostic.
- For unsupported SystemVerilog constructs, use an `UNSUPPORTED_SYSTEMVERILOG`-style diagnostic.
- Surface clear Chinese error messages for users.
- Preserve lint logs and structured outputs in the output directory.
- Keep internal diagnostics normalized so they can be compared against golden/reference/metadata results.

## GUI Runtime Rules

- Keep the GUI responsive while long-running work is active.
- Use a worker thread, subprocess streaming, or another non-blocking approach where needed.
- Stream user-visible logs into the GUI log panel.
- Show elapsed time for active runs.
- Show results and high-risk findings in a dedicated area.
- GUI pages should use existing CLI/core workflows where possible so CLI and GUI behavior stay consistent.
- The GUI must expose five clear pages: RTL Review, RTL Lint, RTL Timing Risk Profiling, Yosys/OpenSTA Backend Analysis, and Case Coverage.
- RTL Review must provide one action that executes both reusable lint and profiling workflows and aggregates their normalized results.
- RTL Lint and RTL Timing Risk Profiling must remain independently executable.
- Backend Reference Analysis may use Yosys/OpenSTA and should show backend logs, WNS/TNS, violations, and parsed report summaries.
- RTL Review must run lint/risk checks without backend tools and should show lint/risk counts, severity, file/line, confidence, evidence, and Chinese suggestions.
- Case Coverage must be read-only with respect to rule support state and must derive data from shared metadata, a case registry, or generated coverage reports.

## Combined RTL Review Rules

- `RTL Review = RTL Lint + RTL Timing Risk Profiling`.
- Use orchestration/adapters rather than duplicating engine logic.
- Preserve independent status, elapsed time, counts, logs, and failures for each sub-workflow.
- A failure in one sub-workflow must not discard valid results from the other.
- Combined diagnostics should include source capability and P0/P1 priority when known.
- Normalize or correlate duplicate findings without hiding relevant evidence.
- The result of a combined run should be equivalent to the union of standalone Lint and Profiling results for the same configuration.

## Case Coverage GUI Rules

- Coverage is based on implemented rules plus executable verification evidence, not documentation claims.
- Use these support statuses consistently: `supported`, `partially_supported`, `unsupported_diagnostic`, `unsupported_by_design`, `not_covered`.
- Track at least: priority, case ID, Chinese name, category, owner, status, test status, rule ID, test/metadata path, and next improvement.
- Show P0 and P1 totals, covered/partial/uncovered counts, and coverage percentages.
- Provide filters for priority, owner, category, and support status.
- Do not maintain an independent hard-coded case list in GUI code.
- Coverage totals displayed in the GUI must match the underlying registry or coverage matrix.
- A case may be marked `supported` only when implementation, tests, and golden/reference or expected-metadata comparison pass.
- A case should be marked `unsupported_by_design` when it requires data outside the current RTL-only scope, such as physical placement/routing, clock tree, RC, PVT, OCV/AOCV/POCV, MCMM, or signoff CDC/RDC analysis.
- A case should be marked `unsupported_diagnostic` when STA-lite detects the construct and emits a clear diagnostic but intentionally does not implement full semantic support.

## Golden Reference Tool Rules

- Golden/reference tools are used for development-time comparison only.
- Search current official project pages, release notes, package repositories, or trusted open-source documentation before choosing a new golden tool.
- Prefer tools that are reproducible locally on Ubuntu/WSL2 and can run from CLI without GUI interaction.
- Prefer OS package manager installation when adequate; otherwise follow the official project installation instructions.
- Record tool name, source URL, version, install command, and comparison command in Chinese documentation or generated verification output.
- Golden tests must skip gracefully when the optional tool is unavailable.
- Do not make optional golden tools mandatory for normal STA-lite runtime.
- Normalize both STA-lite and golden outputs before comparing diagnostics.
- Capture command, version, exit code, stdout, stderr, elapsed time, normalized findings, and pass/fail result.
- Do not run functional simulation for lint/risk golden comparison unless explicitly needed by the case.
- Golden/reference adapters must never be imported or executed by a normal production lint/risk path.
- Record a metadata fallback when no open-source golden can represent an RTL heuristic policy accurately.

Recommended golden/reference mapping:

- Use `iverilog -g2005 -Wall -tnull` for Verilog syntax and warning-like compile diagnostics.
- Use `Verilator --lint-only` for lint, width, latch, combinational-loop, multiple-driver, and synthesizability-style diagnostics when applicable.
- Use `Yosys` for synthesizability, latch inference, hierarchy, combinational-loop, and structural RTL/netlist checks when applicable.
- Use `Surelog`/`UHDM` or `sv-tests`-style references for SystemVerilog frontend coverage when practical.
- Use metadata/expected-diagnostic comparison when no practical open-source golden exists for a heuristic RTL risk case.

## P0 Combinational Loop Rule

- Case ID must be `P0_COMBINATIONAL_LOOP`.
- Prefer implementing this as an RTL Timing Risk Profiling rule, or `both` only if the existing registry already classifies it across lint and profiling.
- Build a real combinational signal dependency graph from continuous assignments and combinational procedural blocks.
- Use a standard strongly connected component algorithm such as Tarjan or Kosaraju to detect cycles.
- Treat clocked/sequential boundaries as graph cut points; ordinary register feedback must not be reported as a combinational loop.
- Report both self-loops and multi-signal loops.
- Evidence should include SCC nodes, edge list or cycle path, relevant assignment/procedural locations, and block kind.
- Use Yosys `check` and, when available, `scc` as development-time reference only.
- Candidate reference command:

```bash
yosys -p "read_verilog -sv <files>; hierarchy -top <top>; proc; opt; check; scc"
```

- Golden comparison must normalize Yosys findings before comparing to STA-lite diagnostics.
- Do not require Yosys for normal RTL Review or Profiling runtime.

## P0 FSM Robustness Rule

- Case ID must be `P0_FSM_ROBUSTNESS`.
- Treat this rule as a conservative RTL heuristic, not formal FSM verification.
- Prefer common FSM patterns first: state register in clocked logic, next-state signal in combinational logic, and `case (state)` transition blocks.
- Detect missing reset/default initialization, missing transition `default`, unsafe default recovery, incomplete next-state assignment, declared-but-unhandled states, and obvious terminal/dead states when evidence is reliable.
- Avoid overclaiming support for complex generated FSMs, deeply parameterized encodings, or full SystemVerilog enum/type elaboration unless the frontend actually supports them.
- Diagnostics must include state register, next-state signal when found, state literals, missing states, reset/default evidence, case location, confidence, Chinese message, and Chinese suggestion.
- Use Yosys FSM passes as development-time reference where practical:

```bash
yosys -p "read_verilog -sv <files>; hierarchy -top <top>; proc; opt; fsm_detect; fsm_extract; fsm_info"
```

- Yosys FSM output may confirm extraction and state structure, but metadata/expected-diagnostic comparison is acceptable for robustness warnings that Yosys does not directly report.
- If only common FSM patterns are supported, keep the coverage status `partially_supported` and document exact limits instead of overstating `supported`.

## P1 Excessive Reset Rule

- Case ID must be `P1_EXCESSIVE_RESET`; owner is `profiling`.
- Analyze reset branches in clocked RTL and collect reset signal, polarity, reset kind, affected registers, declared widths when available, source locations, and estimated reset-bit count.
- Use documented/configurable thresholds for register count and reset-bit count; this is an RTL structural risk heuristic, not a physical reset-tree analysis.
- Do not confuse clock-enable logic with reset logic.
- Evidence must include reset signal, reset kind, count/width estimate, threshold, and relevant source locations.
- Use Yosys `proc; opt; stat` and optional structural/netlist inspection as a development-time reference for resettable-cell extraction. Use expected metadata for STA-lite threshold decisions.

## P1 Xprop CaseX/CaseZ Rule

- Case ID must be `P1_XPROP_CASEX_CASEZ`; owner is `lint`.
- Detect every `casex` statement and issue a Chinese risk warning.
- Detect `casez` and report wildcard matching evidence such as `?` or `z` literals when available.
- Do not flag ordinary `case` statements or safe explicit-mask coding without wildcard case semantics.
- Treat `casex` as high-confidence risk; rate `casez` based on concrete wildcard evidence and do not claim every `casez` is a functional error.
- Use Verilator `--lint-only --Wall` as development-time reference when its installed version emits relevant diagnostics; otherwise use expected metadata.

## P1 Signed/Unsigned Rule

- Case ID must be `P1_SIGNED_UNSIGNED`; owner is `lint`.
- Track declared signedness and width when the existing frontend can parse them.
- Inspect assignments, arithmetic, comparisons, shifts, concatenations, and ternaries for concrete mixed signed/unsigned risk.
- Diagnostics should include operand names/types/widths when known, operator, location, confidence, Chinese message, and Chinese suggestion for explicit cast/extension.
- Avoid reporting when signedness evidence is unavailable; do not claim full SystemVerilog type-system or cast support.
- Use Verilator `--lint-only --Wall` as development-time reference for width/unsigned-related output where available; use expected metadata for rule-specific patterns it does not report.

## P1 Multi-Clock Always Rule

- Case ID must be `P1_MULTI_CLOCK_ALWAYS`; owner is `lint` or `both` according to the case registry.
- Detect more than one independent clock-edge event in a procedural event control.
- Do not flag a normal single-clock plus asynchronous-reset form such as `posedge clk or negedge rst_n`.
- Report the event list, identified clock/reset signals, location, confidence, Chinese message, and Chinese suggestion.
- Treat unusual event expressions, macro-generated controls, and unsupported SystemVerilog procedural semantics conservatively.
- Use Yosys `read_verilog -sv; hierarchy -top <top>; proc; check` as development-time reference where available; Verilator may be a secondary reference.

## Backend Report Location Rules

- Treat report-to-RTL location assistance as a current-version product goal.
- Keep report parsers and RTL mapping logic outside GUI widgets.
- Prefer deterministic source indexes for modules, instances, signals, registers, always blocks, assignments, and source line spans.
- Backend path/report tokens should map to likely RTL candidates with confidence and evidence.
- If exact mapping is not possible, return ranked candidates and a clear Chinese explanation instead of pretending certainty.
- This feature helps debug backend reports; it does not prove signoff timing correctness.

## Lint CLI Flow

Keep or create a CLI flow similar to:

```bash
sta-lite lint \
  --rtl src/*.v src/*.sv \
  --top TOP \
  --include inc/ \
  --define SYNTHESIS=1 \
  --rules rules/custom_rules.json \
  --sdc constraints.sdc \
  --out reports/lint_run
```

For regression, keep or create commands similar to:

```bash
sta-lite lint-regress --cases lint --out reports/lint_diff
sta-lite lint-diff --cases lint --out reports/lint_diff
```

Exact command names may differ, but the capability must exist and be documented.

## Later STA CLI Flow

For later synthesis/STA tasks only, keep or create a flow similar to:

```bash
sta-lite analyze \
  --top TOP \
  --rtl src/*.v \
  --clock clk \
  --period 10 \
  --lib path/to/cells.lib \
  --out reports/run1
```

This later flow may use Yosys and OpenSTA, but it must stay separate from lint corpus/regression tasks.

## RTL Risk CLI Flow

Keep or create a CLI flow similar to:

```bash
sta-lite risk \
  --rtl src/*.v src/*.sv \
  --top TOP \
  --sdc constraints.sdc \
  --out reports/risk_run
```

The risk flow must not invoke synthesis or STA tools by default.

## Lint Output Rules

Each normal lint run should create:

- `lint.log`
- `lint_summary.json`
- optional debug artifacts such as `tokens.json` or `ast.json`

Each differential regression run should create:

- `verilog_iverilog_results.json`
- `sta_lite_results.json`
- `sv_metadata_results.json`
- `diff_summary.json`
- `missing_coverage.md`
- `coverage_matrix.json`
- `coverage_matrix.md`

Generated reports should be gitignored when practical.

## RTL Risk Output Rules

Each risk run should create:

- `risk.log`
- `risk_summary.json`
- `risk_report.md`

Generated risk reports should be gitignored when practical unless explicitly requested.

## Corpus Categories

Maintain categorized Verilog error examples for:

- syntax
- lexical
- declaration
- module_port
- expression
- assignment
- procedural_block
- preprocessor
- generate
- instantiation
- function_task
- specify_udp

Maintain categorized Verilog warning examples for:

- implicit_net
- width_range
- port_connection
- timescale
- unused_unconnected
- multiple_driver
- latch_risk
- style_timing_risk

Maintain categorized SystemVerilog error examples for:

- syntax
- declaration_type
- always_procedure
- package_import
- interface_modport
- enum_struct_typedef
- array_dimension
- class_unsupported

Maintain categorized SystemVerilog warning examples for:

- implicit_cast_width
- always_comb_latch_risk
- enum_usage
- interface_connection
- style_timing_risk

## Coverage Matrix Rules

Maintain a coverage matrix under `reports/lint_diff/`:

```text
coverage_matrix.json
coverage_matrix.md
```

The matrix must track:

- language
- kind: error or warning
- grammar area
- category
- case count
- STA-lite result
- golden/reference/metadata result
- support status: `supported`, `partially_supported`, `unsupported_diagnostic`, `unsupported_by_design`, or `not_covered`
- next recommended improvement

The Markdown report must be in Chinese.

## Warning Classification

The internal lint engine should classify:

- syntax errors
- unsupported constructs
- implicit net risk
- duplicate declarations
- malformed module/port declarations
- malformed expressions
- malformed assignments
- malformed procedural blocks
- preprocessor errors
- instantiation errors
- Verilog warning-like issues reported by `iverilog -Wall`
- SystemVerilog warning-like issues defined by metadata expectations

## Non-Goals

Do not implement these unless explicitly requested:

- formal IEEE certification
- full SystemVerilog semantic/type elaboration
- functional simulation
- running `vvp`
- signoff-level STA
- FPGA real physical interconnect delay modeling
- placement/routing estimation
- ML timing prediction
- multi-corner/multi-mode timing
- full PrimeTime command compatibility
- automatic Verilog/SystemVerilog repair
- mandatory OpenSTA/Yosys/OpenROAD dependency for RTL risk profiling

## Git And GitHub Rules

### Stable Package Rules

- The first stable installable release is `v0.2.0`; `sta_lite.__version__`, tag, filenames, and release notes must remain consistent.
- Support Windows 10 x64, Windows 11 x64, and Ubuntu 20.04+ x86_64, with Windows as the first-priority release platform.
- Build Windows EXE files on a Windows runner. PyInstaller output is platform-specific and must not be presented as a trustworthy cross-compiled Windows release.
- Build Linux frozen packages on the oldest supported glibc baseline, currently Ubuntu 20.04.
- Release packages must embed CPython and STA-lite-owned resources so RTL Review, Lint, Profiling, and Case Coverage work immediately after installation.
- Do not package `tools/`, `nangate45/`, external EDA executables, or third-party Liberty data. Backend Analysis dependencies remain optional and user-provided.
- A stable binary release requires source regressions, frozen CLI and GUI smoke tests, dependency notices, release notes, and SHA-256 checksums.
- Generated installers belong in GitHub Release Assets. Build artifacts must retain the requested `install_package/window10`, `install_package/window11`, or `install_package/ubuntu20` directory layout, but large binaries should not be committed to normal Git history.
- Install and uninstall must not remove the user's `STA-Lite-Workspace`, RTL sources, or generated reports.

- Never use destructive git commands such as `git reset --hard` or `git checkout --` unless explicitly requested.
- Do not revert unrelated user changes.
- Before committing, run `git status --short` and review the intended file set.
- Commit source code, tests, examples, corpus metadata, and documentation.
- Do not commit local logs, generated reports, caches, temporary files, virtual environments, simulator outputs, or local secrets.
- If a GitHub push is requested and a remote is configured, push the verified commit to the current branch.
- If push fails due to missing remote, authentication, or network, keep the local commit and explain the blocker in Chinese.
- Prefer a concise commit message that describes the product change, such as `feat: prepare STA-lite lint v0`.

## Verification

After meaningful changes:

1. Follow the task-specific verification requirements in `Task.md`.
2. For lint tasks, run STA-lite lint regression and applicable `iverilog -g2005 -Wall -tnull` golden checks.
3. For RTL risk tasks, run risk smoke tests without OpenSTA/Yosys/OpenROAD and verify expected risk IDs.
4. For GUI tasks, verify all five required pages and their controller/import behavior.
5. Verify that a combined RTL Review run equals the union of standalone Lint and Profiling results for the same inputs.
6. Verify Case Coverage totals and statuses against the underlying registry/matrix.
7. Run non-GUI lint/risk/orchestration tests if display support is unavailable.
8. For Backend Analysis tasks, verify existing Yosys/OpenSTA behavior when tools are available; if tools are missing, verify graceful Chinese blockers.
9. If optional gold reports exist, run gold comparison; if not, do not treat missing gold as failure.
10. Confirm previously released v0 lint behavior is not broken, or explain any blocker in Chinese.
11. If verification is blocked, explain the blocker in Chinese and leave the implementation ready for the expected environment.
