# Formatting and Figure Audit

## Audit Summary

| 항목 | 최종 상태 | 조치 |
|---|---|---|
| README.md | 최종 제출 첫 화면 구조 | heading/table/Mermaid/image link를 GitHub Markdown 기준으로 정리 |
| FINAL_REPORT_KR.md | 논문형 최종 보고서 구조 | figure 삽입, 결과 해석, 한계 범위를 locked final model 기준으로 정리 |
| docs tree | final-facing 5개 문서만 유지 | 중간/폐기 문서 노출 없이 README에서 필요한 문서만 연결 |
| reports/final Markdown | evidence summary 문서 유지 | board replay, strict record-wise, Vivado, XSim 요약을 최종 제출 톤으로 정리 |
| final result figure | final_test 중심 시각화 | validation 100.00%는 model-selection 영역으로 낮추고 final_test 80.56%/84.21%를 중심 배치 |
| resource/timing figure | badge/card 기반 시각화 | BRAM/DSP 0 값이 사라지지 않도록 별도 resource badge로 표시 |
| board replay evidence | 36개 strict final_test transcript/CSV 존재 | final_pred 36/36, final_mem exact 36/36으로 분리 보고 |
| checker | 자동 consistency check | heading blank line, Mermaid fence, table row, image/link, figure 해상도, metric 일치성 검사 |

## Final-facing Documents

- `README.md`
- `FINAL_REPORT_KR.md`
- `docs/PAPER_SUMMARY_KR.md`
- `docs/SYSTEM_ARCHITECTURE_KR.md`
- `docs/STRICT_RECORDWISE_PROTOCOL_KR.md`
- `docs/HARDWARE_VALIDATION_KR.md`
- `docs/LIMITATIONS_KR.md`

## Generated Figures

최종 보고서용 figure 목록은 `reports/final/figures/FIGURE_INDEX.md`에 정리되어 있다. 모든 final report figure는 `tools/make_final_report_figures.py`로 재생성할 수 있다.

## Remaining Notes

- Board replay는 strict final_test 36개 30분 case evidence이며, 기존 class-wise 4-case replay는 representative smoke evidence로 분리한다.
- Validation 100.00%는 model-selection 성능으로만 문서화했다.
- Physical AFE PCB, ADC silicon, transistor-level layout, clinical diagnosis validation claim은 문서에서 제외했다.
