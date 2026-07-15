# Deprecated：旧 Verilog 注错语料

本目录是旧版 `lint/error_example/` 单一语料布局，当前已 deprecated。

新的 canonical 目录已经拆分为：

```text
lint/verilog_error_example/
lint/verilog_warning_example/
lint/system_verilog_error_examplr/
lint/system_verilog_warning_example/
```

新增或维护用例时，请使用新四目录。旧目录仅保留历史样例和兼容参考，不再作为主回归入口。

完整回归命令：

```sh
./scripts/check_lint_diff.sh
```

新报告输出：

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

下面是旧版说明，保留用于迁移对照。

## 当前错误类型

### syntax

基础语法结构错误：

- 缺少分号
- 端口列表缺少逗号
- 圆括号、中括号不匹配
- `begin/end` 不匹配
- 缺少 `endmodule`
- 非法 token

### declaration

声明相关错误：

- 重复声明信号
- 非法 net/reg 声明组合
- ``default_nettype none`` 下使用未声明标识符
- range 写法错误
- 使用关键字作为标识符

### module_port

模块和端口相关错误：

- 模块头部格式错误
- 非 ANSI 端口列表中端口未声明方向
- 重复端口
- 冲突方向声明
- 端口宽度重复/可疑声明

### expression

表达式错误：

- 非法数字常量
- 拼接表达式不完整
- 三目表达式不完整
- 缺少操作数
- bit-select / part-select 写法错误

### assignment

赋值错误：

- 连续赋值缺少 RHS
- 过程赋值缺少 RHS
- 非法 lvalue
- always 中对 wire 过程赋值
- 连续赋值和过程赋值混合驱动

### procedural_block

过程块结构错误：

- always 事件控制 malformed
- if/else 结构错误
- case 结构错误
- 缺少 endcase
- 阻塞/非阻塞赋值 token 写错

### preprocessor

预处理错误：

- include 文件缺失
- 宏展开后产生非法代码
- 条件编译缺少 endif
- 未定义宏导致非法代码

### instantiation

模块例化错误：

- 缺少实例名
- 命名端口连接格式错误
- 混用命名连接和位置连接
- 例化未定义模块

### warning_like

`iverilog -Wall` 能报告的 lint-like warning：

- 隐式网线
- 子模块端口未连接
- select 越界
- timescale 不一致或缺失
- 端口连接宽度不匹配

## case.json 字段

示例：

```json
{
  "id": "syntax_missing_semicolon_assign_002",
  "category": "syntax",
  "description_zh": "连续赋值语句缺少结尾分号。",
  "top": "top",
  "files": ["missing_semicolon_assign.v"],
  "expected_iverilog_status": "fail",
  "expected_keywords": ["syntax"],
  "include_dirs": [],
  "defines": [],
  "sta_lite_should_detect": true
}
```

`expected_iverilog_status` 取值：

- `fail`：`iverilog` 退出码非零。
- `warning`：`iverilog` 退出码为 0，但 `-Wall` 输出 warning。
- `pass`：golden 不应检出问题。

差分脚本按 case 的预期状态做严格匹配：`fail` 用例需要 STA-lite 给出相关 error/unsupported，`warning` 用例需要给出相关 warning/error。`RTL001_DEFAULT_NETTYPE` 是跨用例通用风格告警，不会单独算作当前 case 的有效命中。

## 运行方式

从仓库根目录运行：

```sh
./scripts/check_lint_diff.sh
```

该命令会生成/刷新当前语料、运行 STA-lite 内部 lint、运行 `iverilog -g2005 -Wall -tnull -s <top> <files>`，并生成 `reports/lint_diff/` 下的差分报告。

## 当前覆盖状态

当前主语料已迁移到四个 canonical 目录，最近一次完整差分规模为 147 个 case（Verilog 106、SystemVerilog 41），覆盖 Verilog error/warning 与 SystemVerilog error/warning。最近一次差分结果：

- 期望检出但 STA-lite 漏报：0
- 报告文件：`reports/lint_diff/diff_summary.json`
- 漏报列表：`reports/lint_diff/missing_coverage.md`
- 覆盖矩阵：`reports/lint_diff/coverage_matrix.md`

后续新增 case 时，优先把真实项目或开源 issue 中出现的最小复现加入本目录，再用差分报告驱动 parser/rule 修复。
