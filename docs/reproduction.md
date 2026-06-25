# Reproduction Guide

## Vivado 프로젝트 열기

~~~text
vivado_project/SNN_ECG_ModelS_Unified/SNN_ECG_ModelS_Unified.xpr
~~~

## 주요 스크립트

- `scripts/`: XSim, synthesis, project rebuild 관련 스크립트
- `reports/`: Model S metric 및 synthesis 결과

## 권장 절차

1. Vivado 2020.2에서 unified project를 연다.
2. RTL source와 testbench source가 모두 정상 로드되는지 확인한다.
3. strict train / validation / test testbench를 실행한다.
4. reports 폴더의 기준 metric과 결과를 비교한다.
5. board smoke top을 implementation한 뒤 bitstream을 Nexys A7에 program한다.

## 주의

GitHub 배포용 저장소에는 ECG 원본 전체 데이터가 포함되지 않을 수 있습니다. 재현 시 dataset manifest와 split 증빙 파일을 먼저 확인해야 합니다.
