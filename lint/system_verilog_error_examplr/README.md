# SystemVerilog Error 语料

本目录保存 SystemVerilog 错误级语料。目录名 `system_verilog_error_examplr` 按当前任务要求原样使用，即使看起来像拼写错误，也不要在本里程碑中擅自改名。

## 用途

- 覆盖常见 SystemVerilog 前端语法入口。
- 不要求完整 SV 语义、类型系统或 elaboration。
- 暂不支持的 SV 构造必须输出 `UNSUPPORTED_SYSTEMVERILOG`，不能静默通过或崩溃。

SystemVerilog 当前默认不强制依赖外部 reference tool；本目录使用 `case.json` metadata 做 expected-vs-actual 对比。

## 当前类别

- `declaration_type`：`logic` 等 SV 类型声明语法。
- `always_procedure`：`always_comb`、`always_ff` 结构和事件控制。
- `enum_struct_typedef`：`typedef`、`enum`、`struct packed` 语法级识别，以及 malformed typedef/enum 错误。
- `package_import`：`package/endpackage`、`import pkg::*`、`import pkg::name` 语法级识别，以及 malformed import/package 错误。
- `interface_modport`：`interface/endinterface`、`modport`、interface 实例形状的语法级识别。
- `array_dimension`：packed/unpacked array、多维 unpacked array、简单 cast 和维度错误。
- `class_unsupported`：`class`、assertion、property、covergroup 的精确 `UNSUPPORTED_SYSTEMVERILOG` 诊断。
- `syntax`：`inside` 等 SV 表达式构造 unsupported 识别。

## 运行

```sh
./sta-lite lint-diff \
  --cases lint/system_verilog_error_examplr \
  --out reports/lint_diff_sv_error
```

## 当前状态

当前内置 31 个 SystemVerilog error case。最近一次完整差分中，本目录没有发现 STA-lite 漏报。

## 限制

- package/import、interface/modport、typedef/enum/struct 当前只做语法级识别，不做完整符号解析和 elaboration。
- 不做 package symbol resolution、interface modport elaboration、enum 类型检查、struct 字段类型检查或 class/assertion/covergroup 语义。
