from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "board_replay" / "microblaze_full_replay"
WORK = REPO.parent / "_snn_ecg_ip_packager_work"
IP_REPO = REPO / "ip_repo"
IP_ROOT = IP_REPO / "snn_ecg_axi_accelerator"
CHECK_WORK = REPO.parent / "_snn_ecg_ip_catalog_check"
VIVADO = Path(r"C:\Xilinx\Vivado\2020.2\bin\vivado.bat")

IP_VENDOR = "user.org"
IP_LIBRARY = "user"
IP_NAME = "snn_ecg_axi_accelerator"
IP_VERSION = "1.0"
TOP = "snn_ecg_axi_lite_stream_top"
PART = "xc7a100tcsg324-1"
IP_VERSION_TAG = IP_VERSION.replace(".", "_")
XGUI_NAME = f"{IP_NAME}_v{IP_VERSION_TAG}.tcl"
OLD_XGUI_NAME = f"{TOP}_v{IP_VERSION_TAG}.tcl"

CORE_SOURCES = [
    "ecg_event_encoder_adaptive.v",
    "snn_ecg_input_normalizer.v",
    "qrs_lif_detector.v",
    "pnn_rhythm_predictor.v",
    "dscr_spike_counter.v",
    "ram_peak_accumulator.v",
    "rdm_variability_neuron.v",
    "ectopic_pair_neuron.v",
    "qrs_maf_neuron.v",
    "rbbb_qrs_delay_bank.v",
    "abandoned_feature_stubs.v",
    "class_score_neurons.v",
    "snn_ecg_3feat_top.v",
]


def slash(path: Path) -> str:
    return str(path).replace("\\", "/")


def quote_tcl_list(paths: list[Path]) -> str:
    return " \\\n    ".join(f'"{slash(path)}"' for path in paths)


def write_tcl() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    rtl_files = [REPO / "rtl" / "common" / "reset_sync.v"]
    rtl_files.extend(REPO / "rtl" / "core" / src for src in CORE_SOURCES)
    rtl_files.extend(
        [
            REPO / "rtl" / "strict_recordwise_locked_params.vh",
            REPO / "rtl" / "final_membrane_layer.v",
            REPO / "rtl" / "snn_ecg_30min_final_top.v",
            REPO / "rtl" / "axi" / "snn_ecg_axi_lite_stream_top.v",
        ]
    )
    sim_files = [REPO / "sim" / "tb_snn_ecg_axi_smoke.v"]

    tcl = WORK / "package_snn_ecg_axi_ip.tcl"
    tcl.write_text(
        f"""set repo_dir "{slash(REPO)}"
set work_dir "{slash(WORK)}"
set ip_repo "{slash(IP_REPO)}"
set ip_root "{slash(IP_ROOT)}"
set check_work "{slash(CHECK_WORK)}"
set ip_vendor "{IP_VENDOR}"
set ip_library "{IP_LIBRARY}"
set ip_name "{IP_NAME}"
set ip_version "{IP_VERSION}"
set ip_vlnv "$ip_vendor:$ip_library:$ip_name:$ip_version"

proc set_bus_param {{bus name value}} {{
    set param [ipx::get_bus_parameters $name -of_objects $bus -quiet]
    if {{[llength $param] == 0}} {{
        set param [ipx::add_bus_parameter $name $bus]
    }}
    set_property VALUE $value $param
}}

proc require_bus_interface {{core name}} {{
    set bus [ipx::get_bus_interfaces $name -of_objects $core -quiet]
    if {{[llength $bus] != 1}} {{
        error "Expected exactly one bus interface named $name, got [llength $bus]"
    }}
    return [lindex $bus 0]
}}

file mkdir $work_dir
file mkdir $ip_repo

create_project -force ${{ip_name}}_pack "$work_dir/vivado_project" -part {PART}

set rtl_files [list \\
    {quote_tcl_list(rtl_files)} \\
]
set sim_files [list \\
    {quote_tcl_list(sim_files)} \\
]

add_files -fileset sources_1 -norecurse $rtl_files
set_property include_dirs [list "$repo_dir/rtl"] [current_fileset]
set locked_param_header [get_files -quiet "$repo_dir/rtl/strict_recordwise_locked_params.vh"]
if {{[llength $locked_param_header] > 0}} {{
    set_property file_type {{Verilog Header}} $locked_param_header
}}
set_property top {TOP} [current_fileset]
update_compile_order -fileset sources_1

add_files -fileset sim_1 -norecurse $sim_files
update_compile_order -fileset sim_1

ipx::package_project -root_dir $ip_root -vendor $ip_vendor -library $ip_library \\
    -taxonomy /UserIP -import_files -set_current true -force
set core [ipx::current_core]
set_property name $ip_name $core
set_property display_name {{Long-Window ECG 4-Class AXI Accelerator}} $core
set_property description {{Long-window ECG 4-class accelerator IP core with AXI4-Lite control and AXI4-Stream ADC sample input.}} $core
set_property vendor_display_name {{User}} $core
set_property company_url {{https://user.org}} $core
set_property version $ip_version $core
set_property taxonomy {{/UserIP}} $core

set s_axi [require_bus_interface $core s_axi]
set s_axis [require_bus_interface $core s_axis]
set clk_if [require_bus_interface $core s_axi_aclk]
set rst_if [require_bus_interface $core s_axi_aresetn]
set irq_if [require_bus_interface $core irq]

set_property BUS_TYPE_VLNV xilinx.com:interface:aximm:1.0 $s_axi
set_property ABSTRACTION_TYPE_VLNV xilinx.com:interface:aximm_rtl:1.0 $s_axi
set_property INTERFACE_MODE slave $s_axi

set_property BUS_TYPE_VLNV xilinx.com:interface:axis:1.0 $s_axis
set_property ABSTRACTION_TYPE_VLNV xilinx.com:interface:axis_rtl:1.0 $s_axis
set_property INTERFACE_MODE slave $s_axis
set_bus_param $s_axis HAS_TREADY 1
set_bus_param $s_axis HAS_TLAST 1
set_bus_param $s_axis TDATA_NUM_BYTES 2
set_bus_param $s_axis TID_WIDTH 0
set_bus_param $s_axis TDEST_WIDTH 0
set_bus_param $s_axis TUSER_WIDTH 0

set_property BUS_TYPE_VLNV xilinx.com:signal:clock:1.0 $clk_if
set_property ABSTRACTION_TYPE_VLNV xilinx.com:signal:clock_rtl:1.0 $clk_if
set_property INTERFACE_MODE slave $clk_if
set_bus_param $clk_if ASSOCIATED_BUSIF {{s_axi:s_axis}}
set_bus_param $clk_if ASSOCIATED_RESET s_axi_aresetn
set_bus_param $clk_if FREQ_HZ 100000000
set_bus_param $clk_if FREQ_TOLERANCE_HZ 0

set_property BUS_TYPE_VLNV xilinx.com:signal:reset:1.0 $rst_if
set_property ABSTRACTION_TYPE_VLNV xilinx.com:signal:reset_rtl:1.0 $rst_if
set_property INTERFACE_MODE slave $rst_if
set_bus_param $rst_if POLARITY ACTIVE_LOW

set_property BUS_TYPE_VLNV xilinx.com:signal:interrupt:1.0 $irq_if
set_property ABSTRACTION_TYPE_VLNV xilinx.com:signal:interrupt_rtl:1.0 $irq_if
set_property INTERFACE_MODE master $irq_if
set_bus_param $irq_if SENSITIVITY LEVEL_HIGH

set mem_maps [ipx::get_memory_maps s_axi -of_objects $core -quiet]
if {{[llength $mem_maps] != 1}} {{
    error "Expected exactly one inferred memory map named s_axi, got [llength $mem_maps]"
}}
set addr_blocks [ipx::get_address_blocks -of_objects [lindex $mem_maps 0] -quiet]
if {{[llength $addr_blocks] != 1}} {{
    error "Expected exactly one inferred address block for s_axi, got [llength $addr_blocks]"
}}
set addr_block [lindex $addr_blocks 0]
set_property BASE_ADDRESS 0 $addr_block
set_property RANGE 4096 $addr_block
set_property WIDTH 32 $addr_block
set_property USAGE register $addr_block

ipx::update_checksums $core
ipx::check_integrity $core
ipx::save_core $core
close_project

set old_xgui "$ip_root/xgui/{OLD_XGUI_NAME}"
set new_xgui "$ip_root/xgui/{XGUI_NAME}"
if {{[file exists $old_xgui]}} {{
    file copy -force $old_xgui $new_xgui
    if {{$old_xgui ne $new_xgui}} {{
        file delete -force $old_xgui
    }}
}}

set component_xml "$ip_root/component.xml"
set component_fh [open $component_xml r]
set component_text [read $component_fh]
close $component_fh
regsub -all {{xgui/{OLD_XGUI_NAME}}} $component_text {{xgui/{XGUI_NAME}}} component_text
regsub -all {{{TOP}_v{IP_VERSION_TAG}}} $component_text {{{IP_NAME}_v{IP_VERSION_TAG}}} component_text
set component_fh [open $component_xml w]
puts -nonewline $component_fh $component_text
close $component_fh

file delete -force $check_work
create_project -force ${{ip_name}}_catalog_check "$check_work/vivado_project" -part {PART}
set_property ip_repo_paths [list $ip_repo] [current_project]
update_ip_catalog
set defs [get_ipdefs -all $ip_vlnv]
if {{[llength $defs] == 0}} {{
    error "Packaged IP $ip_vlnv was not found in catalog"
}}
create_ip -vlnv $ip_vlnv -module_name snn_ecg_axi_accelerator_0
generate_target all [get_ips snn_ecg_axi_accelerator_0]
report_ip_status -file "$check_work/ip_status.rpt"
exit
""",
        encoding="utf-8",
        newline="\n",
    )
    return tcl


def validate_component() -> dict[str, object]:
    component = IP_ROOT / "component.xml"
    if not component.exists():
        raise FileNotFoundError(component)
    text = component.read_text(encoding="utf-8", errors="replace")
    required = {
        "vendor": IP_VENDOR,
        "library": IP_LIBRARY,
        "name": IP_NAME,
        "version": IP_VERSION,
        "top": TOP,
        "s_axi": "s_axi",
        "s_axis": "s_axis",
        "clock": "s_axi_aclk",
        "reset": "s_axi_aresetn",
        "irq": "irq",
        "awprot": "AWPROT",
        "arprot": "ARPROT",
        "aximm": 'spirit:name="aximm"',
        "axis": 'spirit:name="axis"',
        "interrupt": 'spirit:name="interrupt"',
        "associated_busif": "s_axi:s_axis",
        "xgui": f"xgui/{XGUI_NAME}",
        "component_name": f"{IP_NAME}_v{IP_VERSION_TAG}",
    }
    missing = [name for name, needle in required.items() if needle not in text]
    if missing:
        raise RuntimeError(f"component.xml missing expected markers: {missing}")
    bad_path_markers = [slash(WORK), slash(CHECK_WORK)]
    leaked = [marker for marker in bad_path_markers if marker in text]
    if leaked:
        raise RuntimeError(f"component.xml contains workdir paths: {leaked}")
    return {
        "component_xml": str(component),
        "ip_vlnv": f"{IP_VENDOR}:{IP_LIBRARY}:{IP_NAME}:{IP_VERSION}",
        "required_markers_present": sorted(required),
        "workdir_paths_leaked": False,
        "catalog_check_ip_status": str(CHECK_WORK / "ip_status.rpt"),
    }


def main() -> None:
    if not VIVADO.exists():
        raise FileNotFoundError(f"Vivado not found: {VIVADO}")
    if WORK.exists():
        shutil.rmtree(WORK)
    if IP_ROOT.exists():
        shutil.rmtree(IP_ROOT)
    WORK.mkdir(parents=True, exist_ok=True)
    IP_REPO.mkdir(parents=True, exist_ok=True)
    tcl = write_tcl()
    log = WORK / "package_snn_ecg_axi_ip.log"
    with log.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run(
            [str(VIVADO), "-mode", "batch", "-nojournal", "-nolog", "-source", slash(tcl)],
            cwd=REPO,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True,
        )
    if proc.returncode != 0:
        raise RuntimeError(f"Vivado IP packaging failed; see {log}")
    summary = validate_component()
    result_log = RESULTS / "snn_ecg_axi_ip_package.log"
    shutil.copy2(log, result_log)
    ip_status = CHECK_WORK / "ip_status.rpt"
    if ip_status.exists():
        result_ip_status = RESULTS / "snn_ecg_axi_ip_status.rpt"
        shutil.copy2(ip_status, result_ip_status)
        summary["catalog_check_ip_status"] = str(result_ip_status)
    summary["vivado_log"] = str(result_log)
    summary_path = RESULTS / "snn_ecg_axi_ip_package_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(summary_path)


if __name__ == "__main__":
    main()
