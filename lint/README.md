# STA-lite Lint 语料与差分回归

本目录是 STA-lite 内部 lint 前端的回归入口。生产 lint 引擎仍由项目内部 Python 代码实现：

```text
RTL -> preprocessing -> lexer -> parser -> AST/symbol context -> built-in/custom rules -> lint_summary.json
```

外部工具只用于开发期参考。Verilog 用例使用 `iverilog` 作为 golden；SystemVerilog 用例默认使用 `case.json` metadata 做 expected-vs-actual 对比，不强制依赖外部 SV reference tool。

## Canonical 目录

当前必须使用四个语料根目录：

```text
lint/
  verilog_error_example/
  verilog_warning_example/
  system_verilog_error_examplr/
  system_verilog_warning_example/
```

`system_verilog_error_examplr` 是本里程碑指定目录名，虽然看起来像拼写错误，当前按需求原样保留。

旧目录 `lint/error_example/` 已 deprecated，仅保留兼容说明和历史样例；新增用例不要再放入旧目录。

## 当前规模

- 历史基线：74 个 case，0 个期望检出漏报。
- 当前规模：130 个 case，最近一次完整差分 0 个期望检出漏报。
- Verilog error：74 个 case
- Verilog warning：16 个 case
- SystemVerilog error：31 个 case
- SystemVerilog warning：9 个 case

## case.json

每个 case 都应包含 `case.json`：

```json
{
  "id": "verilog_syntax_missing_semicolon_decl_001",
  "language": "verilog",
  "kind": "error",
  "category": "syntax",
  "standard_focus": "IEEE1364",
  "description_zh": "wire 声明缺少结尾分号。",
  "top": "top",
  "files": ["missing_semicolon_decl.v"],
  "expected_status": "fail",
  "expected_keywords": ["syntax"],
  "include_dirs": [],
  "defines": [],
  "sta_lite_should_detect": true
}
```

`language` 取值为 `verilog` 或 `systemverilog`。`kind` 取值为 `error` 或 `warning`。`expected_status` 取值为 `fail`、`warning` 或 `pass`。

## 运行方式

生成/刷新内置语料并运行完整差分：

```sh
./scripts/check_lint_diff.sh
```

等效 CLI：

```sh
PATH="$PWD/tools/bin:$PATH" ./sta-lite lint-diff \
  --write-corpus \
  --out reports/lint_diff \
  --iverilog iverilog
```

只扫描指定语料根目录：

```sh
PATH="$PWD/tools/bin:$PATH" ./sta-lite lint-diff \
  --cases lint/verilog_error_example lint/system_verilog_error_examplr \
  --out reports/lint_diff_partial \
  --iverilog iverilog
```

单独运行一个 STA-lite lint：

```sh
./sta-lite lint \
  --rtl lint/verilog_error_example/syntax/verilog_syntax_missing_semicolon_decl_001/missing_semicolon_decl.v \
  --top top \
  --out runs/lint_one \
  --fail-on never
```

单独运行一个 Verilog iverilog golden：

```sh
PATH="$PWD/tools/bin:$PATH" iverilog -g2005 -Wall -tnull -s top \
  lint/verilog_error_example/syntax/verilog_syntax_missing_semicolon_decl_001/missing_semicolon_decl.v
```

不要运行 `vvp`。本目录只做语法、编译期和 lint-like 检查，不做功能仿真。

## 报告文件

完整差分报告输出到：

```text
reports/lint_diff/
  verilog_iverilog_results.json
  sta_lite_results.json
  sv_metadata_results.json
  diff_summary.json
  missing_coverage.md
  coverage_matrix.json
  coverage_matrix.md
```

- `verilog_iverilog_results.json`：Verilog 用例的 iverilog 命令、退出码、stdout/stderr 和归一化状态。
- `sta_lite_results.json`：所有用例的 STA-lite lint 输出摘要。
- `sv_metadata_results.json`：SystemVerilog 用例的 metadata 参考期望。
- `diff_summary.json`：按 language/category/kind 汇总覆盖率和逐 case 对比。
- `missing_coverage.md`：中文漏报报告，是下一轮 parser/rule 修复队列。
- `coverage_matrix.json` / `coverage_matrix.md`：按语言、error/warning、语法区域和类别组织的覆盖矩阵；`not_covered` 表示该类别仍没有语料，`unsupported_diagnostic` 表示当前能稳定给出明确 unsupported 诊断但还没有完整 AST/语义支持。

当前 `coverage_matrix.md` 不再存在 `not_covered` 类别；`verilog/warning/unused_unconnected` 已有 6 个最小用例并由 STA-lite 内部规则检出。

## 当前限制

- Verilog 覆盖是 IEEE 1364-oriented practical corpus，不是正式标准认证。
- Verilog `generate`、`function`、`task` 已进入语法级结构化识别；`specify` 和 UDP 仍以明确 `UNSUPPORTED_VERILOG` 或结构错误诊断为主。
- SystemVerilog 已对 package/import、typedef/enum/struct、interface/modport、packed/unpacked array 和简单 cast 做语法级识别；仍不做完整类型系统、package elaboration、interface 连接 elaboration 或 class/assertion/covergroup 语义。
- `iverilog` 只作为 Verilog 开发期 golden，不是 STA-lite 生产 lint 引擎。
- SystemVerilog 默认不依赖外部参考工具；当前使用 metadata expected-vs-actual。
