# Technical Rules

## Codex Execution Rules

- Before making changes, read `AGENTS.md`, `Goal.md`, `Task.md`, `Rules.md`, and existing source/tests/examples.
- Ask fewer questions. Inspect the repository, infer the current state, and implement directly unless progress would be unsafe or impossible.
- All user-facing progress logs, error messages, README/report text, verification summaries, and final summaries must be in Simplified Chinese.
- Keep final summaries concise and include: changed files, executed commands, verification results, remaining gaps, and next suggested step.
- Prefer completing implementation plus verification in one pass instead of only proposing a plan.
- If verification is blocked by missing local tools, GUI display, or environment variables, explain the blocker in Chinese and leave the code ready for the expected environment.
- When a task asks for GitHub submission, perform implementation, verification, `.gitignore` cleanup, commit, and push if the remote/authentication are available.

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
  core/          # reusable workflows and run models
  parsers/       # report/log parsers for later STA/backend reports
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
tests/           # regression tests
reports/         # generated outputs, gitignored when practical
README.md
```

Do not put all logic into a single GUI file or a single linter file. GUI code should call reusable core/lint services.

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
- support status: `supported`, `partially_supported`, `unsupported_diagnostic`, or `not_covered`
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

## Git And GitHub Rules

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

1. Run STA-lite lint across all four corpus roots.
2. Run `iverilog -g2005 -Wall -tnull` on Verilog error/warning examples.
3. Compare SystemVerilog cases against metadata expectations or an optional SV reference adapter.
4. Generate `diff_summary.json`, Chinese `missing_coverage.md`, `coverage_matrix.json`, and Chinese `coverage_matrix.md`.
5. Confirm the previous zero-miss baseline is not regressed.
6. Improve the internal lint engine for the highest-priority missed categories.
7. If verification is blocked, explain the blocker in Chinese and leave the implementation ready for the expected environment.
