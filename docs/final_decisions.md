# Final Decisions

## 최종 채택

- 최종 모델명: Model S
- core feature: pNN125, RDM, DSCR, RAM, ECP, QRS MAF
- 추가 readout: RBBB QRS Delay Bank, EERG
- 평가 기준: strict record-wise holdout
- FPGA 검증: Nexys A7 board smoke test

## 폐기한 방향

- hard decision tree 구조
- test set을 보고 weight를 조정하는 방식
- RCD/RCD2/IPB/ETMC 계열 중 최종 Model S에 포함되지 않은 실험 branch
- count를 그대로 class score에 넣는 구조

## 최종 해석

Model S는 single 60초 segment만으로 임상 진단을 확정하는 장치가 아니라, ECG stream에서 여러 feature spike를 누적하여 record-level 판단을 수행하는 SNN-inspired RTL classifier로 정의합니다.
