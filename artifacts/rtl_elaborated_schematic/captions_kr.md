# 보고서용 캡션

## Figure A — Pure RTL top hierarchy

Vivado RTL Elaborated Design에서 확인한 `snn_ecg_30min_final_top`의 상위 계층. 60초 Snapshot 처리 코어 `u_snapshot`과 30분 Final Membrane 계층 `u_final`은 원본 RTL의 실제 instance이다. signed ADC 입력, 두 계층 사이의 네 class-membrane handoff와 최종 class/membrane 출력만 선택하여 표시했다. Snapshot timer와 control FSM은 top module 내부 logic으로 구현되므로 별도의 가상 블록으로 그리지 않았다.

## Figure B — Snapshot core hierarchy

Vivado RTL Elaborated Design에서 확인한 `u_snapshot`의 주요 module hierarchy. 사건 부호화, QRS 검출, PNN·RDM·ectopic·DSCR·RAM·QRS MAF·RBBB 증거 생성과 class readout에 해당하는 10개 실제 RTL instance와 실제 handoff signal만 선택했다. 알고리즘 개념도나 LUT·FF 수준의 synthesized netlist가 아니며, 표시하지 않은 실제 보조 instance는 `hierarchy_report.txt`에 기록했다.

## Figure AB — Top hierarchy and Snapshot expansion

Pure RTL 상위 계층과 `u_snapshot`의 실제 내부 hierarchy를 A4 세로 한 페이지에 위·아래로 배치한 확대 Figure. (a)와 (b)는 각각 Vivado RTL Elaborated Schematic에서 직접 export한 Figure A와 Figure B이며, 파란 화살표와 panel 배치만 두 계층의 확대 관계를 설명하기 위해 추가했다. 단일 schematic에서 parent와 child를 동시에 강제 전개한 그림이나 사람이 다시 그린 연결도가 아니다.

## Figure C — 생략

`final_membrane_layer` 아래에는 별도의 source-module child instance가 없다. 이를 펼치면 읽기 쉬운 module hierarchy가 아니라 RTL operator와 register가 노출되므로 Figure C는 생성하지 않았다.
