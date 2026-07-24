from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "board_replay" / "microblaze_template"
WORK = REPO.parent / "_snn_ecg_microblaze_template_work"
VIVADO = Path(r"C:\Xilinx\Vivado\2020.2\bin\vivado.bat")
PART = "xc7a100tcsg324-1"

SNN_BASE = 0x44A0_0000
FEEDER_BASE = 0x44A1_0000
UART_BASE = 0x4060_0000
INTC_BASE = 0x4120_0000


def slash(path: Path) -> str:
    return str(path).replace("\\", "/")


def run(cmd: list[str], cwd: Path, log: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed {proc.returncode}: {' '.join(cmd)}; see {log}")


def ensure_packaged_ips(skip_package: bool) -> None:
    if skip_package:
        return
    run([sys.executable, str(REPO / "scripts" / "package_sample_feeder_ip.py")], REPO, RESULTS / "package_sample_feeder_ip.log")
    run([sys.executable, str(REPO / "scripts" / "package_snn_ecg_axi_ip.py")], REPO, RESULTS / "package_snn_ecg_axi_ip.log")


def write_tcl(no_bitstream: bool) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    tcl = RESULTS / "build_microblaze_template_system.tcl"
    build_to = "route_design" if no_bitstream else "write_bitstream"
    bitstream_block = "" if no_bitstream else """
set bit_file "$proj_dir/SNN_ECG_MB_TEMPLATE.runs/impl_1/snn_ecg_mb_template_wrapper.bit"
if {![file exists $bit_file]} {
    error "Bitstream not found: $bit_file"
}
file copy -force $bit_file "$out_dir/snn_ecg_mb_template.bit"
"""
    tcl.write_text(
        f"""set repo_dir "{slash(REPO)}"
set work_dir "{slash(WORK)}"
set out_dir "{slash(RESULTS)}"
set proj_dir "$work_dir/project"
set bd_name "snn_ecg_mb_template"
file mkdir $out_dir
file mkdir "$out_dir/reports"

create_project -force SNN_ECG_MB_TEMPLATE $proj_dir -part {PART}
set_property target_language Verilog [current_project]
set_property ip_repo_paths [list "$repo_dir/ip_repo"] [current_project]
update_ip_catalog

create_bd_design $bd_name

create_bd_port -dir I -type clk -freq_hz 100000000 CLK100MHZ
create_bd_port -dir I -type rst CPU_RESETN
set_property CONFIG.POLARITY ACTIVE_LOW [get_bd_ports CPU_RESETN]
create_bd_port -dir I UART_TXD_IN
create_bd_port -dir O UART_RXD_OUT

create_bd_cell -type ip -vlnv xilinx.com:ip:microblaze:* microblaze_0
set_property -dict [list \\
    CONFIG.C_USE_INTERRUPT {{1}} \\
    CONFIG.C_DEBUG_ENABLED {{1}} \\
    CONFIG.C_USE_BARREL {{1}} \\
    CONFIG.C_USE_DIV {{1}} \\
    CONFIG.C_USE_HW_MUL {{1}} \\
    CONFIG.C_USE_ICACHE {{0}} \\
    CONFIG.C_USE_DCACHE {{0}} \\
] [get_bd_cells microblaze_0]

apply_bd_automation -rule xilinx.com:bd_rule:microblaze -config [list \\
    local_mem {{64KB}} \\
    ecc {{None}} \\
    cache {{None}} \\
    debug_module {{Debug Only}} \\
    axi_periph {{Enabled}} \\
    axi_intc {{0}} \\
    clk {{/CLK100MHZ (100 MHz)}} \\
    rst {{/CPU_RESETN}} \\
] [get_bd_cells microblaze_0]

create_bd_cell -type ip -vlnv user.org:user:snn_ecg_axi_accelerator:1.0 snn_ecg_axi_accelerator_0
set_property -dict [list \\
    CONFIG.SNAPSHOT_SAMPLES {{8}} \\
    CONFIG.SNAPSHOTS_PER_CHUNK {{2}} \\
    CONFIG.POST_DONE_TICKS {{37}} \\
    CONFIG.PROFILE_EN {{1}} \\
    CONFIG.TLAST_CHECK_EN {{1}} \\
] [get_bd_cells snn_ecg_axi_accelerator_0]

create_bd_cell -type ip -vlnv user.org:user:axi_lite_axis_sample_feeder:1.0 sample_feeder_0
set_property -dict [list \\
    CONFIG.M_AXIS_TDATA_WIDTH {{16}} \\
    CONFIG.FIFO_DEPTH {{16}} \\
    CONFIG.FIFO_ADDR_WIDTH {{4}} \\
] [get_bd_cells sample_feeder_0]

create_bd_cell -type ip -vlnv xilinx.com:ip:axi_uartlite:* axi_uartlite_0
set_property -dict [list CONFIG.C_BAUDRATE {{115200}} CONFIG.C_DATA_BITS {{8}} CONFIG.C_USE_PARITY {{0}}] [get_bd_cells axi_uartlite_0]

create_bd_cell -type ip -vlnv xilinx.com:ip:axi_intc:* axi_intc_0
set_property -dict [list CONFIG.C_KIND_OF_INTR {{0x00000000}} CONFIG.C_IRQ_CONNECTION {{1}}] [get_bd_cells axi_intc_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:* xlconcat_0
set_property CONFIG.NUM_PORTS {{1}} [get_bd_cells xlconcat_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:* axi_interconnect_0
set_property -dict [list CONFIG.NUM_MI {{4}} CONFIG.NUM_SI {{1}}] [get_bd_cells axi_interconnect_0]

connect_bd_intf_net [get_bd_intf_pins sample_feeder_0/m_axis] [get_bd_intf_pins snn_ecg_axi_accelerator_0/s_axis]
connect_bd_net [get_bd_ports UART_TXD_IN] [get_bd_pins axi_uartlite_0/rx]
connect_bd_net [get_bd_pins axi_uartlite_0/tx] [get_bd_ports UART_RXD_OUT]
connect_bd_net [get_bd_pins snn_ecg_axi_accelerator_0/irq] [get_bd_pins xlconcat_0/In0]
connect_bd_net [get_bd_pins xlconcat_0/dout] [get_bd_pins axi_intc_0/intr]
connect_bd_net [get_bd_pins axi_intc_0/irq] [get_bd_pins microblaze_0/Interrupt]

set rst_cells [get_bd_cells -quiet -hier -filter {{VLNV =~ "xilinx.com:ip:proc_sys_reset:*"}}]
if {{[llength $rst_cells] == 0}} {{
    error "No proc_sys_reset cell found after MicroBlaze automation"
}}
set rst_cell [lindex $rst_cells 0]
set resetn_pin [get_bd_pins $rst_cell/peripheral_aresetn]
if {{[llength [get_bd_nets -quiet -of_objects [get_bd_pins $rst_cell/ext_reset_in]]] == 0}} {{
    connect_bd_net [get_bd_ports CPU_RESETN] [get_bd_pins $rst_cell/ext_reset_in]
}}

connect_bd_intf_net [get_bd_intf_pins microblaze_0/M_AXI_DP] [get_bd_intf_pins axi_interconnect_0/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M00_AXI] [get_bd_intf_pins snn_ecg_axi_accelerator_0/s_axi]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M01_AXI] [get_bd_intf_pins sample_feeder_0/s_axi]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M02_AXI] [get_bd_intf_pins axi_uartlite_0/S_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M03_AXI] [get_bd_intf_pins axi_intc_0/s_axi]

foreach pin [list \\
    [get_bd_pins axi_interconnect_0/ACLK] \\
    [get_bd_pins axi_interconnect_0/S00_ACLK] \\
    [get_bd_pins axi_interconnect_0/M00_ACLK] \\
    [get_bd_pins axi_interconnect_0/M01_ACLK] \\
    [get_bd_pins axi_interconnect_0/M02_ACLK] \\
    [get_bd_pins axi_interconnect_0/M03_ACLK] \\
    [get_bd_pins snn_ecg_axi_accelerator_0/s_axi_aclk] \\
    [get_bd_pins sample_feeder_0/s_axi_aclk] \\
    [get_bd_pins axi_uartlite_0/s_axi_aclk] \\
    [get_bd_pins axi_intc_0/s_axi_aclk] \\
] {{
    if {{[llength [get_bd_nets -quiet -of_objects $pin]] == 0}} {{
        connect_bd_net [get_bd_ports CLK100MHZ] $pin
    }}
}}

foreach pin [list \\
    [get_bd_pins axi_interconnect_0/ARESETN] \\
    [get_bd_pins axi_interconnect_0/S00_ARESETN] \\
    [get_bd_pins axi_interconnect_0/M00_ARESETN] \\
    [get_bd_pins axi_interconnect_0/M01_ARESETN] \\
    [get_bd_pins axi_interconnect_0/M02_ARESETN] \\
    [get_bd_pins axi_interconnect_0/M03_ARESETN] \\
    [get_bd_pins snn_ecg_axi_accelerator_0/s_axi_aresetn] \\
    [get_bd_pins sample_feeder_0/s_axi_aresetn] \\
    [get_bd_pins axi_uartlite_0/s_axi_aresetn] \\
    [get_bd_pins axi_intc_0/s_axi_aresetn] \\
] {{
    if {{[llength [get_bd_nets -quiet -of_objects $pin]] == 0}} {{
        connect_bd_net $resetn_pin $pin
    }}
}}

set mb_data_space [get_bd_addr_spaces microblaze_0/Data]
assign_bd_address -target_address_space $mb_data_space -offset 0x{SNN_BASE:08x} -range 4K [get_bd_addr_segs snn_ecg_axi_accelerator_0/s_axi/reg0]
assign_bd_address -target_address_space $mb_data_space -offset 0x{FEEDER_BASE:08x} -range 4K [get_bd_addr_segs sample_feeder_0/s_axi/reg0]
assign_bd_address -target_address_space $mb_data_space -offset 0x{UART_BASE:08x} -range 4K [get_bd_addr_segs axi_uartlite_0/S_AXI/Reg]
assign_bd_address -target_address_space $mb_data_space -offset 0x{INTC_BASE:08x} -range 4K [get_bd_addr_segs axi_intc_0/S_AXI/Reg]

validate_bd_design
save_bd_design
write_bd_tcl -force "$out_dir/snn_ecg_mb_template_bd.tcl"
set addr_fh [open "$out_dir/reports/system_bd_address.rpt" w]
puts $addr_fh "Long-window ECG 4-Class Accelerator MicroBlaze template address map"
puts $addr_fh "snn_ecg_axi_accelerator_0/s_axi/reg0 0x{SNN_BASE:08x} 4K"
puts $addr_fh "sample_feeder_0/s_axi/reg0          0x{FEEDER_BASE:08x} 4K"
puts $addr_fh "axi_uartlite_0/S_AXI/Reg            0x{UART_BASE:08x} 4K"
puts $addr_fh "axi_intc_0/S_AXI/Reg                0x{INTC_BASE:08x} 4K"
close $addr_fh

make_wrapper -files [get_files "$proj_dir/SNN_ECG_MB_TEMPLATE.srcs/sources_1/bd/$bd_name/$bd_name.bd"] -top
add_files -norecurse "$proj_dir/SNN_ECG_MB_TEMPLATE.gen/sources_1/bd/$bd_name/hdl/${{bd_name}}_wrapper.v"
set_property top snn_ecg_mb_template_wrapper [current_fileset]
update_compile_order -fileset sources_1

add_files -fileset constrs_1 [list "$repo_dir/constraints/nexys_a7_microblaze_template.xdc"]

generate_target all [get_files "$proj_dir/SNN_ECG_MB_TEMPLATE.srcs/sources_1/bd/$bd_name/$bd_name.bd"]
export_ip_user_files -of_objects [get_files "$proj_dir/SNN_ECG_MB_TEMPLATE.srcs/sources_1/bd/$bd_name/$bd_name.bd"] -no_script -sync -force -quiet

set_property strategy Flow_PerfOptimized_high [get_runs synth_1]
set_property strategy Performance_Explore [get_runs impl_1]
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
set_property STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE AggressiveExplore [get_runs impl_1]

launch_runs synth_1 -jobs 4
wait_on_run synth_1
if {{[get_property STATUS [get_runs synth_1]] != "synth_design Complete!"}} {{
    error "synth_1 failed: [get_property STATUS [get_runs synth_1]]"
}}

launch_runs impl_1 -to_step {build_to} -jobs 4
wait_on_run impl_1
if {{[get_property PROGRESS [get_runs impl_1]] != "100%"}} {{
    error "impl_1 did not complete: [get_property STATUS [get_runs impl_1]]"
}}
open_run impl_1
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 50 -file "$out_dir/reports/system_timing_summary.rpt"
report_cdc -details -file "$out_dir/reports/system_cdc.rpt"
report_clock_interaction -file "$out_dir/reports/system_clock_interaction.rpt"
report_methodology -file "$out_dir/reports/system_methodology.rpt"
report_drc -file "$out_dir/reports/system_drc.rpt"
report_io -file "$out_dir/reports/system_io.rpt"
report_route_status -file "$out_dir/reports/system_route_status.rpt"
report_utilization -file "$out_dir/reports/system_utilization.rpt"
report_utilization -hierarchical -file "$out_dir/reports/system_utilization_hier.rpt"
write_checkpoint -force "$out_dir/reports/system_routed.dcp"
report_ip_status -file "$out_dir/reports/system_ip_status.rpt"
{bitstream_block}
if {{![catch {{write_hw_platform -fixed -include_bit -force -file "$out_dir/snn_ecg_mb_template.xsa"}} msg]}} {{
    puts "XSA=$out_dir/snn_ecg_mb_template.xsa"
}} else {{
    puts "WARN write_hw_platform failed: $msg"
}}
exit
""",
        encoding="utf-8",
        newline="\n",
    )
    return tcl


def parse_timing(path: Path) -> dict[str, float | int | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, float | int | None] = {
        "setup_worst_slack_ns": None,
        "setup_total_violation_ns": None,
        "setup_failing_endpoints": None,
        "hold_worst_slack_ns": None,
        "hold_total_violation_ns": None,
        "hold_failing_endpoints": None,
    }
    start = text.find("| Design Timing Summary")
    end = text.find("| Clock Summary", start)
    if start >= 0 and end > start:
        section = text[start:end]
        for line in section.splitlines():
            values = re.findall(r"[-+]?[0-9]+(?:\.[0-9]+)?", line)
            if len(values) >= 8 and "." in values[0]:
                out["setup_worst_slack_ns"] = float(values[0])
                out["setup_total_violation_ns"] = float(values[1])
                out["setup_failing_endpoints"] = int(values[2])
                out["hold_worst_slack_ns"] = float(values[4])
                out["hold_total_violation_ns"] = float(values[5])
                out["hold_failing_endpoints"] = int(values[6])
                break
    return out


def parse_util(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, str] = {}
    for key, pattern in {
        "slice_lut": r"\|\s*Slice LUTs\s*\|\s*([0-9]+)",
        "slice_reg": r"\|\s*Slice Registers\s*\|\s*([0-9]+)",
        "ff": r"\|\s*Register as Flip Flop\s*\|\s*([0-9]+)",
        "bram_tile": r"\|\s*Block RAM Tile\s*\|\s*([0-9.]+)",
        "dsp": r"\|\s*DSPs\s*\|\s*([0-9]+)",
    }.items():
        match = re.search(pattern, text)
        if match:
            out[key] = match.group(1)
    return out


def write_summary(no_bitstream: bool) -> None:
    reports = RESULTS / "reports"
    timing_path = reports / "system_timing_summary.rpt"
    util_path = reports / "system_utilization.rpt"
    cdc_path = reports / "system_cdc.rpt"
    check_timing_clean = False
    cdc_clean = False
    if timing_path.exists():
        text = timing_path.read_text(encoding="utf-8", errors="replace")
        check_timing_clean = all(
            marker in text
            for marker in [
                "checking no_clock (0)",
                "checking unconstrained_internal_endpoints (0)",
                "There are 0 input ports with no input delay specified.",
                "There are 0 ports with no output delay specified.",
                "checking partial_input_delay (0)",
                "checking partial_output_delay (0)",
            ]
        )
    if cdc_path.exists():
        cdc_text = cdc_path.read_text(encoding="utf-8", errors="replace")
        cdc_clean = not re.search(r"\b(Critical|Warning)\b", cdc_text)
    timing_text = timing_path.read_text(encoding="utf-8", errors="replace") if timing_path.exists() else ""
    summary = {
        "top": "snn_ecg_mb_template_wrapper",
        "part": PART,
        "template_parameters": {
            "snapshot_samples": 8,
            "snapshots_per_chunk": 2,
            "total_samples": 16,
            "tlast_check_en": 1,
            "profile_en": 1,
        },
        "addresses": {
            "snn_ecg_axi_accelerator": f"0x{SNN_BASE:08x}",
            "sample_feeder": f"0x{FEEDER_BASE:08x}",
            "axi_uartlite": f"0x{UART_BASE:08x}",
            "axi_intc": f"0x{INTC_BASE:08x}",
        },
        "bitstream": str(RESULTS / "snn_ecg_mb_template.bit"),
        "bitstream_exists": (RESULTS / "snn_ecg_mb_template.bit").exists() if not no_bitstream else False,
        "xsa": str(RESULTS / "snn_ecg_mb_template.xsa"),
        "xsa_exists": (RESULTS / "snn_ecg_mb_template.xsa").exists(),
        "timing_constraints_met": timing_path.exists() and (
            "Timing constraints are met." in timing_text or
            "All user specified timing constraints are met." in timing_text
        ),
        "timing": parse_timing(timing_path) if timing_path.exists() else {},
        "check_timing_clean_markers": check_timing_clean,
        "cdc_clean_markers": cdc_clean,
        "utilization": parse_util(util_path) if util_path.exists() else {},
        "reports": {
            "timing": str(timing_path),
            "cdc": str(cdc_path),
            "clock_interaction": str(reports / "system_clock_interaction.rpt"),
            "drc": str(reports / "system_drc.rpt"),
            "io": str(reports / "system_io.rpt"),
            "route_status": str(reports / "system_route_status.rpt"),
            "utilization": str(util_path),
            "utilization_hier": str(reports / "system_utilization_hier.rpt"),
            "bd_address": str(reports / "system_bd_address.rpt"),
            "ip_status": str(reports / "system_ip_status.rpt"),
        },
    }
    (RESULTS / "microblaze_template_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the MicroBlaze long-window ECG 4-class accelerator packaged-IP template system.")
    parser.add_argument("--skip-package", action="store_true", help="Do not regenerate local packaged IPs first.")
    parser.add_argument("--no-bitstream", action="store_true", help="Stop at routed implementation reports without writing a bitstream.")
    parser.add_argument("--keep-work", action="store_true", help="Keep the previous external Vivado work directory.")
    args = parser.parse_args()

    if not VIVADO.exists():
        raise FileNotFoundError(f"Vivado not found: {VIVADO}")
    if WORK.exists() and not args.keep_work:
        shutil.rmtree(WORK)
    RESULTS.mkdir(parents=True, exist_ok=True)
    ensure_packaged_ips(args.skip_package)
    tcl = write_tcl(args.no_bitstream)
    run([str(VIVADO), "-mode", "batch", "-nojournal", "-nolog", "-source", slash(tcl)], REPO, RESULTS / "vivado_microblaze_template_build.log")
    write_summary(args.no_bitstream)
    print(RESULTS / "microblaze_template_summary.json")


if __name__ == "__main__":
    main()
