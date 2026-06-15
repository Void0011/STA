# Project Goal

## Vision

Build an STA-lite tool that is different from traditional signoff STA products.

The first product direction is not to replace PrimeTime, Tempus, Vivado Timing Analyzer, or other signoff-grade tools. Instead, this tool should help RTL/FPGA/IC developers discover timing-related risks earlier, understand backend violations faster, and reduce repeated synthesis/place-route/debug cycles.

## Business Logic

The system should serve three major workflows.

### 1. GUI-Centered Local STA Flow

The tool should eventually provide a GUI that can run a local flow:

```text
Verilog/SystemVerilog RTL
  -> standalone lint/risk checks
  -> Yosys synthesis
  -> OpenSTA timing report
  -> parsed result
  -> GUI display
```

The GUI should make the flow observable:

- show live compile/synthesis/STA logs
- show elapsed time during analysis
- show final WNS/TNS/risk summary
- show timing violations in a dedicated area or window

### 2. RTL-Stage Risk Inspection

At the RTL design stage, the tool should perform basic checks before expensive backend runs. This lint/risk stage is a product capability of STA-lite itself, not just a wrapper around external EDA tools:

- common lint checks
- Verilog syntax and compile-time issue detection, with regression coverage moving toward practical IEEE 1364 compliance
- SystemVerilog syntax-check coverage for common RTL/frontend constructs
- long combinational logic risk
- latch inference risk
- high-fanout control signal risk
- reset/clock usage risk hints
- constraint-file consistency checks
- missing or suspicious clock constraints

During development, external tools such as `iverilog` may be used as Verilog regression goldens to measure coverage. They should not become the production lint engine. SystemVerilog cases may use metadata expectations or optional reference adapters. Yosys/OpenSTA belong to the later synthesis/STA flow, not the standalone lint frontend.

### 3. Backend Report Reverse Location

At the backend synthesis/place-route/STA stage, the tool should parse reports and help locate violations back to RTL source context.

The long-term goal is:

```text
backend violation report -> netlist path -> module/register/signal mapping -> RTL file/location -> reviewable optimization suggestion
```

The MVP only needs a practical first step:

- parse Yosys/OpenSTA logs and reports
- extract startpoint, endpoint, slack, path group, and warnings
- preserve enough names and files to support future RTL backtracking

## System Positioning

This tool is an early-risk and debug-assistance platform, not a golden timing signoff tool.

It should prioritize:

- reproducibility
- clear GUI visibility
- Chinese engineering diagnostics
- report parsing and structured summaries
- clean integration boundaries
- future extensibility toward RTL source mapping

It should not prioritize in the first version:

- real FPGA physical interconnect delay modeling
- placement/routing estimation
- ML timing prediction
- advanced MCMM or signoff variation models
- full PrimeTime command compatibility
