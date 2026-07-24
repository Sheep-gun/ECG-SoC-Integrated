# Public repository preflight

## 포함

- 고정 AFE–ADC와 Digital RTL source
- Python과 Exact C++ equivalent model
- Pure RTL 및 MicroBlaze canonical Vivado project 각 1개
- 재현 script, compact acceptance, raw-dump audit와 final figures
- claim, evidence, upstream commit와 unresolved registry

## 제외

- 참가신청서의 개인정보, 서명과 직인
- raw PhysioNet database
- temporary Vivado packaging, IP catalog와 cache project
- 중복 upstream checkout과 중간 screenshot

## 공개 claim boundary

30분 engineering validation, FPGA implementation과 model-level AFE–RTL integration까지 공개한다. 24시간 성능, physical AFE/ADC, ASIC/post-layout, silicon power와 clinical validation은 완료 결과로 주장하지 않는다.

최종 검사는 다음 명령으로 수행한다.

```text
python tools/check_clean_workspace.py
python tools/check_integrated_technical_report.py
python tools/check_integrated_repository.py
git diff --check
```
