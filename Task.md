# Current Task

## Long-Task Objective

Maintain every P0 and P1 case at `supported` coverage whenever it is reliably achievable in STA-lite's RTL-only product boundary.

For a case that cannot yet reach `supported`, implement the strongest reliable common subset, keep it as `partially_supported`, and show a Chinese explanation, evidence, exact limitation, and next improvement in Case Coverage. Do not leave P0/P1 cases silently stale or `not_covered` without review.

At the same time, make STA-lite an independent software product for its core capability:

```text
RTL files
  -> STA-lite internal parser / lint / risk rules
  -> GUI and CLI results
```

The production core must not require Yosys, OpenSTA, Verilator, Icarus Verilog, Surelog, sv-tests, or another external EDA tool/software installation.

## Independent Product Boundary

The following must work with no external EDA tool installed or discoverable on `PATH`:

- `RTL Review`
- `RTL Lint`
- `RTL Timing Risk Profiling`
- `Case Coverage`
- core CLI lint/risk commands
- P0/P1 case detection, diagnostics, reports, and GUI display

Yosys, OpenSTA, Verilator, iverilog, Surelog/UHDM, and sv-tests are allowed only as:

- development-time golden/reference tools
- optional offline report/reference adapters
- optional Backend Analysis integration when explicitly configured

The `Yosys/OpenSTA Backend Analysis` page must never block startup or core RTL review. If its optional external tools are absent, show a clear Chinese unavailable status and retain report viewing/parsing capabilities that do not need those tools.

No production lint/profiling rule may invoke an external tool subprocess, parse external-tool output as its primary result, or change its outcome based on tool availability.

## Long-Task Execution Plan

### Phase 1: Establish The Coverage Baseline

1. Read the shared P0/P1 case registry, coverage matrix, rule map, test corpus, and GUI coverage model.
2. Generate a Chinese baseline report listing every P0/P1 case with:
   - case ID and Chinese name
   - owner: `lint`, `profiling`, or `both`
   - current status
   - existing rule/test/evidence paths
   - known limitation
   - candidate golden/reference tool
3. Treat every `partially_supported`, `not_covered`, and stale/unverified `supported` status as work requiring review.
4. Do not change a status until implementation and verification evidence agree with the registry.

### Phase 2: Upgrade Rules And Tests

For each P0/P1 case, in priority order P0 then P1:

1. Define the documented minimum supported scope.
2. Extend STA-lite's internal parser, semantic model, lint rule, or risk rule as required.
3. Keep the rule in its existing owner workflow; do not create GUI-only detection logic or duplicate engines.
4. Add focused positive and negative Verilog/SystemVerilog examples under the correct corpus directory.
5. Add or update automated tests, expected diagnostics, and Case Coverage evidence.
6. Run regressions before promoting the case to `supported`.

Use `supported` only when the documented scope, positive/negative tests, and golden/reference or justified expected-metadata comparison pass.

Use `partially_supported` only when the common subset is implemented and tested but specific syntax, elaboration, parameterization, or semantic patterns remain outside the implemented scope. The exact unsupported subset must be visible in Chinese.

Use `unsupported_by_design` only when the requested property fundamentally needs information outside RTL-only analysis, such as physical extraction, routing, clock tree, PVT/OCV/MCMM, formal proof, or signoff CDC/RDC. Implementation difficulty alone is not a valid reason.

### Phase 3: Golden/Reference Comparison

For every case modified in this long task:

1. Search current official project documentation, package repositories, and mature open-source implementations for an appropriate golden/reference tool.
2. Prefer a locally reproducible Ubuntu/WSL2 CLI tool.
3. Install only the required optional tool using a package manager or official project instructions.
4. Record in Chinese: source URL, version, install command, exact comparison command, normalized result, and limitations.
5. Compare normalized STA-lite diagnostics against normalized golden/reference findings.
6. When no practical golden can express a heuristic risk policy, use versioned expected metadata and explain why it is the valid reference.

Recommended mapping remains:

- `iverilog -g2005 -Wall -tnull` for Verilog compile/lint-style diagnostics
- `Verilator --lint-only --Wall` for width, signedness, constructs, and lint warnings where applicable
- Yosys frontend/process/structural passes for synthesizability, reset, loop, FSM, and structural checks where applicable
- Surelog/UHDM or sv-tests references for practical SystemVerilog frontend coverage where available

Golden tools must be isolated from normal product runtime. Tests must skip gracefully with Chinese output if an optional tool is absent.

### Phase 4: Standalone Product Hardening

Make the core product independently runnable and test it as such.

Required work:

- remove or isolate any production code path that imports, executes, or depends on an external EDA tool for P0/P1 results
- use STA-lite-owned parser/AST/rule/data-model infrastructure for production diagnostics
- keep golden/reference adapters under clearly separated development/test modules
- ensure GUI controllers call internal workflows and do not shell out to golden tools
- ensure generated reports identify their producer as STA-lite, not as an external tool result
- provide clear Chinese optional-tool status in Backend Analysis without affecting core pages
- document the supported local runtime and packaging/startup method

### Phase 5: GUI, CLI, And Coverage Consistency

For every final case status:

- `RTL Review` must aggregate the same internal results from RTL Lint and RTL Timing Risk Profiling.
- The standalone owner page must show the same rule ID, severity, file/line, confidence, evidence, Chinese message, and suggestion.
- Case Coverage must show current status, test status, golden/reference status, evidence path, limitation, and next improvement.
- CLI outputs and GUI results must use the same normalized diagnostic/result model.
- No page may report a case as `supported` merely because a golden tool finds it.

## Required Verification

1. Run a clean-core check with external golden tools unavailable or excluded from `PATH`.
2. Verify all core GUI pages and CLI lint/risk flows still start and run in that environment.
3. Verify production P0/P1 results are unchanged by presence versus absence of golden tools.
4. Run focused positive and negative tests for every changed case.
5. Run lint_v0 and profiling regression/smoke suites after each meaningful batch.
6. Run golden/reference comparisons for every changed case where practical; otherwise record the metadata fallback in Chinese.
7. Verify Case Coverage counts/statuses/evidence agree with the underlying registry and tests.
8. Verify `RTL Review` equals the union of standalone Lint and Profiling results for the same RTL configuration.
9. Verify Backend Analysis gracefully reports missing optional tools without breaking core application behavior.
10. Explain every blocked test, partial status, and remaining gap in Chinese.

### Phase 6: Stable Cross-Platform Distribution

1. Keep the stable application version, Git tag, release notes, installer filenames, and dependency manifests synchronized.
2. Build Windows 10 and Windows 11 x64 installers on a native Windows runner; never claim a Linux cross-build as a verified Windows EXE.
3. Build the Ubuntu 20.04+ x86_64 package against an Ubuntu 20.04 glibc baseline.
4. Bundle the Python runtime, GUI assets, examples, case corpus, and Case Coverage evidence, while excluding `tools/`, `nangate45/`, and all optional backend EDA binaries/data.
5. Verify the frozen CLI version and frozen GUI `/api/case_coverage` endpoint before publishing.
6. Publish installers and SHA-256 checksums as GitHub Release Assets only after the complete lint/risk/review regression passes.
7. Preserve user workspaces and reports during application upgrades and uninstall.

## Documentation Requirements

Update Chinese documentation as the long task progresses:

- P0/P1 coverage baseline and completion status
- supported scope for each rule
- partial-support and unsupported reasons
- corpus/test locations
- golden/reference source, version, installation, and comparison commands
- standalone runtime guarantee and optional-tool boundary
- remaining known gaps and next priority

Avoid a giant one-time report that becomes stale. Keep the case registry, coverage matrix, README documents, and generated verification summaries consistent after each completed batch.

## Hard Boundaries

- Do not change lint_v0 behavior unless needed for a targeted P0/P1 rule; run regressions whenever shared code changes.
- Do not use external EDA tools as the production lint/profiling engine.
- Do not make optional golden/reference tools mandatory for normal user installation or execution.
- Do not claim signoff STA, physical timing prediction, formal verification, full SystemVerilog elaboration, or full CDC/RDC coverage.
- Do not downgrade a case to `partially_supported` without implementing and testing a useful subset.
- Do not mark a case `supported` without executable evidence.

## Completion Criteria

This long task is complete when:

1. Every P0/P1 case has a reviewed, evidence-backed current status.
2. Every supportable P0/P1 case reaches `supported` for its documented scope.
3. Every remaining `partially_supported` case has a tested subset, Chinese limitation, evidence, and next improvement.
4. Core STA-lite RTL Review/Lint/Profiling/Coverage and CLI work without any external EDA tool installed.
5. Golden/reference tools are used only by development/test adapters and are documented for every changed case where practical.
6. GUI, CLI, corpus, registry, coverage matrix, and tests agree on status and diagnostics.
7. The final Chinese summary includes coverage changes, standalone-runtime verification, golden tools/commands, regression results, remaining partial cases, and next suggested step.
