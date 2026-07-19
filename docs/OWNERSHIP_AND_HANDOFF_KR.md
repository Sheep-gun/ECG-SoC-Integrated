# 소유권과 handoff

## Canonical ownership

| Contributor | Primary ownership | Handoff output |
|---|---|---|
| 서민우 | MATLAB nominal AFE+ADC pre-validation, parameter/frequency/gain reference, ADC headroom/clipping, signed reference vectors와 manifest | nominal analog intent, coding convention, class별 reference package |
| 이수환 | LTspice/XMODEL AFE+ADC 구현·검증, non-ideal/stress, full-record stream generation, AFE-to-digital integration | LTspice schematic·검증표, signed 12-bit AFE output, SHA256 identity, canonical cadence integration evidence |
| 양건 | project leadership, long-window architecture, strict evaluation, locked integer model, RTL/XSim/Vivado/IP-XACT/Vitis/board, final integration | locked digital golden, synthesizable/packageable IP, implementation and board evidence |

Canonical machine-readable record는 `source_of_truth/ownership_matrix.csv`이다.

## Handoff 1: MATLAB → LTspice → XMODEL

서민우 component는 nominal parameter와 ADC coding, class별 signed/offset-binary reference vector를 제공한다. 이수환 검증은 이를 ±1.65 V LTspice schematic으로 구현해 회로 응답·S/H·ADC mapping과 stress를 확인한 뒤 같은 회로 계약을 XMODEL signal chain과 RTL 인계 기준으로 사용한다. MATLAB이나 LTspice 결과를 physical measurement로 승격하지 않으며, XMODEL의 non-ideal claim은 별도 evidence에서 검증한다.

## Handoff 2: XMODEL → Digital

이수환 component는 1 kSPS signed 12-bit stream을 생성하고, 36개 final-test chunk가 양건 component의 board-replay input과 SHA256-identical임을 확인한다. Canonical board-facing XSim cadence는 `sample_gap_cycles=2`이다. 이 조건에서 final_pred와 final_mem이 digital golden과 36/36 bit-exact였다는 것이 handoff acceptance criterion이다.

## Handoff 3: Digital → FPGA/IP

양건 component는 locked model의 parameter hash와 final metrics를 고정하고, 같은 architecture를 RTL, XSim, Vivado, AXI/IP-XACT, Vitis/MicroBlaze와 board replay로 연결한다. Board result는 classification algorithm ownership과 physical analog ownership을 확장하지 않는다.

## 협업 claim의 표현

Mixed-signal-to-digital chain은 공동 integration 결과지만 구현 owner를 합치지 않는다.

- MATLAB nominal implementation owner: 서민우
- LTspice/XMODEL and AFE-to-digital verification owner: 이수환
- digital architecture/implementation owner: 양건
- integrated repository and final claim coordination: 양건

한 contributor의 artifact를 다른 contributor의 구현 성과로 표현하지 않는다.
