# Hardware implementation

## Pure RTL implementation

Locked long-window top을 Vivado에서 구현한 direct evidence는 다음과 같다.

| Metric | Value | Interpretation |
|---|---:|---|
| LUT | 9719 | pure RTL implemented design |
| FF | 5038 | pure RTL implemented design |
| BRAM | 0 | raw long-window buffer를 사용하지 않는 구조와 일치 |
| DSP | 0 | integer/shift-add/comparator 중심 datapath |
| WNS | 8.184 ns | recorded constraints에서 positive timing slack |

이는 fixed device/tool/configuration의 implementation evidence다. WNS를 processing latency로 바꾸거나 resource 수치만으로 energy superiority를 주장하지 않는다.

## IP-XACT and AXI packaging

Digital core는 AXI-Lite/stream wrapper와 sample feeder를 포함하는 reusable IP 형태로 package됐다. `components/digital_accelerator/ip_repo/`의 `component.xml`, source와 xgui metadata가 packaging evidence다. Smoke simulation과 packaging scripts는 interface integrity를 지원한다.

## Vitis/MicroBlaze full-replay system

| Metric | Value | Scope |
|---|---:|---|
| LUT | 12494 | accelerator + MicroBlaze replay system |
| Slice register | 8494 | whole system |
| BRAM | 16 | software/data/replay infrastructure 포함 |
| DSP | 3 | whole system |
| Setup WNS | 0.097 ns | system implementation timing closure |
| Hold WNS | 0.019 ns | system implementation timing closure |

Pure RTL과 MicroBlaze system resource는 scope가 다르므로 같은 열에서 직접 감소율로 비교하지 않는다.

## FPGA replay

Strict final-test 36개 full-record stream을 packaged system에서 replay했다. 각 case는 1,800,000 accepted samples, 30 snapshots와 한 decision을 갖는다. Board final_pred와 final_mem은 full-top XSim expected output과 각각 36/36 일치했다. Ground-truth label과의 accuracy는 29/36이다.

## 구현되지 않은 물리 범위

Nexys A7 replay는 digital IP integration proof다. External electrode, physical AFE PCB, ADC silicon, fabricated SoC 또는 post-layout ASIC result가 아니다. Historical source 안의 XADC 제안이나 demo description을 실제 live acquisition으로 승격하지 않는다.

## Benchmark 분리

Resource와 timing closure는 본 문서에 포함하지만 CPU/RTL latency, throughput, speedup, power와 energy는 별도 benchmark package가 완료될 때까지 공란이다.
