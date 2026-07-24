# Pure RTL Elaborated Schematic 재현 안내

## 목적과 범위

이 산출물은 고정 Pure RTL의 실제 module hierarchy를 Vivado 2020.2가 elaboration한 결과다. Top은 `snn_ecg_30min_final_top`, FPGA part는 `xc7a100tcsg324-1`, 고정 digital commit은 `c6b80de19cdcad5b7e43fe7835588b629d847f75`이다. 원본 RTL의 기능, parameter, interface, pipeline timing에는 손대지 않았다.

기존 MicroBlaze 통합 project의 schematic은 MicroBlaze, AXI interconnect, BRAM, UART와 packaged IP shell이 중심이므로 Pure RTL 내부를 설명하기에 적합하지 않다. Packaged `snn_ecg_axi_accelerator`의 외부 AXI shell만 보이는 그림도 register interface를 보여줄 뿐 Snapshot·Final Membrane 계층을 설명하지 못한다. 반대로 synthesized netlist의 모든 LUT, FF, CARRY4, MUX와 net을 펼치면 수천 개 leaf cell 때문에 A4 가로 페이지에서 module명과 주요 신호 관계를 읽을 수 없다.

따라서 이 project는 `design/digital/rtl/`의 recursive minimum source closure만 직접 추가하고 `synth_design -rtl -flatten_hierarchy none`으로 RTL elaboration한다. MicroBlaze, AXI, implementation routing source는 추가하지 않는다.

## 생성 파일과 실제 hierarchy

Figure A는 design root `snn_ecg_30min_final_top` 아래의 실제 instance 두 개를 사용한다.

- `u_snapshot : snn_ecg_3feat_top`
- `u_final : final_membrane_layer`

signed ADC 입력, `u_snapshot`에서 `u_final`로 전달되는 NSR·CHF·ARR·AFF class membrane, `u_final`의 최종 valid/class/membrane 출력만 선택한다. Snapshot timer와 control FSM은 top 내부 `always` logic과 register로 구현되어 있으므로 별도 module처럼 만들지 않았다.

Figure B는 다음 10개 실제 `u_snapshot` child instance를 사용한다.

- `u_event_encoder : ecg_event_encoder_adaptive`
- `u_qrs_detector : qrs_lif_detector`
- `u_pnn : pnn_rhythm_predictor`
- `u_rdm : rdm_variability_neuron`
- `u_ectopic : ectopic_pair_neuron`
- `u_dscr : dscr_spike_counter`
- `u_ram : ram_peak_accumulator`
- `u_qrs_maf : qrs_maf_neuron`
- `u_rbbb_qrs_delay : rbbb_qrs_delay_bank`
- `u_class : class_score_neurons`

나머지 실제 support instance는 `hierarchy_report.txt`에 남겼지만, 보고서 그림의 leaf-cell 폭발을 막기 위해 Figure B에서 생략했다.

Figure C는 만들지 않았다. `final_membrane_layer` 아래에는 별도의 non-primitive source-module child가 없으므로 내부를 펼치면 module hierarchy가 아니라 operator와 register가 나타난다.

## 재현 방법

Repository root의 shell에서 다음을 실행한다.

```text
vivado -mode batch -source tools/vivado/generate_readable_rtl_elaborated_schematic.tcl
```

이 명령은 disposable project `vivado/pure_rtl/project/SNN_ECG_PURE_RTL_VISUALIZATION.xpr`를 다시 만들고 RTL elaboration 및 text report 생성을 검증한다.

Vivado의 실제 PDF/SVG 자동 출력을 실행하려면 다음을 사용한다.

```text
vivado -mode gui -source tools/vivado/generate_readable_rtl_elaborated_schematic.tcl -tclargs --auto-export-exit
```

Vivado 2020.2에서 `show_schematic`과 `write_schematic -format pdf|svg`가 지원됨을 `help`로 확인했다. native PNG export는 지원하지 않는다. Vivado PDF의 회전 metadata를 정규화하고 같은 vector PDF에서 PNG preview를 렌더링하려면 Poppler의 `pdftoppm`이 PATH에 있는 환경에서 다음을 실행한다.

```text
python tools/vivado/normalize_vivado_schematic_pdfs.py
```

`FIG-RTL-A_top_hierarchy.pdf/.png`와 `FIG-RTL-B_snapshot_core_hierarchy.pdf/.png`가 개별 보고서용 파일이다. PDF는 Vivado가 생성한 vector schematic의 페이지 회전 metadata만 정리한 것이며, block·signal·layout을 다시 그리지 않았다.

두 계층을 한 장에서 설명할 때는 `FIG-RTL-AB_top_with_snapshot_expansion.pdf/.png`를 사용한다. 이 파일은 Figure A와 B의 vector PDF를 A4 세로 페이지에 위·아래로 배치한 publication composite다. 두 schematic의 block과 연결은 변경하지 않았고, `u_snapshot` 확대 관계를 나타내는 panel label과 아래 방향 화살표만 추가했다. Parent와 child를 Vivado 한 schematic에서 동시에 강제 전개하면 leaf-cell 탐색이 다시 발생하므로, 이 composite를 단일 Vivado schematic으로 표현하지 않는다.

```text
python tools/vivado/compose_rtl_hierarchy_figure.py
```

## GUI에서 직접 확인하고 수동 출력하는 방법

1. Vivado 2020.2를 실행한다.
2. Repository root를 working directory로 두고 Tcl Console에서 `set argv {--gui}; source tools/vivado/generate_readable_rtl_elaborated_schematic.tcl`을 실행한다. Shell에서는 `vivado -mode gui -source tools/vivado/generate_readable_rtl_elaborated_schematic.tcl -tclargs --gui`를 사용할 수 있다.
3. 열린 RTL Elaborated Design의 top이 `snn_ecg_30min_final_top`인지 확인한다.
4. `FIG-RTL-A_top_hierarchy` 또는 `FIG-RTL-B_snapshot_core_hierarchy` schematic tab을 선택한다.
5. Schematic toolbar에서 **Regenerate Layout**을 누른다.
6. **Zoom Fit**을 눌러 전체 선택 범위를 화면에 맞춘다.
7. 필요하면 불필요한 port bundle만 접는다. 새로운 block이나 net은 추가하지 않는다.
8. **File → Print**를 선택한다.
9. Printer에서 **Microsoft Print to PDF**를 선택한다.
10. Landscape orientation과 페이지 맞춤을 선택하여 저장한다.
11. 저장한 PDF를 A4 가로 크기로 열어 instance명과 handoff signal이 읽히는지 확인한다.

Script가 여는 schematic tab 이름은 `FIG-RTL-A_top_hierarchy`와 `FIG-RTL-B_snapshot_core_hierarchy`다. `write_schematic`, `show_schematic`, `synth_design -flatten_hierarchy none`의 지원 여부와 cell property 결과는 `vivado_capability_report.txt`, `cell_property_probe.txt`에 기록했다.

## 해석상 주의

이 그림은 사람이 다시 그린 conceptual algorithm diagram이 아니다. 원본 RTL elaboration에서 실제로 존재하는 named instance와 실제 handoff signal을 Vivado schematic으로 제한 선택한 것이다. 동시에 placement/routing 결과나 synthesized gate-level netlist도 아니다. 따라서 LUT, FF, CARRY4의 물리 연결이나 FPGA 배치 위치를 나타내지 않는다.

원본 fixed RTL은 수정하지 않았으며, visualization-only Tcl, disposable project와 artifact만 추가했다.
