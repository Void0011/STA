from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GENERIC_STA_RULES = {"RTL001_DEFAULT_NETTYPE"}
DEFAULT_CORPUS_ROOTS = [
    "lint/verilog_error_example",
    "lint/verilog_warning_example",
    "lint/system_verilog_error_examplr",
    "lint/system_verilog_warning_example",
]


@dataclass(frozen=True)
class CorpusCase:
    id: str
    language: str
    kind: str
    category: str
    description_zh: str
    top: str
    files: dict[str, str]
    expected_status: str
    expected_keywords: tuple[str, ...] = ()
    support_files: dict[str, str] = field(default_factory=dict)
    standard_focus: str = ""
    include_dirs: tuple[str, ...] = ()
    defines: tuple[str, ...] = ()
    sta_lite_should_detect: bool = True
    root: str = ""


def c(
    *,
    id: str,
    language: str,
    kind: str,
    category: str,
    description_zh: str,
    top: str,
    files: dict[str, str],
    expected_status: str,
    expected_keywords: tuple[str, ...] = (),
    support_files: dict[str, str] | None = None,
    standard_focus: str | None = None,
    include_dirs: tuple[str, ...] = (),
    defines: tuple[str, ...] = (),
    sta_lite_should_detect: bool = True,
) -> CorpusCase:
    if language == "verilog" and kind == "error":
        root = "lint/verilog_error_example"
    elif language == "verilog" and kind == "warning":
        root = "lint/verilog_warning_example"
    elif language == "systemverilog" and kind == "error":
        root = "lint/system_verilog_error_examplr"
    elif language == "systemverilog" and kind == "warning":
        root = "lint/system_verilog_warning_example"
    else:
        raise ValueError(f"非法语料类型：{language}/{kind}")
    return CorpusCase(
        id=id,
        language=language,
        kind=kind,
        category=category,
        description_zh=description_zh,
        top=top,
        files=files,
        expected_status=expected_status,
        expected_keywords=expected_keywords,
        support_files=support_files or {},
        standard_focus=standard_focus or ("IEEE1364" if language == "verilog" else "SystemVerilog"),
        include_dirs=include_dirs,
        defines=defines,
        sta_lite_should_detect=sta_lite_should_detect,
        root=root,
    )


BUILTIN_CASES: list[CorpusCase] = [
    c(
        id="verilog_lexical_unterminated_string_001",
        language="verilog",
        kind="error",
        category="lexical",
        description_zh="字符串字面量缺少右侧双引号。",
        top="top",
        files={"unterminated_string.v": 'module top(output y);\n  assign y = "abc;\nendmodule\n'},
        expected_status="fail",
        expected_keywords=("syntax", "string"),
    ),
    c(
        id="verilog_lexical_unterminated_comment_002",
        language="verilog",
        kind="error",
        category="lexical",
        description_zh="块注释缺少结束符。",
        top="top",
        files={"unterminated_comment.v": "module top(output y);\n  /* comment\n  assign y = 1'b0;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("comment", "EOF"),
    ),
    c(
        id="verilog_syntax_missing_semicolon_decl_001",
        language="verilog",
        kind="error",
        category="syntax",
        description_zh="wire 声明缺少结尾分号。",
        top="top",
        files={"missing_semicolon_decl.v": "module top(input a, output y);\n  wire n\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_syntax_missing_semicolon_assign_002",
        language="verilog",
        kind="error",
        category="syntax",
        description_zh="连续赋值语句缺少结尾分号。",
        top="top",
        files={"missing_semicolon_assign.v": "module top(input a, output y);\n  assign y = a\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_syntax_extra_semicolon_port_003",
        language="verilog",
        kind="error",
        category="syntax",
        description_zh="ANSI 端口列表中出现额外分号。",
        top="top",
        files={"extra_semicolon_port.v": "module top(input a; output y);\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_syntax_missing_comma_port_004",
        language="verilog",
        kind="error",
        category="syntax",
        description_zh="ANSI 端口列表中两个端口之间缺少逗号。",
        top="top",
        files={"missing_comma_port.v": "module top(input a output y);\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax", "port"),
    ),
    c(
        id="verilog_syntax_unmatched_parenthesis_005",
        language="verilog",
        kind="error",
        category="syntax",
        description_zh="表达式缺少右括号。",
        top="top",
        files={"unmatched_parenthesis.v": "module top(input a, input b, output y);\n  assign y = (a & b;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_syntax_unmatched_bracket_006",
        language="verilog",
        kind="error",
        category="syntax",
        description_zh="位选择缺少右中括号。",
        top="top",
        files={"unmatched_bracket.v": "module top(input [3:0] a, output y);\n  assign y = a[2;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_syntax_unmatched_begin_007",
        language="verilog",
        kind="error",
        category="syntax",
        description_zh="always 块 begin 没有匹配 end。",
        top="top",
        files={"unmatched_begin.v": "module top(input clk, input d, output reg q);\n  always @(posedge clk) begin\n    q <= d;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_syntax_missing_endmodule_008",
        language="verilog",
        kind="error",
        category="syntax",
        description_zh="模块缺少 endmodule。",
        top="top",
        files={"missing_endmodule.v": "module top(input a, output y);\n  assign y = a;\n"},
        expected_status="fail",
        expected_keywords=("endmodule", "syntax"),
    ),
    c(
        id="verilog_syntax_illegal_token_009",
        language="verilog",
        kind="error",
        category="syntax",
        description_zh="源码中出现 Verilog 不支持的非法 token 序列。",
        top="top",
        files={"illegal_token.v": "module top(input a, output y);\n  assign y = a @@@;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_declaration_duplicate_signal_001",
        language="verilog",
        kind="error",
        category="declaration",
        description_zh="同一模块内重复声明信号。",
        top="top",
        files={"duplicate_signal.v": "module top(input a, output y);\n  wire n;\n  wire n;\n  assign n = a;\n  assign y = n;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("already", "declared"),
    ),
    c(
        id="verilog_declaration_invalid_net_reg_002",
        language="verilog",
        kind="error",
        category="declaration",
        description_zh="同一声明同时使用 wire 和 reg。",
        top="top",
        files={"invalid_net_reg.v": "module top(input a, output y);\n  wire reg n;\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_declaration_undeclared_default_nettype_003",
        language="verilog",
        kind="error",
        category="declaration",
        description_zh="default_nettype none 下使用未声明信号。",
        top="top",
        files={"undeclared_default_nettype.v": "`default_nettype none\nmodule top(input a, output y);\n  assign y = a & missing_sig;\nendmodule\n`default_nettype wire\n"},
        expected_status="fail",
        expected_keywords=("Unable to bind", "missing_sig"),
    ),
    c(
        id="verilog_declaration_range_syntax_004",
        language="verilog",
        kind="error",
        category="declaration",
        description_zh="向量范围缺少右边界。",
        top="top",
        files={"range_syntax.v": "module top(input a, output y);\n  wire [7:] n;\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_declaration_keyword_identifier_005",
        language="verilog",
        kind="error",
        category="declaration",
        description_zh="使用 Verilog 关键字作为标识符。",
        top="top",
        files={"keyword_identifier.v": "module top(input a, output y);\n  wire begin;\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_declaration_parameter_missing_value_006",
        language="verilog",
        kind="error",
        category="declaration",
        description_zh="parameter 声明缺少赋值表达式。",
        top="top",
        files={"parameter_missing_value.v": "module top(output y);\n  parameter WIDTH = ;\n  assign y = 1'b0;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_module_port_malformed_header_001",
        language="verilog",
        kind="error",
        category="module_port",
        description_zh="模块头部端口列表不完整。",
        top="top",
        files={"malformed_header.v": "module top(input a, output y;\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_module_port_missing_port_decl_002",
        language="verilog",
        kind="error",
        category="module_port",
        description_zh="非 ANSI 端口列表中的端口没有方向声明。",
        top="top",
        files={"missing_port_decl.v": "`default_nettype none\nmodule top(a, y);\n  input a;\n  assign y = a;\nendmodule\n`default_nettype wire\n"},
        expected_status="fail",
        expected_keywords=("port", "y"),
    ),
    c(
        id="verilog_module_port_duplicate_port_003",
        language="verilog",
        kind="error",
        category="module_port",
        description_zh="端口列表中重复端口名。",
        top="top",
        files={"duplicate_port.v": "module top(a, a);\n  input a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("duplicate", "port"),
    ),
    c(
        id="verilog_module_port_invalid_direction_004",
        language="verilog",
        kind="error",
        category="module_port",
        description_zh="端口方向声明互相冲突。",
        top="top",
        files={"invalid_direction.v": "module top(a);\n  input output a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_module_port_width_redecl_005",
        language="verilog",
        kind="error",
        category="module_port",
        description_zh="端口宽度声明和后续声明不一致。",
        top="top",
        files={"width_redecl.v": "module top(a, y);\n  input [3:0] a;\n  input a;\n  output y;\n  assign y = a[0];\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("already", "declared"),
    ),
    c(
        id="verilog_expression_invalid_number_001",
        language="verilog",
        kind="error",
        category="expression",
        description_zh="基数数字常量缺少实际数值。",
        top="top",
        files={"invalid_number.v": "module top(output [3:0] y);\n  assign y = 4'd;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_expression_malformed_concat_002",
        language="verilog",
        kind="error",
        category="expression",
        description_zh="拼接表达式缺少右大括号。",
        top="top",
        files={"malformed_concat.v": "module top(input a, input b, output [1:0] y);\n  assign y = {a, b;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_expression_malformed_ternary_003",
        language="verilog",
        kind="error",
        category="expression",
        description_zh="三目表达式缺少冒号和假值分支。",
        top="top",
        files={"malformed_ternary.v": "module top(input a, input b, output y);\n  assign y = a ? b;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_expression_missing_operand_004",
        language="verilog",
        kind="error",
        category="expression",
        description_zh="二元操作符右侧缺少操作数。",
        top="top",
        files={"missing_operand.v": "module top(input a, output y);\n  assign y = a & ;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_expression_bad_part_select_005",
        language="verilog",
        kind="error",
        category="expression",
        description_zh="part-select 语法缺少冒号左侧表达式。",
        top="top",
        files={"bad_part_select.v": "module top(input [7:0] a, output [3:0] y);\n  assign y = a[:3];\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_assignment_continuous_missing_rhs_001",
        language="verilog",
        kind="error",
        category="assignment",
        description_zh="连续赋值缺少右值。",
        top="top",
        files={"continuous_missing_rhs.v": "module top(output y);\n  assign y = ;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_assignment_procedural_missing_rhs_002",
        language="verilog",
        kind="error",
        category="assignment",
        description_zh="过程赋值缺少右值。",
        top="top",
        files={"procedural_missing_rhs.v": "module top(input clk, output reg q);\n  always @(posedge clk) begin\n    q <= ;\n  end\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_assignment_invalid_lvalue_003",
        language="verilog",
        kind="error",
        category="assignment",
        description_zh="连续赋值左侧不是合法 lvalue。",
        top="top",
        files={"invalid_lvalue.v": "module top(input a);\n  assign 1'b0 = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("l-value", "syntax"),
    ),
    c(
        id="verilog_assignment_wire_procedural_004",
        language="verilog",
        kind="error",
        category="assignment",
        description_zh="在 always 中对 wire 端口过程赋值。",
        top="top",
        files={"wire_procedural.v": "module top(input clk, input d, output y);\n  always @(posedge clk) begin\n    y <= d;\n  end\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("not a valid l-value", "reg"),
    ),
    c(
        id="verilog_assignment_mixed_driver_005",
        language="verilog",
        kind="error",
        category="assignment",
        description_zh="同一 reg 既被连续赋值又被过程赋值。",
        top="top",
        files={"mixed_driver.v": "module top(input clk, input d, output reg q);\n  assign q = d;\n  always @(posedge clk) q <= d;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("reg", "continuous"),
    ),
    c(
        id="verilog_procedural_bad_event_001",
        language="verilog",
        kind="error",
        category="procedural_block",
        description_zh="always 事件控制缺少边沿信号。",
        top="top",
        files={"bad_event.v": "module top(input clk, output reg q);\n  always @(posedge) q <= clk;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_procedural_bad_if_002",
        language="verilog",
        kind="error",
        category="procedural_block",
        description_zh="if 条件表达式为空。",
        top="top",
        files={"bad_if.v": "module top(input a, output reg y);\n  always @* begin\n    if () y = a;\n  end\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_procedural_bad_else_003",
        language="verilog",
        kind="error",
        category="procedural_block",
        description_zh="else 没有匹配的 if。",
        top="top",
        files={"bad_else.v": "module top(input a, output reg y);\n  always @* begin\n    y = a;\n  end else begin\n    y = 1'b0;\n  end\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_procedural_bad_case_004",
        language="verilog",
        kind="error",
        category="procedural_block",
        description_zh="case 表达式为空。",
        top="top",
        files={"bad_case.v": "module top(input [1:0] a, output reg y);\n  always @* begin\n    case ()\n      2'b00: y = 1'b0;\n    endcase\n  end\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_procedural_missing_endcase_005",
        language="verilog",
        kind="error",
        category="procedural_block",
        description_zh="case 语句缺少 endcase。",
        top="top",
        files={"missing_endcase.v": "module top(input [1:0] a, output reg y);\n  always @* begin\n    case (a)\n      2'b00: y = 1'b0;\n  end\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax", "endcase"),
    ),
    c(
        id="verilog_procedural_bad_nonblocking_006",
        language="verilog",
        kind="error",
        category="procedural_block",
        description_zh="非阻塞赋值操作符被错误拆成 `< =`。",
        top="top",
        files={"bad_nonblocking.v": "module top(input clk, input d, output reg q);\n  always @(posedge clk) begin\n    q < = d;\n  end\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_preprocessor_missing_include_001",
        language="verilog",
        kind="error",
        category="preprocessor",
        description_zh="include 文件不存在。",
        top="top",
        files={"missing_include.v": "`include \"does_not_exist.vh\"\nmodule top(input a, output y);\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("Include file", "No such"),
    ),
    c(
        id="verilog_preprocessor_malformed_define_002",
        language="verilog",
        kind="error",
        category="preprocessor",
        description_zh="宏展开后产生非法表达式。",
        top="top",
        files={"malformed_define.v": "`define BAD 4'd\nmodule top(output [3:0] y);\n  assign y = `BAD;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_preprocessor_unterminated_ifdef_003",
        language="verilog",
        kind="error",
        category="preprocessor",
        description_zh="条件编译块缺少 endif。",
        top="top",
        files={"unterminated_ifdef.v": "`ifdef USE_A\nmodule top(input a, output y);\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("endif", "directive"),
    ),
    c(
        id="verilog_preprocessor_undefined_macro_invalid_004",
        language="verilog",
        kind="error",
        category="preprocessor",
        description_zh="使用未定义宏，导致表达式非法。",
        top="top",
        files={"undefined_macro_invalid.v": "module top(output y);\n  assign y = `UNDEF_MACRO;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("macro", "syntax"),
    ),
    c(
        id="verilog_instantiation_missing_instance_name_001",
        language="verilog",
        kind="error",
        category="instantiation",
        description_zh="模块例化缺少实例名。",
        top="top",
        files={"missing_instance_name.v": "module child(input a, output y); assign y = a; endmodule\nmodule top(input a, output y);\n  child (.a(a), .y(y));\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_instantiation_bad_named_port_002",
        language="verilog",
        kind="error",
        category="instantiation",
        description_zh="命名端口连接缺少右括号。",
        top="top",
        files={"bad_named_port.v": "module child(input a, output y); assign y = a; endmodule\nmodule top(input a, output y);\n  child u (.a(a), .y(y);\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_instantiation_mixed_connection_003",
        language="verilog",
        kind="error",
        category="instantiation",
        description_zh="同一例化中混用命名连接和位置连接。",
        top="top",
        files={"mixed_connection.v": "module child(input a, input b, output y); assign y = a & b; endmodule\nmodule top(input a, input b, output y);\n  child u (.a(a), b, .y(y));\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_instantiation_unresolved_module_004",
        language="verilog",
        kind="error",
        category="instantiation",
        description_zh="例化了未定义模块。",
        top="top",
        files={"unresolved_module.v": "module top(input a, output y);\n  missing_child u (.a(a), .y(y));\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("Unknown module", "missing_child"),
    ),
    c(
        id="verilog_generate_missing_endgenerate_001",
        language="verilog",
        kind="error",
        category="generate",
        description_zh="generate 块缺少 endgenerate。",
        top="top",
        files={"missing_endgenerate.v": "module top(input a, output y);\n  generate\n    if (1) begin : g\n      assign y = a;\n    end\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax", "endgenerate"),
    ),
    c(
        id="verilog_function_missing_endfunction_001",
        language="verilog",
        kind="error",
        category="function_task",
        description_zh="function 缺少 endfunction。",
        top="top",
        files={"missing_endfunction.v": "module top(input a, output y);\n  function f;\n    input a;\n    f = a;\n  assign y = f(a);\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax", "function"),
    ),
    c(
        id="verilog_task_missing_endtask_002",
        language="verilog",
        kind="error",
        category="function_task",
        description_zh="task 缺少 endtask。",
        top="top",
        files={"missing_endtask.v": "module top(input a, output reg y);\n  task drive;\n    input a;\n    y = a;\n  always @* drive(a);\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax", "task"),
    ),
    c(
        id="verilog_specify_malformed_001",
        language="verilog",
        kind="error",
        category="specify_udp",
        description_zh="specify/specparam 语法不完整。",
        top="top",
        files={"malformed_specify.v": "module top(input a, output y);\n  specify\n    specparam tpd = ;\n  endspecify\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax",),
    ),
    c(
        id="verilog_udp_malformed_002",
        language="verilog",
        kind="error",
        category="specify_udp",
        description_zh="UDP primitive/table 构造不完整。",
        top="top",
        files={"malformed_udp.v": "primitive udp_bad(out, in);\n  output out;\n  input in;\n  table\n    0 : 0;\nendprimitive\nmodule top(input a, output y);\n  udp_bad u(y, a);\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("syntax", "table"),
    ),
    c(
        id="verilog_warning_implicit_net_001",
        language="verilog",
        kind="warning",
        category="implicit_net",
        description_zh="未声明信号导致隐式 wire。",
        top="top",
        files={"implicit_net.v": "module top(input a, output y);\n  assign y = a & typo_signal;\nendmodule\n"},
        expected_status="warning",
        expected_keywords=("implicit", "typo_signal"),
    ),
    c(
        id="verilog_warning_port_not_connected_001",
        language="verilog",
        kind="warning",
        category="port_connection",
        description_zh="子模块输入端口未连接。",
        top="top",
        files={"port_not_connected.v": "module child(input a, input b, output y); assign y = a & b; endmodule\nmodule top(input a, output y);\n  child u (.a(a), .y(y));\nendmodule\n"},
        expected_status="warning",
        expected_keywords=("dangling", "port"),
    ),
    c(
        id="verilog_warning_port_width_001",
        language="verilog",
        kind="warning",
        category="width_range",
        description_zh="模块端口连接宽度不匹配。",
        top="top",
        files={"port_width.v": "module child(input [3:0] a, output y); assign y = |a; endmodule\nmodule top(input a, output y);\n  child u(.a(a), .y(y));\nendmodule\n"},
        expected_status="warning",
        expected_keywords=("expects", "bits"),
    ),
    c(
        id="verilog_warning_select_range_001",
        language="verilog",
        kind="warning",
        category="width_range",
        description_zh="常量位选择越界。",
        top="top",
        files={"select_range.v": "module top(input [1:0] a, output y);\n  assign y = a[4];\nendmodule\n"},
        expected_status="warning",
        expected_keywords=("select", "range"),
    ),
    c(
        id="verilog_warning_timescale_001",
        language="verilog",
        kind="warning",
        category="timescale",
        description_zh="多个模块 timescale 使用不一致或缺失。",
        top="top",
        files={
            "top.v": "`timescale 1ns/1ps\nmodule top(input a, output y);\n  child u(.a(a), .y(y));\nendmodule\n",
            "child.v": "module child(input a, output y);\n  assign y = a;\nendmodule\n",
        },
        expected_status="warning",
        expected_keywords=("timescale",),
    ),
    c(
        id="verilog_warning_multi_driver_001",
        language="verilog",
        kind="warning",
        category="multiple_driver",
        description_zh="同一 wire 被多个连续赋值驱动，STA-lite 应作为风险提示。",
        top="top",
        files={"multi_driver.v": "module top(input a, input b, output y);\n  assign y = a;\n  assign y = b;\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=True,
    ),
    c(
        id="verilog_warning_latch_risk_001",
        language="verilog",
        kind="warning",
        category="latch_risk",
        description_zh="组合 always 中 if 缺少 else，存在 latch 风险。",
        top="top",
        files={"latch_risk.v": "module top(input a, input en, output reg y);\n  always @* begin\n    if (en) y = a;\n  end\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=True,
    ),
    c(
        id="verilog_warning_long_comb_001",
        language="verilog",
        kind="warning",
        category="style_timing_risk",
        description_zh="连续赋值组合表达式较长，存在早期时序风险。",
        top="top",
        files={"long_comb.v": "module top(input [7:0] a, b, c, d, output [7:0] y);\n  assign y = (((a + b) ^ (c + d)) + ((a & b) | (c & d))) ^ ((a << 1) + (b >> 1));\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=True,
    ),
    c(
        id="verilog_warning_declared_signal_unused_001",
        language="verilog",
        kind="warning",
        category="unused_unconnected",
        description_zh="声明了内部信号但从未读取或驱动。",
        top="top",
        files={"declared_signal_unused.v": "module top(input a, output y);\n  wire unused_n;\n  assign y = a;\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=True,
    ),
    c(
        id="verilog_warning_assigned_signal_not_read_002",
        language="verilog",
        kind="warning",
        category="unused_unconnected",
        description_zh="内部信号被赋值但从未被后续逻辑读取。",
        top="top",
        files={"assigned_signal_not_read.v": "module top(input a, output y);\n  wire tmp;\n  assign tmp = a;\n  assign y = a;\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=True,
    ),
    c(
        id="verilog_warning_module_input_unused_003",
        language="verilog",
        kind="warning",
        category="unused_unconnected",
        description_zh="模块输入端口声明后未被当前模块逻辑使用。",
        top="top",
        files={"module_input_unused.v": "module top(input a, input unused_in, output y);\n  assign y = a;\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=True,
    ),
    c(
        id="verilog_warning_module_output_undriven_004",
        language="verilog",
        kind="warning",
        category="unused_unconnected",
        description_zh="模块输出端口没有被连续赋值、过程赋值或子模块输出连接驱动。",
        top="top",
        files={"module_output_undriven.v": "module top(output y);\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=True,
    ),
    c(
        id="verilog_warning_instance_output_omitted_005",
        language="verilog",
        kind="warning",
        category="unused_unconnected",
        description_zh="子模块输出端口在命名例化中完全未连接。",
        top="top",
        files={"instance_output_omitted.v": "module child(input a, output out);\n  assign out = a;\nendmodule\nmodule top(input a);\n  child u(.a(a));\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=True,
    ),
    c(
        id="verilog_warning_named_output_empty_006",
        language="verilog",
        kind="warning",
        category="unused_unconnected",
        description_zh="命名端口连接使用 `.out()` 空连接，导致子模块输出悬空。",
        top="top",
        files={"named_output_empty.v": "module child(input a, output out);\n  assign out = a;\nendmodule\nmodule top(input a);\n  child u(.a(a), .out());\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=True,
    ),
    c(
        id="sv_logic_missing_semicolon_001",
        language="systemverilog",
        kind="error",
        category="declaration_type",
        description_zh="logic 声明缺少分号。",
        top="top",
        files={"logic_missing_semicolon.sv": "module top(input logic a, output logic y);\n  logic n\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("logic", "semicolon"),
    ),
    c(
        id="sv_always_comb_missing_end_001",
        language="systemverilog",
        kind="error",
        category="always_procedure",
        description_zh="always_comb 块缺少 end。",
        top="top",
        files={"always_comb_missing_end.sv": "module top(input logic a, output logic y);\n  always_comb begin\n    y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("end",),
    ),
    c(
        id="sv_always_ff_bad_event_001",
        language="systemverilog",
        kind="error",
        category="always_procedure",
        description_zh="always_ff 的 posedge 缺少信号名。",
        top="top",
        files={"always_ff_bad_event.sv": "module top(input logic clk, input logic d, output logic q);\n  always_ff @(posedge) q <= d;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("posedge",),
    ),
    c(
        id="sv_typedef_enum_unsupported_001",
        language="systemverilog",
        kind="error",
        category="enum_struct_typedef",
        description_zh="typedef enum 已进入语法级支持，旧 unsupported 回归用例现在用于确认不误报。",
        top="top",
        files={"typedef_enum.sv": "module top(input logic a, output logic y);\n  typedef enum logic [1:0] {IDLE, RUN} state_t;\n  assign y = a;\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=False,
    ),
    c(
        id="sv_struct_unsupported_001",
        language="systemverilog",
        kind="error",
        category="enum_struct_typedef",
        description_zh="typedef struct packed 已进入语法级支持，旧 unsupported 回归用例现在用于确认不误报。",
        top="top",
        files={"struct_unsupported.sv": "module top(input logic a, output logic y);\n  typedef struct packed { logic a; logic b; } pair_t;\n  assign y = a;\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=False,
    ),
    c(
        id="sv_package_import_unsupported_001",
        language="systemverilog",
        kind="error",
        category="package_import",
        description_zh="package/import 已进入语法级支持，旧 unsupported 回归用例现在用于确认不误报。",
        top="top",
        files={"package_import.sv": "package p;\n  parameter int W = 1;\nendpackage\nimport p::*;\nmodule top(input logic a, output logic y);\n  assign y = a;\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=False,
    ),
    c(
        id="sv_interface_modport_unsupported_001",
        language="systemverilog",
        kind="error",
        category="interface_modport",
        description_zh="interface/modport 已进入语法级支持，旧 unsupported 回归用例现在用于确认不误报。",
        top="top",
        files={"interface_modport.sv": "interface bus_if;\n  logic data;\n  modport master(output data);\nendinterface\nmodule top;\nendmodule\n"},
        expected_status="pass",
        expected_keywords=(),
        sta_lite_should_detect=False,
    ),
    c(
        id="sv_array_bad_dimension_001",
        language="systemverilog",
        kind="error",
        category="array_dimension",
        description_zh="unpacked array 维度范围缺少右边界。",
        top="top",
        files={"array_bad_dimension.sv": "module top(input logic a, output logic y);\n  logic [3:0] mem [3:];\n  assign y = a;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("array", "range"),
    ),
    c(
        id="sv_class_unsupported_001",
        language="systemverilog",
        kind="error",
        category="class_unsupported",
        description_zh="class 当前不属于 STA-lite RTL lint 支持子集，应明确报 UNSUPPORTED_SYSTEMVERILOG。",
        top="top",
        files={"class_unsupported.sv": "class c;\n  int x;\nendclass\nmodule top;\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("UNSUPPORTED_SYSTEMVERILOG", "class"),
    ),
    c(
        id="sv_inside_unsupported_001",
        language="systemverilog",
        kind="error",
        category="syntax",
        description_zh="inside 表达式当前不支持，应至少给出语法/unsupported 诊断。",
        top="top",
        files={"inside_unsupported.sv": "module top(input logic [1:0] a, output logic y);\n  assign y = a inside {2'b00, 2'b11};\nendmodule\n"},
        expected_status="fail",
        expected_keywords=("inside",),
    ),
    c(
        id="sv_warning_implicit_net_001",
        language="systemverilog",
        kind="warning",
        category="implicit_cast_width",
        description_zh="SV 文件中未声明标识符仍应提示隐式网线/拼写风险。",
        top="top",
        files={"implicit_net.sv": "module top(input logic a, output logic y);\n  assign y = a & typo_signal;\nendmodule\n"},
        expected_status="warning",
        expected_keywords=("implicit",),
    ),
    c(
        id="sv_warning_always_comb_latch_001",
        language="systemverilog",
        kind="warning",
        category="always_comb_latch_risk",
        description_zh="always_comb 中 if 缺少 else，存在 latch 风险。",
        top="top",
        files={"always_comb_latch.sv": "module top(input logic a, input logic en, output logic y);\n  always_comb begin\n    if (en) y = a;\n  end\nendmodule\n"},
        expected_status="warning",
        expected_keywords=("latch",),
    ),
    c(
        id="sv_warning_port_width_001",
        language="systemverilog",
        kind="warning",
        category="implicit_cast_width",
        description_zh="logic 端口连接宽度不匹配。",
        top="top",
        files={"port_width.sv": "module child(input logic [3:0] a, output logic y); assign y = |a; endmodule\nmodule top(input logic a, output logic y);\n  child u(.a(a), .y(y));\nendmodule\n"},
        expected_status="warning",
        expected_keywords=("width",),
    ),
    c(
        id="sv_warning_select_range_001",
        language="systemverilog",
        kind="warning",
        category="implicit_cast_width",
        description_zh="logic 向量常量位选择越界。",
        top="top",
        files={"select_range.sv": "module top(input logic [1:0] a, output logic y);\n  assign y = a[4];\nendmodule\n"},
        expected_status="warning",
        expected_keywords=("select", "range"),
    ),
    c(
        id="sv_warning_long_comb_001",
        language="systemverilog",
        kind="warning",
        category="style_timing_risk",
        description_zh="always_comb 中组合表达式较长，存在早期时序风险。",
        top="top",
        files={"long_comb.sv": "module top(input logic [7:0] a, b, c, d, output logic [7:0] y);\n  always_comb begin\n    y = (((a + b) ^ (c + d)) + ((a & b) | (c & d))) ^ ((a << 1) + (b >> 1));\n  end\nendmodule\n"},
        expected_status="warning",
        expected_keywords=("timing",),
    ),
]


BUILTIN_CASES.extend(
    [
        c(
            id="verilog_generate_genvar_missing_semicolon_002",
            language="verilog",
            kind="error",
            category="generate",
            description_zh="genvar 声明缺少分号，后续 generate 结构被破坏。",
            top="top",
            files={"genvar_missing_semicolon.v": "module top(input [3:0] a, output [3:0] y);\n  genvar i\n  generate\n    for (i=0; i<4; i=i+1) begin : g\n      assign y[i] = a[i];\n    end\n  endgenerate\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax", "genvar"),
        ),
        c(
            id="verilog_generate_for_missing_paren_003",
            language="verilog",
            kind="error",
            category="generate",
            description_zh="generate-for 头部括号不完整。",
            top="top",
            files={"generate_for_missing_paren.v": "module top(input [3:0] a, output [3:0] y);\n  genvar i;\n  generate\n    for (i=0; i<4; i=i+1 begin : g\n      assign y[i] = a[i];\n    end\n  endgenerate\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax", "for"),
        ),
        c(
            id="verilog_generate_if_missing_end_004",
            language="verilog",
            kind="error",
            category="generate",
            description_zh="generate-if 命名块缺少 end。",
            top="top",
            files={"generate_if_missing_end.v": "module top(input a, output y);\n  generate\n    if (1) begin : g\n      assign y = a;\n  endgenerate\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax",),
        ),
        c(
            id="verilog_generate_case_missing_endcase_005",
            language="verilog",
            kind="error",
            category="generate",
            description_zh="generate-case 缺少 endcase。",
            top="top",
            files={"generate_case_missing_endcase.v": "module top(input a, output y);\n  generate\n    case (1)\n      1: assign y = a;\n  endgenerate\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax", "case"),
        ),
        c(
            id="verilog_generate_valid_unsupported_006",
            language="verilog",
            kind="error",
            category="generate",
            description_zh="合法 generate-for 的语法级结构化支持样例。",
            top="top",
            files={"generate_valid_unsupported.v": "module top(input [1:0] a, output [1:0] y);\n  genvar i;\n  generate\n    for (i=0; i<2; i=i+1) begin : g\n      assign y[i] = a[i];\n    end\n  endgenerate\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="verilog_function_missing_name_003",
            language="verilog",
            kind="error",
            category="function_task",
            description_zh="function 声明缺少函数名。",
            top="top",
            files={"function_missing_name.v": "module top(input a, output y);\n  function ;\n    input a;\n    begin = a;\n  endfunction\n  assign y = a;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax", "function"),
        ),
        c(
            id="verilog_function_automatic_missing_end_004",
            language="verilog",
            kind="error",
            category="function_task",
            description_zh="automatic function 缺少 endfunction。",
            top="top",
            files={"automatic_function_missing_end.v": "module top(input a, output y);\n  function automatic f;\n    input a;\n    f = a;\n  assign y = f(a);\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax", "function"),
        ),
        c(
            id="verilog_function_call_missing_paren_005",
            language="verilog",
            kind="error",
            category="function_task",
            description_zh="函数调用表达式缺少右括号。",
            top="top",
            files={"function_call_missing_paren.v": "module top(input a, output y);\n  function f;\n    input a;\n    f = a;\n  endfunction\n  assign y = f(a;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax",),
        ),
        c(
            id="verilog_task_output_arg_bad_006",
            language="verilog",
            kind="error",
            category="function_task",
            description_zh="task 端口方向声明不完整。",
            top="top",
            files={"task_output_arg_bad.v": "module top(input a, output reg y);\n  task drive;\n    output;\n    y = a;\n  endtask\n  always @* drive(y);\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax", "task"),
        ),
        c(
            id="verilog_task_valid_unsupported_007",
            language="verilog",
            kind="error",
            category="function_task",
            description_zh="合法 task/endtask 的语法级结构化支持样例。",
            top="top",
            files={"task_valid_unsupported.v": "module top(input a, output reg y);\n  task drive;\n    input d;\n    begin y = d; end\n  endtask\n  always @* drive(a);\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="verilog_function_valid_call_supported_008",
            language="verilog",
            kind="error",
            category="function_task",
            description_zh="合法 function/endfunction 以及表达式中函数调用的语法级支持样例。",
            top="top",
            files={"function_valid_call_supported.v": "module top(input a, output y);\n  function f;\n    input d;\n    f = d;\n  endfunction\n  assign y = f(a);\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="verilog_specify_missing_endspecify_003",
            language="verilog",
            kind="error",
            category="specify_udp",
            description_zh="specify 块缺少 endspecify。",
            top="top",
            files={"specify_missing_endspecify.v": "module top(input a, output y);\n  specify\n    (a => y) = 1;\n  assign y = a;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax", "specify"),
        ),
        c(
            id="verilog_specify_bad_path_delay_004",
            language="verilog",
            kind="error",
            category="specify_udp",
            description_zh="specify 路径延迟表达式不完整。",
            top="top",
            files={"specify_bad_path_delay.v": "module top(input a, output y);\n  specify\n    (a => y) = ;\n  endspecify\n  assign y = a;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax",),
        ),
        c(
            id="verilog_udp_missing_table_003",
            language="verilog",
            kind="error",
            category="specify_udp",
            description_zh="UDP primitive 缺少 table。",
            top="top",
            files={"udp_missing_table.v": "primitive udp_bad(out, in);\n  output out;\n  input in;\nendprimitive\nmodule top(input a, output y);\n  udp_bad u(y, a);\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax", "table"),
        ),
        c(
            id="verilog_udp_missing_endprimitive_004",
            language="verilog",
            kind="error",
            category="specify_udp",
            description_zh="UDP primitive 缺少 endprimitive。",
            top="top",
            files={"udp_missing_endprimitive.v": "primitive udp_bad(out, in);\n  output out;\n  input in;\n  table\n    0 : 0;\n  endtable\nmodule top(input a, output y);\n  assign y = a;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax", "primitive"),
        ),
        c(
            id="verilog_preprocessor_nested_include_missing_005",
            language="verilog",
            kind="error",
            category="preprocessor",
            description_zh="嵌套 include 中引用缺失文件。",
            top="top",
            files={
                "top.v": "`include \"outer.vh\"\nmodule top(input a, output y);\n  assign y = a;\nendmodule\n",
                "outer.vh": "`include \"missing_inner.vh\"\n",
            },
            expected_status="fail",
            expected_keywords=("include", "missing"),
        ),
        c(
            id="verilog_preprocessor_nested_ifdef_missing_endif_006",
            language="verilog",
            kind="error",
            category="preprocessor",
            description_zh="嵌套条件编译缺少内层 endif。",
            top="top",
            files={"nested_ifdef_missing_endif.v": "`define A 1\n`ifdef A\n`ifdef B\nmodule top(output y);\n  assign y = 1'b0;\nendmodule\n`endif\n"},
            expected_status="fail",
            expected_keywords=("endif",),
        ),
        c(
            id="verilog_preprocessor_elsif_without_ifdef_007",
            language="verilog",
            kind="error",
            category="preprocessor",
            description_zh="`elsif 没有匹配的 `ifdef/`ifndef。",
            top="top",
            files={"elsif_without_ifdef.v": "`elsif A\nmodule top(output y);\n  assign y = 1'b0;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("elsif",),
        ),
        c(
            id="verilog_preprocessor_include_line_mapping_invalid_008",
            language="verilog",
            kind="error",
            category="preprocessor",
            description_zh="include 展开后的错误应保留被 include 文件的行列信息。",
            top="top",
            files={
                "top.v": "module top(output [3:0] y);\n  `include \"bad_expr.vh\"\nendmodule\n",
            },
            support_files={"bad_expr.vh": "assign y = 1'b;\n"},
            expected_status="fail",
            expected_keywords=("syntax",),
            include_dirs=(".",),
        ),
        c(
            id="verilog_instantiation_named_param_override_valid_005",
            language="verilog",
            kind="error",
            category="instantiation",
            description_zh="合法命名参数覆盖样例，用于确认 parser 不误报。",
            top="top",
            files={"named_param_override_valid.v": "module child #(parameter WIDTH=1)(input [WIDTH-1:0] a, output y); assign y = |a; endmodule\nmodule top(input [3:0] a, output y);\n  child #(.WIDTH(4)) u(.a(a), .y(y));\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="verilog_instantiation_ordered_param_override_valid_006",
            language="verilog",
            kind="error",
            category="instantiation",
            description_zh="合法位置参数覆盖样例，用于确认 parser 不误报。",
            top="top",
            files={"ordered_param_override_valid.v": "module child #(parameter WIDTH=1)(input [WIDTH-1:0] a, output y); assign y = |a; endmodule\nmodule top(input [3:0] a, output y);\n  child #(4) u(.a(a), .y(y));\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="verilog_expression_hierarchical_reference_bad_006",
            language="verilog",
            kind="error",
            category="expression",
            description_zh="层级引用缺少成员名。",
            top="top",
            files={"hierarchical_reference_bad.v": "module child(output y); assign y = 1'b0; endmodule\nmodule top(output y);\n  child u(.y());\n  assign y = u.;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax",),
        ),
        c(
            id="verilog_lexical_escaped_identifier_bad_003",
            language="verilog",
            kind="error",
            category="lexical",
            description_zh="转义标识符缺少空白终止，破坏赋值语法。",
            top="top",
            files={"escaped_identifier_bad.v": "module top(input a, output y);\n  wire \\bad= a;\n  assign y = \\bad ;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("syntax",),
        ),
        c(
            id="verilog_warning_blocking_seq_001",
            language="verilog",
            kind="warning",
            category="style_timing_risk",
            description_zh="时序 always 中使用阻塞赋值。",
            top="top",
            files={"blocking_seq.v": "module top(input clk, input d, output reg q);\n  always @(posedge clk) begin\n    q = d;\n  end\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=True,
        ),
        c(
            id="verilog_warning_nonblocking_comb_001",
            language="verilog",
            kind="warning",
            category="style_timing_risk",
            description_zh="组合 always 中使用非阻塞赋值。",
            top="top",
            files={"nonblocking_comb.v": "module top(input a, output reg y);\n  always @* begin\n    y <= a;\n  end\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=True,
        ),
        c(
            id="sv_package_import_wildcard_supported_002",
            language="systemverilog",
            kind="error",
            category="package_import",
            description_zh="package/endpackage 与 import pkg::* 的语法级支持样例。",
            top="top",
            files={"package_import_wildcard.sv": "package p;\n  typedef enum logic [0:0] {S0, S1} state_t;\nendpackage\nimport p::*;\nmodule top(input logic a, output logic y);\n  state_t state;\n  assign y = a;\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_package_import_named_supported_003",
            language="systemverilog",
            kind="error",
            category="package_import",
            description_zh="import pkg::name 的语法级支持样例。",
            top="top",
            files={"package_import_named.sv": "package p;\n  typedef enum logic [0:0] {S0, S1} state_t;\nendpackage\nimport p::state_t;\nmodule top(input logic a, output logic y);\n  state_t state;\n  assign y = a;\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_package_missing_endpackage_004",
            language="systemverilog",
            kind="error",
            category="package_import",
            description_zh="package 缺少 endpackage。",
            top="top",
            files={"package_missing_endpackage.sv": "package p;\n  parameter int W = 1;\nmodule top(output logic y);\n  assign y = 1'b0;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("endpackage",),
        ),
        c(
            id="sv_import_missing_scope_005",
            language="systemverilog",
            kind="error",
            category="package_import",
            description_zh="import 语句缺少 `::`。",
            top="top",
            files={"import_missing_scope.sv": "import p::*;\nmodule top(output logic y);\n  import p state_t;\n  assign y = 1'b0;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("import",),
        ),
        c(
            id="sv_package_parameter_supported_006",
            language="systemverilog",
            kind="error",
            category="package_import",
            description_zh="package 内 parameter/localparam 与命名 import 的语法级支持样例。",
            top="top",
            files={"package_parameter_supported.sv": "package p;\n  parameter int W = 4;\n  localparam int L = W;\nendpackage\nimport p::W;\nmodule top(input logic a, output logic y);\n  assign y = a;\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_typedef_enum_supported_002",
            language="systemverilog",
            kind="error",
            category="enum_struct_typedef",
            description_zh="typedef enum 的语法级支持样例。",
            top="top",
            files={"typedef_enum_supported.sv": "module top(input logic a, output logic y);\n  typedef enum logic [1:0] {IDLE, RUN} state_t;\n  state_t state;\n  assign y = a;\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_typedef_struct_supported_003",
            language="systemverilog",
            kind="error",
            category="enum_struct_typedef",
            description_zh="typedef struct packed 的语法级支持样例。",
            top="top",
            files={"typedef_struct_supported.sv": "module top(input logic a, output logic y);\n  typedef struct packed { logic a; logic b; } pair_t;\n  pair_t pair;\n  assign y = a;\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_enum_missing_brace_004",
            language="systemverilog",
            kind="error",
            category="enum_struct_typedef",
            description_zh="typedef enum 缺少右大括号。",
            top="top",
            files={"enum_missing_brace.sv": "module top(output logic y);\n  typedef enum logic [1:0] {IDLE, RUN state_t;\n  assign y = 1'b0;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("enum", "brace"),
        ),
        c(
            id="sv_typedef_missing_semicolon_005",
            language="systemverilog",
            kind="error",
            category="enum_struct_typedef",
            description_zh="typedef 声明缺少分号。",
            top="top",
            files={"typedef_missing_semicolon.sv": "module top(output logic y);\n  typedef logic [3:0] nibble_t\n  assign y = 1'b0;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("typedef", "semicolon"),
        ),
        c(
            id="sv_interface_modport_supported_002",
            language="systemverilog",
            kind="error",
            category="interface_modport",
            description_zh="interface/modport 定义和 interface 实例的语法级支持样例。",
            top="top",
            files={"interface_modport_supported.sv": "interface bus_if;\n  logic data;\n  modport master(output data);\nendinterface\nmodule top;\n  bus_if.master bus();\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_interface_missing_endinterface_003",
            language="systemverilog",
            kind="error",
            category="interface_modport",
            description_zh="interface 缺少 endinterface。",
            top="top",
            files={"interface_missing_endinterface.sv": "interface bus_if;\n  logic data;\nmodule top;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("endinterface",),
        ),
        c(
            id="sv_modport_missing_paren_004",
            language="systemverilog",
            kind="error",
            category="interface_modport",
            description_zh="modport 缺少端口列表括号。",
            top="top",
            files={"modport_missing_paren.sv": "interface bus_if;\n  logic data;\n  modport master output data;\nendinterface\nmodule top;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("modport",),
        ),
        c(
            id="sv_interface_instance_supported_005",
            language="systemverilog",
            kind="error",
            category="interface_modport",
            description_zh="无 modport 的 interface 实例语法级支持样例。",
            top="top",
            files={"interface_instance_supported.sv": "interface bus_if;\n  logic data;\nendinterface\nmodule top;\n  bus_if bus();\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_packed_unpacked_array_supported_002",
            language="systemverilog",
            kind="error",
            category="array_dimension",
            description_zh="packed 和 unpacked array 声明的语法级支持样例。",
            top="top",
            files={"packed_unpacked_array_supported.sv": "module top(input logic [3:0] a, output logic y);\n  logic signed [7:0] mem [0:3];\n  assign y = a[0];\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_array_missing_rbracket_003",
            language="systemverilog",
            kind="error",
            category="array_dimension",
            description_zh="array 维度缺少右中括号。",
            top="top",
            files={"array_missing_rbracket.sv": "module top(input logic a, output logic y);\n  logic [3:0 mem [0:3];\n  assign y = a;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("bracket",),
        ),
        c(
            id="sv_simple_cast_supported_004",
            language="systemverilog",
            kind="error",
            category="array_dimension",
            description_zh="简单 cast 语法级支持样例。",
            top="top",
            files={"simple_cast_supported.sv": "module top(input logic a, output logic y);\n  assign y = logic'(a);\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_multi_unpacked_array_supported_005",
            language="systemverilog",
            kind="error",
            category="array_dimension",
            description_zh="多维 unpacked array 声明的语法级支持样例。",
            top="top",
            files={"multi_unpacked_array_supported.sv": "module top(input logic a, output logic y);\n  logic [7:0] mem [0:3][0:1];\n  assign y = a;\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_assert_unsupported_002",
            language="systemverilog",
            kind="error",
            category="class_unsupported",
            description_zh="immediate assert 当前不做语义支持，应给出 UNSUPPORTED_SYSTEMVERILOG。",
            top="top",
            files={"assert_unsupported.sv": "module top(input logic a, output logic y);\n  always_comb begin\n    assert (a);\n    y = a;\n  end\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("UNSUPPORTED_SYSTEMVERILOG", "assert"),
        ),
        c(
            id="sv_property_unsupported_003",
            language="systemverilog",
            kind="error",
            category="class_unsupported",
            description_zh="property/endproperty 当前不做语义支持，应给出 UNSUPPORTED_SYSTEMVERILOG。",
            top="top",
            files={"property_unsupported.sv": "module top(input logic clk, output logic y);\n  property p; @(posedge clk) 1'b1; endproperty\n  assign y = 1'b0;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("UNSUPPORTED_SYSTEMVERILOG", "property"),
        ),
        c(
            id="sv_covergroup_unsupported_004",
            language="systemverilog",
            kind="error",
            category="class_unsupported",
            description_zh="covergroup 当前不做语义支持，应给出 UNSUPPORTED_SYSTEMVERILOG。",
            top="top",
            files={"covergroup_unsupported.sv": "module top(input logic clk, output logic y);\n  covergroup cg @(posedge clk); endgroup\n  assign y = 1'b0;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("UNSUPPORTED_SYSTEMVERILOG", "covergroup"),
        ),
        c(
            id="sv_class_extends_unsupported_005",
            language="systemverilog",
            kind="error",
            category="class_unsupported",
            description_zh="class extends 当前不做语义支持，应给出 UNSUPPORTED_SYSTEMVERILOG。",
            top="top",
            files={"class_extends_unsupported.sv": "class base;\nendclass\nclass derived extends base;\nendclass\nmodule top;\nendmodule\n"},
            expected_status="fail",
            expected_keywords=("UNSUPPORTED_SYSTEMVERILOG", "class"),
        ),
        c(
            id="sv_warning_enum_usage_001",
            language="systemverilog",
            kind="warning",
            category="enum_usage",
            description_zh="enum typedef 使用样例，当前只验证语法级不误报。",
            top="top",
            files={"enum_usage.sv": "module top(input logic a, output logic y);\n  typedef enum logic [0:0] {S0, S1} state_t;\n  state_t state;\n  assign y = a;\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_warning_interface_connection_001",
            language="systemverilog",
            kind="warning",
            category="interface_connection",
            description_zh="interface 实例连接样例，当前只验证语法级不误报。",
            top="top",
            files={"interface_connection.sv": "interface bus_if;\n  logic data;\nendinterface\nmodule top;\n  bus_if bus();\nendmodule\n"},
            expected_status="pass",
            expected_keywords=(),
            sta_lite_should_detect=False,
        ),
        c(
            id="sv_warning_always_ff_blocking_001",
            language="systemverilog",
            kind="warning",
            category="style_timing_risk",
            description_zh="always_ff 中使用阻塞赋值。",
            top="top",
            files={"always_ff_blocking.sv": "module top(input logic clk, input logic d, output logic q);\n  always_ff @(posedge clk) begin\n    q = d;\n  end\nendmodule\n"},
            expected_status="warning",
            expected_keywords=("blocking",),
            sta_lite_should_detect=True,
        ),
        c(
            id="sv_warning_unique_case_latch_001",
            language="systemverilog",
            kind="warning",
            category="always_comb_latch_risk",
            description_zh="unique case 缺少 default，存在组合覆盖风险。",
            top="top",
            files={"unique_case_latch.sv": "module top(input logic [1:0] a, output logic y);\n  always_comb begin\n    unique case (a)\n      2'b00: y = 1'b0;\n    endcase\n  end\nendmodule\n"},
            expected_status="warning",
            expected_keywords=("latch",),
            sta_lite_should_detect=True,
        ),
    ]
)


def write_corpus() -> None:
    for case in BUILTIN_CASES:
        case_dir = ROOT / case.root / case.category / case.id
        case_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in case.files.items():
            (case_dir / filename).write_text(content, encoding="utf-8")
        for filename, content in case.support_files.items():
            (case_dir / filename).write_text(content, encoding="utf-8")
        metadata = {
            "id": case.id,
            "language": case.language,
            "kind": case.kind,
            "category": case.category,
            "standard_focus": case.standard_focus,
            "description_zh": case.description_zh,
            "top": case.top,
            "files": list(case.files),
            "support_files": list(case.support_files),
            "expected_status": case.expected_status,
            "expected_keywords": list(case.expected_keywords),
            "include_dirs": list(case.include_dirs),
            "defines": list(case.defines),
            "sta_lite_should_detect": case.sta_lite_should_detect,
        }
        (case_dir / "case.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_case(data: dict[str, Any], case_dir: Path) -> dict[str, Any]:
    if "language" not in data:
        expected = str(data.get("expected_iverilog_status") or "fail")
        data["language"] = "verilog"
        data["kind"] = "warning" if expected == "warning" or data.get("category") == "warning_like" else "error"
        data["expected_status"] = expected
    data.setdefault("kind", "error")
    data.setdefault("expected_status", data.get("expected_iverilog_status", "fail"))
    data.setdefault("expected_keywords", [])
    data.setdefault("include_dirs", [])
    data.setdefault("defines", [])
    data.setdefault("sta_lite_should_detect", True)
    data["_case_dir"] = str(case_dir)
    data["_root"] = str(case_dir.parents[1]) if len(case_dir.parents) > 1 else str(case_dir)
    return data


def load_cases(case_roots: list[Path]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for root in case_roots:
        for case_json in sorted(root.glob("*/*/case.json")):
            data = json.loads(case_json.read_text(encoding="utf-8"))
            cases.append(normalize_case(data, case_json.parent))
    return sorted(cases, key=lambda item: (str(item.get("language")), str(item.get("kind")), str(item.get("category")), str(item.get("id"))))


def run_command(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    try:
        process = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        exit_code = process.returncode
        stdout = process.stdout
        stderr = process.stderr
    except FileNotFoundError as exc:
        exit_code = 127
        stdout = ""
        stderr = f"命令不存在：{cmd[0]} ({exc})"
    elapsed = time.monotonic() - started
    return {
        "command": cmd,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "raw_output": stdout + stderr,
        "elapsed_seconds": round(elapsed, 3),
    }


def classify_tool_result(result: dict[str, Any]) -> str:
    if int(result["exit_code"]) == 127:
        return "unavailable"
    if int(result["exit_code"]) != 0:
        return "fail"
    raw = str(result["raw_output"]).lower()
    if "warning:" in raw:
        return "warning"
    return "pass"


def classify_sta_lite(summary: dict[str, Any]) -> str:
    if int(summary.get("error_count", 0)) or int(summary.get("unsupported_count", 0)):
        return "fail"
    if int(summary.get("warning_count", 0)):
        return "warning"
    return "pass"


def status_detected(status: str) -> bool:
    return status in {"fail", "warning"}


def expected_detected_for_case(case: dict[str, Any], reference_status: str | None) -> bool:
    if bool(case.get("sta_lite_should_detect", True)):
        return True
    if case.get("language") == "verilog" and reference_status:
        return status_detected(reference_status)
    return status_detected(str(case.get("expected_status") or "pass"))


def _is_unsupported_diag(item: dict[str, Any]) -> bool:
    return str(item.get("rule") or "").startswith("UNSUPPORTED")


def sta_lite_detected_for_case(case: dict[str, Any], diagnostics: list[dict[str, Any]]) -> bool:
    if not bool(case.get("sta_lite_should_detect", True)):
        return False
    relevant = [item for item in diagnostics if str(item.get("rule") or "") not in GENERIC_STA_RULES]
    expected = str(case.get("expected_status") or "fail")
    kind = str(case.get("kind") or "error")
    if expected == "fail" or kind == "error":
        return any(str(item.get("severity") or "") == "error" or _is_unsupported_diag(item) for item in relevant)
    if expected == "warning" or kind == "warning":
        return any(str(item.get("severity") or "") in {"error", "warning"} or _is_unsupported_diag(item) for item in relevant)
    return bool(relevant)


def run_iverilog(case: dict[str, Any], case_dir: Path, iverilog_bin: str) -> dict[str, Any]:
    cmd = [iverilog_bin, "-g2005", "-Wall", "-tnull", "-s", str(case["top"])]
    for include_dir in case.get("include_dirs", []):
        cmd.extend(["-I", str(case_dir / include_dir)])
    for define in case.get("defines", []):
        cmd.append("-D" + str(define))
    cmd.extend(str(case_dir / filename) for filename in case["files"])
    env = os.environ.copy()
    tools_bin = str(ROOT / "tools" / "bin")
    env["PATH"] = tools_bin + os.pathsep + env.get("PATH", "")
    result = run_command(cmd, ROOT, env=env)
    result["status"] = classify_tool_result(result)
    return result


def run_sta_lite(case: dict[str, Any], case_dir: Path, out_dir: Path) -> dict[str, Any]:
    lint_out = out_dir / "sta_lite_runs" / str(case["id"])
    cmd = [
        sys.executable,
        str(ROOT / "sta-lite"),
        "lint",
        "--top",
        str(case["top"]),
        "--out",
        str(lint_out),
        "--fail-on",
        "never",
        "--format",
        "json",
        "--rtl",
    ]
    cmd.extend(str(case_dir / filename) for filename in case["files"])
    for include_dir in case.get("include_dirs", []):
        cmd.extend(["--include", str(case_dir / include_dir)])
    for define in case.get("defines", []):
        cmd.extend(["--define", str(define)])
    command_result = run_command(cmd, ROOT)
    try:
        summary = json.loads(command_result["stdout"])
    except json.JSONDecodeError:
        summary = {
            "error_count": 1,
            "warning_count": 0,
            "unsupported_count": 0,
            "diagnostics": [
                {
                    "rule": "LINT_RUNNER",
                    "severity": "error",
                    "message_zh": "STA-lite lint JSON 输出解析失败。",
                    "source_excerpt": command_result["stdout"][:4000],
                }
            ],
        }
    status = classify_sta_lite(summary)
    return {
        "command": cmd,
        "exit_code": command_result["exit_code"],
        "stdout": command_result["stdout"],
        "stderr": command_result["stderr"],
        "raw_output": command_result["raw_output"],
        "elapsed_seconds": command_result["elapsed_seconds"],
        "summary": summary,
        "status": status,
    }


def normalize_sta_diagnostics(summary: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics = summary.get("diagnostics", [])
    if not isinstance(diagnostics, list):
        return []
    return [
        {
            "severity": item.get("severity"),
            "rule": item.get("rule"),
            "category": item.get("category"),
            "file": item.get("file"),
            "line": item.get("line"),
            "column": item.get("column"),
            "message_zh": item.get("message_zh"),
        }
        for item in diagnostics
        if isinstance(item, dict)
    ]


def compare(cases: list[dict[str, Any]], out_dir: Path, iverilog_bin: str) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    iverilog_results: dict[str, Any] = {}
    sta_lite_results: dict[str, Any] = {}
    sv_metadata_results: dict[str, Any] = {}
    per_case: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        case_dir = Path(case["_case_dir"])
        print(f"[lint-diff] ({index}/{len(cases)}) 运行用例：{case['id']}")
        reference_status: str | None = None
        reference_output = ""
        if case.get("language") == "verilog":
            iv = run_iverilog(case, case_dir, iverilog_bin)
            reference_status = iv["status"]
            reference_output = str(iv["raw_output"])
            iverilog_results[case["id"]] = {k: v for k, v in iv.items() if k != "raw_output"}
            iverilog_results[case["id"]]["raw_output"] = iv["raw_output"]
        else:
            reference_status = str(case.get("expected_status") or "pass")
            sv_metadata_results[case["id"]] = {
                "language": case.get("language"),
                "kind": case.get("kind"),
                "category": case.get("category"),
                "expected_status": reference_status,
                "expected_keywords": case.get("expected_keywords", []),
                "reference": "metadata",
            }
        st = run_sta_lite(case, case_dir, out_dir)
        sta_lite_results[case["id"]] = {
            "command": st["command"],
            "exit_code": st["exit_code"],
            "stdout": st["stdout"],
            "stderr": st["stderr"],
            "elapsed_seconds": st["elapsed_seconds"],
            "summary": st["summary"],
            "status": st["status"],
        }
        sta_diagnostics = normalize_sta_diagnostics(st["summary"])
        sta_relevant_diagnostics = [item for item in sta_diagnostics if str(item.get("rule") or "") not in GENERIC_STA_RULES]
        expected_detected = expected_detected_for_case(case, reference_status)
        sta_detected = sta_lite_detected_for_case(case, sta_diagnostics)
        entry = {
            "id": case["id"],
            "language": case.get("language"),
            "kind": case.get("kind"),
            "category": case.get("category"),
            "description_zh": case.get("description_zh"),
            "expected_status": case.get("expected_status"),
            "reference_status": reference_status,
            "sta_lite_status": st["status"],
            "expected_detected": expected_detected,
            "sta_lite_detected": sta_detected,
            "match": expected_detected == sta_detected,
            "reference_output_excerpt": reference_output[:1200],
            "sta_lite_relevant_diagnostics": sta_relevant_diagnostics,
            "sta_lite_diagnostics": sta_diagnostics,
            "files": [str(case_dir / filename) for filename in case.get("files", [])],
        }
        per_case.append(entry)

    diff_summary = summarize(per_case)
    diff_summary["per_case"] = per_case
    verilog_iverilog_text = json.dumps(iverilog_results, ensure_ascii=False, indent=2) + "\n"
    (out_dir / "verilog_iverilog_results.json").write_text(verilog_iverilog_text, encoding="utf-8")
    (out_dir / "iverilog_results.json").write_text(verilog_iverilog_text, encoding="utf-8")
    (out_dir / "sta_lite_results.json").write_text(json.dumps(sta_lite_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "sv_metadata_results.json").write_text(json.dumps(sv_metadata_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "diff_summary.json").write_text(json.dumps(diff_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_missing_coverage(out_dir / "missing_coverage.md", diff_summary)
    coverage_matrix = build_coverage_matrix(diff_summary)
    (out_dir / "coverage_matrix.json").write_text(json.dumps(coverage_matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_coverage_matrix_md(out_dir / "coverage_matrix.md", coverage_matrix)
    return diff_summary


def summarize(per_case: list[dict[str, Any]]) -> dict[str, Any]:
    totals_by_language: dict[str, int] = {}
    totals_by_kind: dict[str, int] = {}
    totals_by_category: dict[str, int] = {}
    coverage: dict[str, Any] = {}
    for item in per_case:
        language = str(item["language"])
        kind = str(item["kind"])
        category = str(item["category"])
        totals_by_language[language] = totals_by_language.get(language, 0) + 1
        totals_by_kind[kind] = totals_by_kind.get(kind, 0) + 1
        category_key = f"{language}/{kind}/{category}"
        totals_by_category[category_key] = totals_by_category.get(category_key, 0) + 1
        bucket = coverage.setdefault(
            language,
            {},
        ).setdefault(
            kind,
            {},
        ).setdefault(
            category,
            {"total": 0, "expected_detected": 0, "sta_lite_detected": 0, "matched": 0, "missed": 0, "coverage_percent": 0.0},
        )
        bucket["total"] += 1
        bucket["expected_detected"] += int(bool(item["expected_detected"]))
        bucket["sta_lite_detected"] += int(bool(item["sta_lite_detected"]))
        bucket["matched"] += int(bool(item["match"]))
        bucket["missed"] += int(bool(item["expected_detected"] and not item["sta_lite_detected"]))
    for language_data in coverage.values():
        for kind_data in language_data.values():
            for bucket in kind_data.values():
                expected = bucket["expected_detected"]
                bucket["coverage_percent"] = round((bucket["sta_lite_detected"] / expected * 100.0) if expected else 100.0, 2)

    missed = [item for item in per_case if item["expected_detected"] and not item["sta_lite_detected"]]
    extras = [item for item in per_case if item["sta_lite_detected"] and not item["expected_detected"]]
    verilog_cases = [item for item in per_case if item["language"] == "verilog"]
    sv_cases = [item for item in per_case if item["language"] == "systemverilog"]
    return {
        "total_cases": len(per_case),
        "totals_by_language": totals_by_language,
        "totals_by_kind": totals_by_kind,
        "totals_by_language_category_kind": totals_by_category,
        "cases_expected_but_sta_lite_missed": len(missed),
        "cases_sta_lite_reported_but_not_expected": len(extras),
        "verilog_cases": len(verilog_cases),
        "verilog_reference_agree": sum(1 for item in verilog_cases if item["match"]),
        "verilog_reference_missed": sum(1 for item in verilog_cases if item["expected_detected"] and not item["sta_lite_detected"]),
        "verilog_sta_lite_extra": sum(1 for item in verilog_cases if item["sta_lite_detected"] and not item["expected_detected"]),
        "systemverilog_cases": len(sv_cases),
        "systemverilog_metadata_matched": sum(1 for item in sv_cases if item["match"]),
        "systemverilog_metadata_missed": sum(1 for item in sv_cases if item["expected_detected"] and not item["sta_lite_detected"]),
        "coverage_by_language_category_kind": coverage,
    }


def write_missing_coverage(path: Path, diff_summary: dict[str, Any]) -> None:
    missed = [
        item
        for item in diff_summary["per_case"]
        if item["expected_detected"] and not item["sta_lite_detected"]
    ]
    lines = [
        "# STA-lite Lint 缺失覆盖报告",
        "",
        f"- 总用例数：{diff_summary['total_cases']}",
        f"- 期望检出但 STA-lite 漏报：{len(missed)}",
        f"- Verilog 用例数：{diff_summary['verilog_cases']}，Verilog 漏报：{diff_summary['verilog_reference_missed']}",
        f"- SystemVerilog 用例数：{diff_summary['systemverilog_cases']}，SV 元数据漏报：{diff_summary['systemverilog_metadata_missed']}",
        "",
        "## 按 language/category/kind 统计",
        "",
    ]
    coverage = diff_summary["coverage_by_language_category_kind"]
    for language in sorted(coverage):
        for kind in sorted(coverage[language]):
            for category, stats in sorted(coverage[language][kind].items()):
                lines.append(
                    f"- `{language}/{kind}/{category}`：总数 {stats['total']}，"
                    f"期望检出 {stats['expected_detected']}，STA-lite 检出 {stats['sta_lite_detected']}，"
                    f"漏报 {stats['missed']}，覆盖率 {stats['coverage_percent']}%"
                )
    lines.extend(["", "## 漏报明细", ""])
    if not missed:
        lines.append("当前四类语料中没有发现 STA-lite 漏报。")
    for item in missed:
        lines.extend(
            [
                f"### {item['id']}",
                "",
                f"- 语言/类型/类别：`{item['language']}/{item['kind']}/{item['category']}`",
                f"- 说明：{item['description_zh']}",
                f"- 文件：{', '.join(item.get('files', []))}",
                f"- 参考/元数据期望：`{item['reference_status']}`",
                f"- STA-lite 实际状态：`{item['sta_lite_status']}`",
                "- 参考输出摘录：",
                "",
                "```text",
                item["reference_output_excerpt"].strip() or "<无外部参考输出，使用 case.json metadata>",
                "```",
                "",
                "- 建议改进：补齐该 language/category/kind 的 parser 或 rule 识别，并保持中文诊断和准确文件行列。",
                "",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


REQUIRED_MATRIX_CATEGORIES = {
    "verilog": {
        "error": [
            "lexical",
            "syntax",
            "declaration",
            "module_port",
            "expression",
            "assignment",
            "procedural_block",
            "preprocessor",
            "generate",
            "instantiation",
            "function_task",
            "specify_udp",
        ],
        "warning": [
            "implicit_net",
            "width_range",
            "port_connection",
            "timescale",
            "unused_unconnected",
            "multiple_driver",
            "latch_risk",
            "style_timing_risk",
        ],
    },
    "systemverilog": {
        "error": [
            "syntax",
            "declaration_type",
            "always_procedure",
            "package_import",
            "interface_modport",
            "enum_struct_typedef",
            "array_dimension",
            "class_unsupported",
        ],
        "warning": [
            "implicit_cast_width",
            "always_comb_latch_risk",
            "enum_usage",
            "interface_connection",
            "style_timing_risk",
        ],
    },
}


GRAMMAR_AREA_ZH = {
    "lexical": "词法/注释/字符串",
    "syntax": "基础语法",
    "declaration": "声明语法",
    "module_port": "模块和端口",
    "expression": "表达式",
    "assignment": "赋值",
    "procedural_block": "过程块",
    "preprocessor": "预处理",
    "generate": "generate",
    "instantiation": "例化/参数覆盖",
    "function_task": "function/task",
    "specify_udp": "specify/UDP",
    "implicit_net": "隐式网线",
    "width_range": "位宽/范围",
    "port_connection": "端口连接",
    "timescale": "timescale",
    "unused_unconnected": "未用/未连接",
    "multiple_driver": "多驱动",
    "latch_risk": "latch 风险",
    "style_timing_risk": "风格/时序风险",
    "declaration_type": "SV 类型声明",
    "always_procedure": "SV always 过程块",
    "package_import": "SV package/import",
    "interface_modport": "SV interface/modport",
    "enum_struct_typedef": "SV typedef/enum/struct",
    "array_dimension": "SV 数组/类型",
    "class_unsupported": "SV 非 RTL 构造",
    "implicit_cast_width": "SV 隐式/位宽",
    "always_comb_latch_risk": "SV always_comb 风险",
    "enum_usage": "SV enum 使用",
    "interface_connection": "SV interface 连接",
}


NEXT_IMPROVEMENT_ZH = {
    "verilog/error/generate": "逐步实现 generate-for/if/case AST，而不是仅依赖 unsupported 诊断。",
    "verilog/error/function_task": "补齐 function/task 端口、作用域和调用点 AST。",
    "verilog/error/specify_udp": "将 specify/UDP 从显式 unsupported 推进到结构化识别。",
    "verilog/error/preprocessor": "继续增加嵌套 include 与条件编译的行列映射回归。",
    "verilog/warning/unused_unconnected": "继续补充跨模块输出扇出、generate 内部未用信号和参数化例化相关用例。",
    "systemverilog/error/package_import": "补齐 package 符号表和 import 解析结果的跨模块可见性。",
    "systemverilog/error/interface_modport": "补齐 interface/modport elaboration 与端口方向检查。",
    "systemverilog/error/enum_struct_typedef": "补齐 typedef/enum/struct 类型系统和字段访问检查。",
    "systemverilog/error/class_unsupported": "继续保持 class/assertion/covergroup 精确 unsupported，暂不做语义支持。",
    "systemverilog/warning/enum_usage": "增加 enum 覆盖率、非法状态和默认分支相关 warning。",
    "systemverilog/warning/interface_connection": "增加 interface 实例连接、modport 方向和未连接信号 warning。",
}


def build_coverage_matrix(diff_summary: dict[str, Any]) -> dict[str, Any]:
    per_case = diff_summary.get("per_case", [])
    rows: list[dict[str, Any]] = []
    coverage = diff_summary.get("coverage_by_language_category_kind", {})
    for language, kind_map in REQUIRED_MATRIX_CATEGORIES.items():
        for kind, categories in kind_map.items():
            for category in categories:
                stats = coverage.get(language, {}).get(kind, {}).get(
                    category,
                    {"total": 0, "expected_detected": 0, "sta_lite_detected": 0, "matched": 0, "missed": 0, "coverage_percent": 0.0},
                )
                category_cases = [
                    item for item in per_case
                    if item.get("language") == language and item.get("kind") == kind and item.get("category") == category
                ]
                support_status = _support_status_for_category(stats, category_cases)
                key = f"{language}/{kind}/{category}"
                rows.append(
                    {
                        "language": language,
                        "kind": kind,
                        "grammar_area": GRAMMAR_AREA_ZH.get(category, category),
                        "category": category,
                        "case_count": stats["total"],
                        "sta_lite_result": _status_summary([str(item.get("sta_lite_status")) for item in category_cases]),
                        "reference_result": _status_summary([str(item.get("reference_status")) for item in category_cases]),
                        "expected_detected": stats["expected_detected"],
                        "sta_lite_detected": stats["sta_lite_detected"],
                        "missed": stats["missed"],
                        "coverage_percent": stats["coverage_percent"],
                        "support_status": support_status,
                        "next_recommended_improvement": _next_improvement(key, support_status),
                    }
                )
    return {
        "generated_by": "sta_lite_lint_diff",
        "total_cases": diff_summary.get("total_cases", 0),
        "baseline_74_zero_miss_preserved": diff_summary.get("cases_expected_but_sta_lite_missed", 0) == 0 and diff_summary.get("total_cases", 0) >= 74,
        "rows": rows,
    }


def _support_status_for_category(stats: dict[str, Any], category_cases: list[dict[str, Any]]) -> str:
    total = int(stats.get("total", 0))
    if total == 0:
        return "not_covered"
    if int(stats.get("missed", 0)) > 0:
        return "partially_supported"
    relevant = []
    for item in category_cases:
        relevant.extend(item.get("sta_lite_relevant_diagnostics") or [])
    if any(str(diag.get("rule") or "").startswith("UNSUPPORTED") for diag in relevant):
        return "unsupported_diagnostic"
    return "supported"


def _status_summary(statuses: list[str]) -> str:
    if not statuses:
        return "无用例"
    counts: dict[str, int] = {}
    for status in statuses:
        counts[status] = counts.get(status, 0) + 1
    return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))


def _next_improvement(key: str, support_status: str) -> str:
    if support_status == "not_covered":
        return "新增最小可复现语料，并接入差分回归。"
    if support_status == "partially_supported":
        return "优先修复当前漏报 case 对应的 parser/rule 能力。"
    return NEXT_IMPROVEMENT_ZH.get(key, "保持当前覆盖，继续补充真实项目中的最小复现。")


def write_coverage_matrix_md(path: Path, coverage_matrix: dict[str, Any]) -> None:
    lines = [
        "# STA-lite Lint 覆盖矩阵",
        "",
        f"- 总用例数：{coverage_matrix['total_cases']}",
        f"- 74-case 零漏报基线保持：{'是' if coverage_matrix['baseline_74_zero_miss_preserved'] else '否'}",
        "",
        "| 语言 | 类型 | 语法区域 | 类别 | 用例数 | STA-lite 结果 | 参考/元数据结果 | 覆盖率 | 支持状态 | 下一步建议 |",
        "|---|---|---|---|---:|---|---|---:|---|---|",
    ]
    for row in coverage_matrix["rows"]:
        lines.append(
            "| "
            f"{row['language']} | {row['kind']} | {row['grammar_area']} | `{row['category']}` | "
            f"{row['case_count']} | {row['sta_lite_result']} | {row['reference_result']} | "
            f"{row['coverage_percent']}% | `{row['support_status']}` | {row['next_recommended_improvement']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_case_roots(values: list[str] | None) -> list[Path]:
    roots = values or DEFAULT_CORPUS_ROOTS
    return [(ROOT / value).resolve() for value in roots]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 STA-lite lint、Verilog iverilog golden 和 SV metadata 差分回归")
    parser.add_argument("--cases", nargs="*", default=None, help="语料根目录；不指定时扫描四个 canonical root")
    parser.add_argument("--out", default="reports/lint_diff", help="差分报告输出目录")
    parser.add_argument("--iverilog", default="iverilog", help="iverilog 命令名或路径")
    parser.add_argument("--write-corpus", action="store_true", help="先生成/刷新内置四类语料")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.write_corpus:
        write_corpus()
        print("[lint-diff] 已生成四类 lint 语料。")
    case_roots = resolve_case_roots(args.cases)
    cases = load_cases(case_roots)
    if not cases:
        roots_text = ", ".join(str(root) for root in case_roots)
        raise SystemExit(f"没有找到 case.json：{roots_text}")
    summary = compare(cases, (ROOT / args.out).resolve(), args.iverilog)
    print(
        "[lint-diff] 完成："
        f"总数 {summary['total_cases']}，"
        f"期望检出但 STA-lite 漏报 {summary['cases_expected_but_sta_lite_missed']}。"
    )
    print(f"[lint-diff] 报告目录：{(ROOT / args.out).resolve()}")
    return 1 if int(summary["cases_expected_but_sta_lite_missed"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
