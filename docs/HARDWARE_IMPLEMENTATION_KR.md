# Hardware implementation

## Pure RTL implementation

Locked long-window top을 Vivado에서 구현한 direct evidence는 다음과 같다.

| Metric | Value | Interpretation |
|---|---:|---|
| LUT | 9719 | pure RTL implemented design |
| FF | 5038 | pure RTL implemented design |
| BRAM | 0 | direct RTL streaming-state audit와 일치하는 implementation evidence |
| DSP | 0 | integer/shift-add/comparator 중심 datapath |
| WNS | 8.184 ns | recorded constraints에서 positive timing slack |

이는 fixed device/tool/configuration의 implementation evidence다. WNS를 processing latency로 바꾸거나 resource 수치만으로 energy superiority를 주장하지 않는다.

## RTL timing bottleneck과 pipeline 최적화 이력

초기 OOC 분석에서는 `class_score_neurons`의 `rdm_level_spike → pred_class` 경로가 약 90 logic levels와 52개 CARRY4를 포함한 주요 병목으로 관측됐다. `c7c75cf...`와 `5e2e5d0...`에서 C24/readout–WTA 분리, `*_next` capture, delta 등록, exact lookup, Snapshot 단계 분리, QRS MAF timestamp FIFO, PNN center 등록, Final Membrane pairwise stage와 flush 정렬을 적용했다. 두 commit은 최종 고정 RTL `c6b80de...`의 ancestor다.

Historical OOC에서 약 17.5k LUT였던 hotspot 값은 최적화 전 `class_score_neurons` 분석값이며, 위 표의 최종 Pure RTL 9,719 LUT와 직접 비교하지 않는다. 원래 RDM-to-prediction path 제거를 timing report로 확인한 뒤 Python–RTL과 FPGA 기능 등가성을 확인했다. 최종 근거는 Pure RTL WNS 8.184 ns, MicroBlaze system setup WNS 0.097 ns, XSim의 `final_pred`·`final_mem` mismatch 각 0/36과 FPGA 두 출력 각 36/36이다 [CLM-048]. 상세 Git history와 현재 component에서 추적 가능한 RTL 경로는 `docs/RTL_TIMING_OPTIMIZATION_HISTORY_KR.md`에 구분해 기록한다.

Full-window-buffer avoidance의 직접 근거는 BRAM=0 단일 수치가 아니라 `STREAMING_STATE_MEMORY_KR.md`와 `streaming_state_inventory.csv`의 RTL state/control inspection이다 [CLM-023]. `avoided full raw-input window storage`는 2.7 MB decimal이며 MicroBlaze memory 측정값이 아니다.

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

Resource와 timing closure에 더해 Nexys A7-100T 36-case hardware counter를 반영한다. Active-core는 `profile_total-profile_input_wait=3,601,290 cycles`, 36.012900 ms이고 처리량은 49,982,089.751172 samples/s, Exact C++ 대비 speedup은 49.362861641×다. UART-paced raw interval 187,144.750920 ms는 transport diagnostic으로만 보존하며 integrated-system compute timing은 미측정이다. 성능 조건과 일치하는 direct-100 MHz timing-closed route의 네 class 실제 ECG burst SAIF 중앙값은 accelerator+static/hierarchy dynamic/device static 0.149500/0.052500/0.097000 W이고 WNS +0.035 ns로 MET이다. Routed-net SAIF match는 약 12%이며 미매칭 net은 vectorless다. 기존 1 MHz 0.099 W와 MicroBlaze system 0.271 W는 각각 별도 vectorless power-only operating point이며 physical board input power는 미측정이다.
