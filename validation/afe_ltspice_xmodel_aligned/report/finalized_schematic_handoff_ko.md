# XMODEL-aligned LTspice handoff

다른 workspace에서 우선 가져갈 파일은 다음과 같다.

1. Graphical schematic: `schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc`
2. Generated netlist: `schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.net`
3. Op-amp model/symbol: `schematics/xmodel_aligned/XOpAmp_XMODEL.lib`, `XOpAmp_XMODEL.asy`
4. Audit: `audit/xmodel_alignment_audit.md`, `audit/report_vs_xmodel_aligned.csv`
5. Core tables: `tables/xmodel_aligned_nominal_ac_metrics.csv`, `xmodel_aligned_nominal_transient_metrics.csv`, `xmodel_aligned_track_hold_metrics.csv`, `xmodel_aligned_adc_mapping_metrics.csv`, `xmodel_aligned_stress_results.csv`
6. Final sample CSV: `results/xmodel_aligned/nominal/ltspice_xmodel_aligned_adc_samples.csv`
7. Direct/S&H vectors: `ltspice_xmodel_aligned_direct_adc_signed.mem`, `ltspice_track_hold_adc_signed.mem`
8. Report draft: `report/report_update_draft_ko.md`

Graphical schematic 실행에는 `schematics/xmodel_aligned/patient100_xmodel_drive_10s.txt`도 반드시 함께 전달한다.

현재 최종 후보는 ±1.65 V, dedicated XMODEL-like op-amp, ECG+=patient/ECG-=0, first aperture 1 ms 기준이다. ±5 V 파일은 `pre_alignment` 감사자료이며 최종 결과로 사용하지 않는다.

Fixed XMODEL code correlation은 후속 team handoff에서 완료했다. 동일 10초 ECG 10,000 sample 기준 MAE 0.6445 LSB, RMS 1.3020 LSB, maximum 13 LSB, correlation 0.999518, lag 0이며 98.74%가 ±5 LSB, 99.89%가 ±10 LSB 이내다. TB와 실행/비교 script는 `reference/xmodel_alignment/tb_xmodel_correlation.sv`, `scripts/run_fixed_xmodel_correlation.sh`, `scripts/compare_xmodel_ltspice.py`에 있고 최신 보고서 figure는 `../../../docs/MIXED_SIGNAL_VERIFICATION_KR.md`에 있다.
