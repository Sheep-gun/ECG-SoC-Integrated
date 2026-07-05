# Formatting and Figure Audit

## Audit Summary

| 항목 | 현재 상태 | 문제 | 조치 |
|---|---|---|---|
| README.md | 최종 제출 첫 화면 구조로 정리됨 | 기존에는 figure package 연결이 부족했음 | Abstract, System Flow, Final Locked Model, Hardware, Repository Structure, Limitations, Main Report Link로 재구성 |
| FINAL_REPORT_KR.md | 논문형 12-section 구조로 정리됨 | figure 삽입과 section 흐름이 부족했음 | Abstract부터 Conclusion까지 최종 locked model 기준으로 재작성 |
| docs tree | final-facing 5개 문서만 유지됨 | 중간 보고서 링크 노출 위험은 현재 없음 | 5개 문서 모두 README/최종보고서와 같은 claim boundary로 정리 |
| reports/final/figures | 기존 AFE waveform figure만 존재했음 | 최종 시스템/결과/검증 흐름 figure가 부족했음 | final report용 8개 PNG와 `FIGURE_INDEX.md` 생성 |
| final_metrics.json | 최종 수치 source of truth로 존재 | 문서/figure가 같은 값을 읽는지 확인 필요 | figure script와 checker가 해당 JSON 기준으로 검증 |
| board replay evidence | 4개 class-wise transcript/CSV 존재 | 36-case board batch와 혼동 위험 | 문서와 figure에 4-case representative replay로 명시 |
| Mermaid | README/FINAL_REPORT/docs에 code fence로 존재 | Mermaid fence 검증 필요 | consistency checker에 Mermaid fence 존재 검사 추가 |
| Markdown tables | 주요 결과 표 존재 | table row 형식 검증 필요 | consistency checker에 간단한 pipe table 검사 추가 |

## Final-facing Documents

- `README.md`
- `FINAL_REPORT_KR.md`
- `docs/PAPER_SUMMARY_KR.md`
- `docs/SYSTEM_ARCHITECTURE_KR.md`
- `docs/STRICT_RECORDWISE_PROTOCOL_KR.md`
- `docs/HARDWARE_VALIDATION_KR.md`
- `docs/LIMITATIONS_KR.md`

## Generated Figures

Figure 목록은 `reports/final/figures/FIGURE_INDEX.md`를 기준으로 한다. 모든 새 figure는 `tools/make_final_report_figures.py`로 재생성할 수 있다.

## Remaining Notes

- Board replay는 class-wise 대표 4개 30분 case evidence이다.
- Validation 100.00%는 model-selection 성능으로만 문서화했다.
- Physical AFE PCB, ADC silicon, transistor-level layout, clinical diagnosis validation claim은 문서에서 제외했다.
