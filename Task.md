# Current Task

## Immediate Execution Summary

Implement the next lint improvement and then prepare the project for a v0 GitHub submission.

Current known result from the latest regression:

- `coverage_matrix.md` still shows `verilog/warning/unused_unconnected` has no cases.
- Some capabilities are still precise unsupported diagnostics rather than structured semantic support:
  - Verilog `generate`
  - Verilog `function`
  - Verilog `task`
  - Verilog `specify`
  - Verilog `UDP`
  - SystemVerilog `class`
  - SystemVerilog assertion/covergroup
- Previous regression had zero missed expected detections. Preserve that baseline.

The current task has two phases:

1. Improve lint coverage and implementation.
2. Prepare and publish the v0 version to GitHub, including `.gitignore`.

## Phase 1: Lint Improvement

### Required Fix 1: Add `unused_unconnected` Warning Coverage

`verilog/warning/unused_unconnected` currently has no cases. Add both corpus cases and detection support.

Add examples under:

```text
lint/verilog_warning_example/unused_unconnected/
```

Cover at least:

- declared signal never used
- assigned signal never read
- module input never used
- module output never driven
- instance output left unconnected
- named port connection left empty, such as `.out()`

Each case should include `case.json` metadata and a minimal Verilog file.

Update STA-lite lint so it can report these warnings with normalized diagnostics, Chinese explanation, and useful suggestions.

### Required Fix 2: Start Structured Verilog AST Support

Move these Verilog constructs from generic unsupported diagnostics toward structured AST recognition where practical:

- `generate/endgenerate`
- `genvar`
- generate-for
- generate-if
- named generate block
- `function/endfunction`
- `task/endtask`
- function call in expressions

Do not attempt full elaboration yet. Syntax-level structured AST support is enough for v0.

For constructs still not implemented, keep precise unsupported diagnostics:

- `specify/endspecify`
- `primitive/endprimitive` UDP
- detailed specify timing checks
- UDP table semantics

### Required Fix 3: Keep SystemVerilog Unsupported Diagnostics Precise

Keep these as explicit unsupported diagnostics unless syntax-level support already exists:

- `class`
- assertions
- covergroup

The diagnostic should not be a generic parser crash. Use a category such as `UNSUPPORTED_SYSTEMVERILOG` and include Chinese guidance.

### Required Reports

After changes, regenerate:

```text
reports/lint_diff/diff_summary.json
reports/lint_diff/missing_coverage.md
reports/lint_diff/coverage_matrix.json
reports/lint_diff/coverage_matrix.md
```

The generated report files are verification artifacts and should not be committed unless the repository already intentionally tracks report snapshots.

## Phase 2: v0 GitHub Submission Preparation

After Phase 1 passes verification, prepare the project as a v0 version suitable for GitHub.

### Required Cleanup

- Create or update `.gitignore`.
- Ensure local logs, generated reports, caches, temporary files, simulation outputs, and local environment files are not committed.
- Keep source code, documentation, tests, examples, and corpus `case.json` files tracked.
- Do not delete useful source files or examples.

### Required Documentation

Update Chinese README/documentation so v0 users can understand:

- what STA-lite lint v0 can do
- how to run lint on a single design
- how to run corpus regression
- how to interpret `coverage_matrix.md`
- why `iverilog` is used only as Verilog development-time golden
- why `vvp` is not run
- current limitations
- next roadmap

### Required Verification Before Commit

Run the available regression flow and confirm:

- `unused_unconnected` warning cases exist and are detected
- previous zero-miss baseline is not regressed
- Verilog examples still use `iverilog -g2005 -Wall -tnull` only as golden
- `vvp` is not run
- SystemVerilog metadata comparison still works
- `coverage_matrix.md` no longer shows `verilog/warning/unused_unconnected` as `not_covered`

If a tool or environment is missing, explain the blocker in Chinese and do not fake successful verification.

### GitHub Submission

If verification passes:

1. Run `git status --short`.
2. Review changed files and avoid committing generated logs/reports/caches.
3. Stage only intended files.
4. Create a v0 commit with a concise message, for example:

```text
feat: prepare STA-lite lint v0
```

5. Push to the configured GitHub remote and current branch if remote/authentication are available.
6. If pushing is blocked by missing remote/authentication/network, leave the local commit ready and explain the exact blocker in Chinese.

Do not overwrite or revert unrelated user changes.

## Acceptance Criteria

This task is complete when:

1. `lint/verilog_warning_example/unused_unconnected/` has meaningful cases.
2. STA-lite reports unused/unconnected warnings with normalized diagnostics.
3. Verilog generate/function/task have initial structured syntax/AST support, or remaining gaps are precise and documented.
4. SystemVerilog class/assertion/covergroup unsupported diagnostics remain precise.
5. Full lint regression passes without regressing the previous zero-miss baseline.
6. `coverage_matrix.md` no longer lists `verilog/warning/unused_unconnected` as missing coverage.
7. `.gitignore` prevents local logs, generated reports, caches, and temporary artifacts from being committed.
8. README/documentation is updated for v0.
9. A clean intended git commit is created.
10. The commit is pushed to GitHub, or a clear Chinese blocker is reported if push is not possible.
