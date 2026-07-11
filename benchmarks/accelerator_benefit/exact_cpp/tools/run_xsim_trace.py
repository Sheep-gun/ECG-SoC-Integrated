#!/usr/bin/env python3
"""Build the locked full top with verification-only Snapshot trace output."""
from __future__ import annotations
import argparse
import shutil
import subprocess
from pathlib import Path

EXACT=Path(__file__).resolve().parents[1]
REPO=EXACT.parents[2]
VIVADO=Path(r"C:\Xilinx\Vivado\2020.2\bin")
CORE=["ecg_event_encoder.v","ecg_event_encoder_adaptive.v","snn_ecg_input_normalizer.v",
      "qrs_lif_detector.v","pnn_rhythm_predictor.v","dscr_spike_counter.v","ram_peak_accumulator.v",
      "rdm_variability_neuron.v","ectopic_pair_neuron.v","qrs_maf_neuron.v","rbbb_qrs_delay_bank.v",
      "abandoned_feature_stubs.v","class_score_neurons.v","snn_ecg_3feat_top.v"]

def slash(path:Path)->str:return str(path).replace("\\","/")
def run(cmd:list[str],cwd:Path,log:Path)->None:
    with log.open("w",encoding="utf-8",errors="replace") as out:
        proc=subprocess.run(cmd,cwd=cwd,stdout=out,stderr=subprocess.STDOUT,text=True)
    if proc.returncode: raise RuntimeError(f"failed: {' '.join(cmd)}; see {log}")

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--input",type=Path,required=True); parser.add_argument("--log",type=Path,required=True)
    args=parser.parse_args(); source=args.input.resolve()
    work=(EXACT/"build-xsim-trace").resolve()
    if work.exists():
        if EXACT not in work.parents: raise RuntimeError("refusing unsafe work deletion")
        shutil.rmtree(work)
    work.mkdir(parents=True)
    local_input=work/"input.mem"; shutil.copyfile(source,local_input)
    sources=[REPO/"rtl"/"core"/name for name in CORE]+[REPO/"rtl"/"final_membrane_layer.v",REPO/"rtl"/"snn_ecg_30min_final_top.v",EXACT/"tools"/"tb_exact_cpp_snapshot_trace.v"]
    prj=work/"sources.prj"; prj.write_text("\n".join(f'verilog work "{slash(p)}"' for p in sources)+"\n",encoding="utf-8",newline="\n")
    tcl=work/"run.tcl"; tcl.write_text("run all\nquit\n",encoding="utf-8",newline="\n")
    run([str(VIVADO/"xvlog.bat"),"--nolog","-i",slash(REPO/"rtl"),"-prj",slash(prj)],work,work/"xvlog.log")
    run([str(VIVADO/"xelab.bat"),"--nolog","-debug","typical","tb_exact_cpp_snapshot_trace","-s","tb_exact_cpp_snapshot_trace"],work,work/"xelab.log")
    args.log.parent.mkdir(parents=True,exist_ok=True)
    run([str(VIVADO/"xsim.bat"),"tb_exact_cpp_snapshot_trace","--nolog","-tclbatch","{"+slash(tcl)+"}"],work,args.log.resolve())
    return 0
if __name__=="__main__":raise SystemExit(main())
