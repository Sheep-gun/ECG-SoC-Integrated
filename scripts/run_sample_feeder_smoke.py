from __future__ import annotations

import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "final_membrane_v2_snn" / "sample_feeder_smoke"
XVLOG = Path(r"C:\Xilinx\Vivado\2020.2\bin\xvlog.bat")
XELAB = Path(r"C:\Xilinx\Vivado\2020.2\bin\xelab.bat")
XSIM = Path(r"C:\Xilinx\Vivado\2020.2\bin\xsim.bat")


def slash(path: Path) -> str:
    return str(path).replace("\\", "/")


def run(cmd: list[str], log: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run(cmd, cwd=RESULTS, stdout=f, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed {proc.returncode}: {' '.join(cmd)}; see {log}")


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    prj = RESULTS / "sources_sample_feeder_smoke.prj"
    prj.write_text(
        "\n".join(
            [
                f'verilog work "{slash(REPO / "rtl" / "axi" / "axi_lite_axis_sample_feeder.v")}"',
                f'verilog work "{slash(REPO / "sim" / "tb_axi_lite_axis_sample_feeder.v")}"',
            ]
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    tcl = RESULTS / "run_sample_feeder_smoke.tcl"
    tcl.write_text("run all\nquit\n", encoding="utf-8", newline="\n")

    top = "tb_axi_lite_axis_sample_feeder"
    snap = f"{top}_behav"
    run([str(XVLOG), "--nolog", "-prj", slash(prj)], RESULTS / "xvlog.log")
    run([str(XELAB), "--nolog", "-debug", "typical", top, "-s", snap], RESULTS / "xelab.log")
    run([str(XSIM), snap, "--nolog", "-tclbatch", "{" + slash(tcl) + "}"], RESULTS / "xsim.log")

    text = (RESULTS / "xsim.log").read_text(encoding="utf-8", errors="replace")
    if "FEEDER_SMOKE_PASS" not in text:
        raise RuntimeError(f"sample feeder smoke did not pass; see {RESULTS / 'xsim.log'}")
    print("FEEDER_SMOKE_PASS")


if __name__ == "__main__":
    main()
