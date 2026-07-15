from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "long_task_golden" / "golden_results.json"


def run_optional(command: list[str]) -> dict[str, object]:
    executable = shutil.which(command[0])
    if not executable and command[0] == "verilator":
        workspace_verilator = ROOT / "tools" / "verilator" / "usr" / "bin" / "verilator"
        executable = str(workspace_verilator) if workspace_verilator.is_file() else None
    if not executable:
        return {"status": "skipped", "message_zh": f"未安装可选开发期工具 {command[0]}，已使用 case.json 正负例作为可复现 reference。"}
    result = subprocess.run([executable, *command[1:]], cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)
    version_args = ["-V"] if command[0] == "yosys" else ["--version"]
    version = subprocess.run([executable, *version_args], cwd=ROOT, text=True, capture_output=True, check=False, timeout=10)
    return {
        "status": "passed" if result.returncode == 0 else "observed_diagnostic",
        "returncode": result.returncode,
        "command": command,
        "executable": executable,
        "version_excerpt": (version.stdout + version.stderr).splitlines()[0] if (version.stdout + version.stderr).splitlines() else "未知版本",
        "output_excerpt": (result.stdout + result.stderr)[-2000:],
        "message_zh": "可选外部工具已完成开发期观察；结果不参与生产运行。",
    }


def main() -> int:
    metadata_cases = [
        "ram_inference_async_read",
        "ram_vector_safe",
        "dsp_inference_mac",
        "dsp_no_multiply_safe",
        "missing_pipeline_compare_mux",
        "pipeline_registered_safe",
        "high_fanout_clock_enable",
        "clock_enable_small_safe",
        "async_data_control_event",
        "async_reset_control_safe",
    ]
    metadata = {}
    for name in metadata_cases:
        path = ROOT / "risk_profile" / "cases" / name / "case.json"
        item = json.loads(path.read_text(encoding="utf-8"))
        if "expected_risks" not in item and "forbidden_risks" not in item:
            raise SystemExit(f"{path} 缺少 expected_risks/forbidden_risks reference。")
        metadata[name] = {"status": "passed", "reference": str(path.relative_to(ROOT))}

    yosys_ram = run_optional(["yosys", "-q", "-p", "read_verilog risk_profile/cases/ram_inference_async_read/ram_inference_async_read.v; hierarchy -top top; proc; memory_dff; memory_collect; stat"])
    yosys_dsp = run_optional(["yosys", "-q", "-p", "read_verilog risk_profile/cases/dsp_inference_mac/dsp_inference_mac.v; hierarchy -top top; proc; alumacc; stat"])
    yosys_generate = run_optional(["yosys", "-q", "-p", "read_verilog lint/verilog_warning_example/generate_elaboration/verilog_warning_complex_generate_001/complex_generate.v; hierarchy -top top; proc; check"])
    yosys_synthesizability = run_optional(["yosys", "-q", "-p", "read_verilog lint/verilog_warning_example/synthesizability/verilog_warning_simulation_constructs_001/simulation_constructs.v; hierarchy -top top; proc; check"])
    verilator = run_optional(["verilator", "--lint-only", "--Wall", "lint/verilog_warning_example/parameter_width/verilog_warning_parameter_width_001/parameter_width.v"])
    payload = {
        "purpose_zh": "仅用于测试/开发期的可选 golden/reference，不是生产 lint/risk 依赖。",
        "metadata_reference": metadata,
        "reference_sources": {
            "yosys_memory": "https://yosyshq.readthedocs.io/projects/yosys/en/v0.56/using_yosys/synthesis/memory.html",
            "yosys_dsp": "https://yosyshq.readthedocs.io/projects/yosys/en/v0.51/cmd/xilinx_dsp.html",
            "verilator_warnings": "https://verilator.org/guide/latest/warnings.html",
            "installation_zh": "Yosys 可由系统包安装；Verilator 可由系统包安装，或使用本仓库 tools/verilator 的已解包开发期副本。二者均非生产依赖。",
        },
        "optional_tools": {
            "yosys_ram": yosys_ram,
            "yosys_dsp": yosys_dsp,
            "yosys_generate": yosys_generate,
            "yosys_synthesizability": yosys_synthesizability,
            "verilator_parameter_width": verilator,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[test_long_task_golden_reference] metadata reference 通过；可选工具结果已写入 {OUT}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
