from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "board_replay" / "microblaze_full_replay"
WORK = REPO.parent / "_sample_feeder_ip_packager_work"
CHECK_WORK = REPO.parent / "_sample_feeder_ip_catalog_check"
IP_REPO = REPO / "ip_repo"
IP_ROOT = IP_REPO / "axi_lite_axis_sample_feeder"
VIVADO = Path(r"C:\Xilinx\Vivado\2020.2\bin\vivado.bat")

IP_VENDOR = "user.org"
IP_LIBRARY = "user"
IP_NAME = "axi_lite_axis_sample_feeder"
IP_VERSION = "1.0"
TOP = "axi_lite_axis_sample_feeder"
PART = "xc7a100tcsg324-1"


def slash(path: Path) -> str:
    return str(path).replace("\\", "/")


def quote_tcl_list(paths: list[Path]) -> str:
    return " \\\n    ".join(f'"{slash(path)}"' for path in paths)


def write_tcl() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    rtl_files = [REPO / "rtl" / "axi" / "axi_lite_axis_sample_feeder.v"]
    sim_files = [REPO / "sim" / "tb_axi_lite_axis_sample_feeder.v"]
    tcl = WORK / "package_sample_feeder_ip.tcl"
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
set_property top {TOP} [current_fileset]
update_compile_order -fileset sources_1

add_files -fileset sim_1 -norecurse $sim_files
update_compile_order -fileset sim_1

ipx::package_project -root_dir $ip_root -vendor $ip_vendor -library $ip_library \\
    -taxonomy /UserIP -import_files -set_current true -force
set core [ipx::current_core]
set_property name $ip_name $core
set_property display_name {{AXI-Lite AXIS Sample Feeder}} $core
set_property description {{AXI4-Lite controlled sample feeder with a small FIFO and AXI4-Stream master output.}} $core
set_property vendor_display_name {{User}} $core
set_property company_url {{https://user.org}} $core
set_property version $ip_version $core
set_property taxonomy {{/UserIP}} $core

set s_axi [require_bus_interface $core s_axi]
set m_axis [require_bus_interface $core m_axis]
set clk_if [require_bus_interface $core s_axi_aclk]
set rst_if [require_bus_interface $core s_axi_aresetn]

set_property BUS_TYPE_VLNV xilinx.com:interface:aximm:1.0 $s_axi
set_property ABSTRACTION_TYPE_VLNV xilinx.com:interface:aximm_rtl:1.0 $s_axi
set_property INTERFACE_MODE slave $s_axi

set_property BUS_TYPE_VLNV xilinx.com:interface:axis:1.0 $m_axis
set_property ABSTRACTION_TYPE_VLNV xilinx.com:interface:axis_rtl:1.0 $m_axis
set_property INTERFACE_MODE master $m_axis
set_bus_param $m_axis HAS_TREADY 1
set_bus_param $m_axis HAS_TLAST 1
set_bus_param $m_axis TDATA_NUM_BYTES 2
set_bus_param $m_axis TID_WIDTH 0
set_bus_param $m_axis TDEST_WIDTH 0
set_bus_param $m_axis TUSER_WIDTH 0

set_property BUS_TYPE_VLNV xilinx.com:signal:clock:1.0 $clk_if
set_property ABSTRACTION_TYPE_VLNV xilinx.com:signal:clock_rtl:1.0 $clk_if
set_property INTERFACE_MODE slave $clk_if
set_bus_param $clk_if ASSOCIATED_BUSIF {{s_axi:m_axis}}
set_bus_param $clk_if ASSOCIATED_RESET s_axi_aresetn
set_bus_param $clk_if FREQ_HZ 100000000
set_bus_param $clk_if FREQ_TOLERANCE_HZ 0

set_property BUS_TYPE_VLNV xilinx.com:signal:reset:1.0 $rst_if
set_property ABSTRACTION_TYPE_VLNV xilinx.com:signal:reset_rtl:1.0 $rst_if
set_property INTERFACE_MODE slave $rst_if
set_bus_param $rst_if POLARITY ACTIVE_LOW

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

file delete -force $check_work
create_project -force ${{ip_name}}_catalog_check "$check_work/vivado_project" -part {PART}
set_property ip_repo_paths [list $ip_repo] [current_project]
update_ip_catalog
set defs [get_ipdefs -all $ip_vlnv]
if {{[llength $defs] == 0}} {{
    error "Packaged IP $ip_vlnv was not found in catalog"
}}
create_ip -vlnv $ip_vlnv -module_name axi_lite_axis_sample_feeder_0
generate_target all [get_ips axi_lite_axis_sample_feeder_0]
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
        "m_axis": "m_axis",
        "clock": "s_axi_aclk",
        "reset": "s_axi_aresetn",
        "awprot": "AWPROT",
        "arprot": "ARPROT",
        "aximm": 'spirit:name="aximm"',
        "axis": 'spirit:name="axis"',
        "associated_busif": "s_axi:m_axis",
    }
    missing = [name for name, needle in required.items() if needle not in text]
    if missing:
        raise RuntimeError(f"component.xml missing expected markers: {missing}")
    leaked = [marker for marker in [slash(WORK), slash(CHECK_WORK)] if marker in text]
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
    log = WORK / "package_sample_feeder_ip.log"
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
    result_log = RESULTS / "sample_feeder_ip_package.log"
    shutil.copy2(log, result_log)
    ip_status = CHECK_WORK / "ip_status.rpt"
    if ip_status.exists():
        result_ip_status = RESULTS / "sample_feeder_ip_status.rpt"
        shutil.copy2(ip_status, result_ip_status)
        summary["catalog_check_ip_status"] = str(result_ip_status)
    summary["vivado_log"] = str(result_log)
    summary_path = RESULTS / "sample_feeder_ip_package_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(summary_path)


if __name__ == "__main__":
    main()
