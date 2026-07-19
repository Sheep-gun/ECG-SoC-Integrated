# Integrated figure index

Generated integrated figures and immutable team-provided analog validation figures are indexed below. Generated source data: `figures/source/figure_data.json`; analog handoff hashes: `figures/source/team_handoff_analog/README.md`.

## FIG-01

- File: `figures/final/FIG-01_long_window_motivation.svg`
- Owner: 양건
- Source files: `docs/PROBLEM_DEFINITION_KR.md`
- Source commits: INTEGRATED
- Source-data path: `figures/source/figure_data.json`
- Caption: 장시간 ECG에서 국소 evidence와 장기 persistence를 결합하는 문제 동기
- Evidence scope: architectural motivation
- Limitations: Holter-oriented; not clinical certification

## FIG-02

- File: `figures/final/FIG-02_research_workflow.svg`
- Owner: 서민우·이수환·양건
- Source files: `source_of_truth/upstream_commits.yaml`, `validation/afe_ltspice_xmodel_aligned/README.md`, `components/digital_accelerator/configs/final_submission_locked_model.json`, `components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv`, `components/digital_accelerator/reports/final/final_metrics.json`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192, INTEGRATED_LTSPICE_2026-07-19, 4756a5086023547328ef44fd5fd87da3c250dc39, c6b80de19cdcad5b7e43fe7835588b629d847f75
- Source-data path: `figures/source/figure_data.json`
- Caption: Record-wise 분할 뒤 Train·Validation으로 MATLAB→LTspice→XMODEL Front End와 Digital RTL을 설계·검증하고, 설계 잠금 뒤 Held-out Test를 최초 1회 사용한 다음 구현·통합 등가성 검증으로 이어지는 전체 workflow
- Evidence scope: data-separated portrait workflow with one pre-lock digital correction loop and a one-time locked final test
- Limitations: the post-lock implementation and integration stages verify equivalence and do not permit model, threshold, or structural retuning

## FIG-03

- File: `figures/final/FIG-03_ownership_handoff.svg`
- Owner: 양건(편집)
- Source files: `source_of_truth/ownership_matrix.csv`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192, INTEGRATED_LTSPICE_2026-07-19, 4756a5086023547328ef44fd5fd87da3c250dc39, c6b80de19cdcad5b7e43fe7835588b629d847f75
- Source-data path: `figures/source/figure_data.json`
- Caption: Contributor ownership과 handoff
- Evidence scope: ownership
- Limitations: collaboration does not transfer implementation ownership

## FIG-04

- File: `figures/final/FIG-04_analog_validation_flow.svg`
- Owner: 양건(통합 편집)
- Source files: `figures/final/SPICE-03_matlab_ltspice_afe_response.png`, `figures/final/SPICE-04_matlab_ltspice_notch_response.png`, `figures/final/SPICE-05_xmodel_ltspice_adc_waveform_full.png`, `figures/final/SPICE-08_xmodel_ltspice_adc_error_histogram.png`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192, INTEGRATED_LTSPICE_2026-07-19, 4756a5086023547328ef44fd5fd87da3c250dc39, INTEGRATED
- Source-data path: `figures/source/figure_data.json`
- Caption: MATLAB–LTspice 주파수 응답 비교와 LTspice–XMODEL ADC 출력 비교의 아날로그 검증 흐름
- Evidence scope: two-stage analog model comparison
- Limitations: model- and schematic-level simulation evidence; not physical PCB or silicon measurement

## VAL-02

- File: `figures/final/VAL-02_digital_validation_flow.svg`
- Owner: 양건(통합 편집)
- Source files: `components/digital_accelerator/reports/final/xsim_locked_model_predictions.csv`, `benchmarks/accelerator_benefit/results/post_benchmark_equivalence.json`, `components/digital_accelerator/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv`, `components/digital_accelerator/sim/tb_snn_ecg_axi_smoke.v`, `components/digital_accelerator/sim/tb_axi_lite_axis_sample_feeder.v`
- Source commits: c6b80de19cdcad5b7e43fe7835588b629d847f75, 09e4d840827ad20856f5e23be4743ddd01565e30, INTEGRATED
- Source-data path: `figures/source/figure_data.json`
- Caption: Python과 Exact C++ 기준을 RTL/XSim에 비교한 뒤 Full-top 제어와 AXI/IP 인터페이스로 확장하는 디지털 검증 흐름
- Evidence scope: digital functional and interface verification sequence
- Limitations: AXI/IP smoke-test source exists; a report-facing rerun transcript and waveform remain to be captured

## VAL-03

- File: `figures/final/VAL-03_analog_digital_integration_flow.svg`
- Owner: 양건(통합 편집)
- Source files: `components/afe_xmodel/docs/integration_latest/afe36_sha256_bitidentity.csv`, `components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv`
- Source commits: 4756a5086023547328ef44fd5fd87da3c250dc39, c6b80de19cdcad5b7e43fe7835588b629d847f75, INTEGRATED
- Source-data path: `figures/source/figure_data.json`
- Caption: XMODEL AFE·ADC의 signed 12-bit 출력이 Digital RTL/XSim 최종 상태까지 이어지는 아날로그–디지털 통합 검증 흐름
- Evidence scope: 36-case XMODEL-to-RTL handoff and end-to-end equivalence
- Limitations: model-based AFE and RTL simulation evidence; not physical analog acquisition or clinical validation

## FIG-05

- File: `figures/final/FIG-05_strict_recordwise_protocol.svg`
- Owner: 양건
- Source files: `components/digital_accelerator/reports/final/final_metrics.json`
- Source commits: c6b80de19cdcad5b7e43fe7835588b629d847f75
- Source-data path: `figures/source/figure_data.json`
- Caption: Strict source-record-wise evaluation protocol
- Evidence scope: evaluation protocol
- Limitations: does not solve database-class confounding

## FIG-06

- File: `figures/final/FIG-06_matlab_nominal_summary.svg`
- Owner: 서민우
- Source files: `components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_dynamic_range_headroom_summary.csv`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192
- Source-data path: `figures/source/figure_data.json`
- Caption: MATLAB representative nominal clipping/headroom
- Evidence scope: four selected nominal 60-second records
- Limitations: not physical measurement

## FIG-07

- File: `figures/final/FIG-07_xmodel_scope.svg`
- Owner: 이수환
- Source files: `components/afe_xmodel/docs/afe_stress/AFE_xmodel_verification.md`
- Source commits: 4756a5086023547328ef44fd5fd87da3c250dc39
- Source-data path: `figures/source/figure_data.json`
- Caption: XMODEL waveform/stress/integration scope
- Evidence scope: model-based verification
- Limitations: not transistor/post-layout/PCB/silicon

## FIG-08

- File: `figures/final/FIG-08_signed_stream_handoff.svg`
- Owner: 이수환
- Source files: `components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv`
- Source commits: 4756a5086023547328ef44fd5fd87da3c250dc39
- Source-data path: `figures/source/figure_data.json`
- Caption: Signed-stream SHA256와 canonical output identity
- Evidence scope: 36 final-test chunks
- Limitations: identity is not label accuracy

## FIG-09

- File: `figures/final/FIG-09_digital_validation_hierarchy.svg`
- Owner: 양건
- Source files: `components/digital_accelerator/reports/final/final_metrics.json`
- Source commits: c6b80de19cdcad5b7e43fe7835588b629d847f75
- Source-data path: `figures/source/figure_data.json`
- Caption: Digital validation hierarchy
- Evidence scope: integer reference through board replay
- Limitations: physical analog not included

## FIG-10

- File: `figures/final/FIG-10_classification_summary.svg`
- Owner: 양건
- Source files: `components/digital_accelerator/reports/final/final_metrics.json`
- Source commits: c6b80de19cdcad5b7e43fe7835588b629d847f75
- Source-data path: `figures/source/figure_data.json`
- Caption: Locked classification results
- Evidence scope: final-test and model-selection metrics
- Limitations: public-dataset engineering result

## FIG-11

- File: `figures/final/FIG-11_confounding_claim_boundary.svg`
- Owner: 양건(편집)
- Source files: `docs/DATASET_DOMAIN_CONFOUNDING_KR.md`
- Source commits: INTEGRATED
- Source-data path: `figures/source/figure_data.json`
- Caption: Database-class confounding and claim boundary
- Evidence scope: generalization interpretation
- Limitations: does not invalidate RTL/IP evidence

## FIG-12

- File: `figures/final/FIG-12_digital_processing_flow.svg`
- Owner: 양건(편집)
- Source files: `figures/source/approved_svg/FIG-12_digital_processing_flow.svg`, `components/digital_accelerator/rtl/snn_ecg_30min_final_top.v`, `components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v`, `components/digital_accelerator/rtl/core/qrs_lif_detector.v`, `components/digital_accelerator/rtl/final_membrane_layer.v`, `tables/streaming_state_inventory.csv`
- Source commits: c6b80de19cdcad5b7e43fe7835588b629d847f75
- Source-data path: `figures/source/figure_data.json`
- Caption: Signed ECG가 사건·QRS 검출을 거쳐 rhythm·morphology 경로로 분기되고, 네 morphology 증거가 서로 독립적인 병렬 경로로 class scoring에 합류한 뒤 60초 Snapshot 30개가 Final Membrane으로 누적되는 digital processing flow
- Evidence scope: reader-facing digital architecture with four parallel morphology evidence paths and 30-Snapshot accumulation
- Limitations: conceptual grouping, not literal post-synthesis netlist connectivity; block internals remain in the body

## FIG-15

- File: `figures/final/FIG-15_afe_adc_signal_flow.svg`
- Owner: 양건(통합 편집)
- Source files: `figures/source/approved_svg/FIG-15_afe_adc_signal_flow.svg`, `validation/afe_ltspice_xmodel_aligned/schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc`, `components/matlab_prevalidation/matlab_afe_validation/docs/afe_adc_parameter_reference.md`, `components/afe_xmodel/analog/ecg_afe_xmodel.sv`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192, INTEGRATED_LTSPICE_2026-07-19, 4756a5086023547328ef44fd5fd87da3c250dc39, INTEGRATED
- Source-data path: `figures/source/figure_data.json`
- Caption: 차동 ECG가 HPF·IA·Active Twin-T notch·LPF와 buffer·12-bit ADC를 통과해 signed stream으로 인계되고, XMODEL 비이상성은 실제 고정 검증 범위에 맞춘 점선 경로로 주입되는 AFE·ADC signal flow
- Evidence scope: finite GBW across active op-amp stages, VOS stress at the IA input pair, and one ADC code-boundary injection
- Limitations: reader-facing architecture; use SPICE-02 for the actual LTspice graphical schematic; neither is physical PCB or silicon evidence

## FIG-RTL

- File: `figures/final/FIG-RTL_top_with_snapshot_expansion.svg`
- Owner: 양건(통합 편집)
- Source files: `figures/source/approved_svg/FIG-RTL_top_with_snapshot_expansion.svg`, `artifacts/rtl_elaborated_schematic/FIG-RTL-A_top_hierarchy.svg`, `artifacts/rtl_elaborated_schematic/FIG-RTL-B_snapshot_core_hierarchy.svg`, `artifacts/rtl_elaborated_schematic/hierarchy_report.txt`
- Source commits: c6b80de19cdcad5b7e43fe7835588b629d847f75, INTEGRATED
- Source-data path: `figures/source/figure_data.json`
- Caption: Pure RTL top hierarchy와 Snapshot core 확장
- Evidence scope: Vivado RTL Elaborated Schematic 기반 hierarchy reconstruction
- Limitations: module instances and connectivity retained; not a synthesized gate-level or post-route netlist

## MAT-01

- File: `figures/final/MAT-01_afe_chain_overview.png`
- Owner: 서민우
- Source files: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_afe_chain_overview.png`, `components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192
- Source-data path: `figures/source/figure_data.json`
- Caption: MATLAB nominal AFE+ADC chain overview
- Evidence scope: fixed MATLAB nominal reference figure
- Limitations: not transistor-level, PCB, silicon, post-layout, or MATLAB-LTspice-XMODEL bit-exact evidence

## MAT-02

- File: `figures/final/MAT-02_total_frequency_response.png`
- Owner: 서민우
- Source files: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_total_frequency_response.png`, `components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192
- Source-data path: `figures/source/figure_data.json`
- Caption: MATLAB nominal total frequency-response reference
- Evidence scope: fixed MATLAB nominal reference figure
- Limitations: not transistor-level, PCB, silicon, post-layout, or MATLAB-LTspice-XMODEL bit-exact evidence

## MAT-03

- File: `figures/final/MAT-03_notch_dense_sweep.png`
- Owner: 서민우
- Source files: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_notch_dense_sweep.png`, `components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192
- Source-data path: `figures/source/figure_data.json`
- Caption: Active Twin-T dense 60 Hz sweep
- Evidence scope: fixed MATLAB nominal reference figure
- Limitations: not transistor-level, PCB, silicon, post-layout, or MATLAB-LTspice-XMODEL bit-exact evidence

## MAT-04

- File: `figures/final/MAT-04_dynamic_range_headroom.png`
- Owner: 서민우
- Source files: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_dynamic_range_headroom.png`, `components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192
- Source-data path: `figures/source/figure_data.json`
- Caption: Representative ADC rail headroom
- Evidence scope: fixed MATLAB nominal reference figure
- Limitations: not transistor-level, PCB, silicon, post-layout, or MATLAB-LTspice-XMODEL bit-exact evidence

## MAT-05

- File: `figures/final/MAT-05_adc_code_distribution.png`
- Owner: 서민우
- Source files: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_adc_code_distribution.png`, `components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192
- Source-data path: `figures/source/figure_data.json`
- Caption: Representative offset-binary ADC-code distribution
- Evidence scope: fixed MATLAB nominal reference figure
- Limitations: not transistor-level, PCB, silicon, post-layout, or MATLAB-LTspice-XMODEL bit-exact evidence

## MAT-06

- File: `figures/final/MAT-06_reference_vector_handoff.png`
- Owner: 서민우
- Source files: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_reference_vector_handoff.png`, `components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192
- Source-data path: `figures/source/figure_data.json`
- Caption: MATLAB reference-vector handoff
- Evidence scope: fixed MATLAB nominal reference figure
- Limitations: not transistor-level, PCB, silicon, post-layout, or MATLAB-LTspice-XMODEL bit-exact evidence

## MAT-07

- File: `figures/final/MAT-07_prevalidation_flow.png`
- Owner: 서민우
- Source files: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_matlab_prevalidation_flow.png`, `components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md`
- Source commits: 907f7e1f081a9d6a5703a32095d962143315a192
- Source-data path: `figures/source/figure_data.json`
- Caption: MATLAB nominal pre-validation role
- Evidence scope: fixed MATLAB nominal reference figure
- Limitations: not transistor-level, PCB, silicon, post-layout, or MATLAB-LTspice-XMODEL bit-exact evidence

## SPICE-01

- File: `figures/final/SPICE-01_analog_afe_architecture.svg`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: AFE+ADC architecture and non-ideality injection points
- Evidence scope: schematic/behavioral architecture
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## SPICE-02

- File: `figures/final/SPICE-02_ltspice_xmodel_aligned_schematic.jpg`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: XMODEL-aligned LTspice AFE+ADC/S&H graphical schematic
- Evidence scope: actual LTspice schematic capture
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## SPICE-03

- File: `figures/final/SPICE-03_matlab_ltspice_afe_response.png`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: MATLAB and LTspice full AFE frequency-response comparison
- Evidence scope: MATLAB-to-schematic design-intent comparison
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## SPICE-04

- File: `figures/final/SPICE-04_matlab_ltspice_notch_response.png`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: MATLAB and LTspice active Twin-T notch comparison
- Evidence scope: 60 Hz dense response comparison
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## SPICE-05

- File: `figures/final/SPICE-05_xmodel_ltspice_adc_waveform_full.png`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: Full ten-second XMODEL-LTspice ADC waveform overlay
- Evidence scope: patient100 nominal 10-second comparison
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## SPICE-06

- File: `figures/final/SPICE-06_xmodel_ltspice_adc_waveform_zoom.png`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: Two-to-three-second XMODEL-LTspice ADC waveform zoom
- Evidence scope: QRS-region nominal comparison
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## SPICE-07

- File: `figures/final/SPICE-07_xmodel_ltspice_adc_error.png`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: Per-sample LTspice S/H minus XMODEL ADC error
- Evidence scope: ten-second code error
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## SPICE-08

- File: `figures/final/SPICE-08_xmodel_ltspice_adc_error_histogram.png`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: XMODEL-LTspice ADC error histogram
- Evidence scope: ten-second code-error distribution
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## SPICE-09

- File: `figures/final/SPICE-09_xmodel_ltspice_adc_agreement.png`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: Cumulative ADC-code agreement by error range
- Evidence scope: exact through plus-or-minus 10 LSB coverage
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## SPICE-10

- File: `figures/final/SPICE-10_xmodel_ltspice_adc_metrics.png`
- Owner: 이수환(팀 handoff)
- Source files: `figures/source/team_handoff_analog/README.md`, `validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv`
- Source commits: INTEGRATED_LTSPICE_2026-07-19
- Source-data path: `figures/source/figure_data.json`
- Caption: Quantitative XMODEL-LTspice ADC comparison
- Evidence scope: full and settled nominal metrics
- Limitations: team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement

## FIG-P05

- File: `figures/publication/FIG-P05_vivado_implementation/device_view_annotated_publication.svg`
- Owner: 양건(통합 편집)
- Source files: `figures/publication/FIG-P05_vivado_implementation/export_vivado_figures.tcl`, `figures/publication/FIG-P05_vivado_implementation/extract_hierarchy_placement.tcl`, `figures/publication/FIG-P05_vivado_implementation/build_annotated_device_figure.py`, `figures/publication/FIG-P05_vivado_implementation/build_vector_publication.py`, `figures/publication/FIG-P05_vivado_implementation/evidence_paths.md`, `figures/publication/FIG-P05_vivado_implementation/device_view_full_original.png`, `figures/publication/FIG-P05_vivado_implementation/hierarchy_tile_occupancy.csv`, `figures/publication/FIG-P05_vivado_implementation/placed_tile_occupancy.csv`, `figures/publication/FIG-P05_vivado_implementation/microblaze_block_design_vivado_native.pdf`, `figures/publication/FIG-P05_vivado_implementation/worst_setup_path_vivado_native.pdf`, `components/digital_accelerator/results/board_replay/microblaze_full_replay/reports/system_timing_summary.rpt`, `components/digital_accelerator/results/board_replay/microblaze_full_replay/reports/system_utilization_hier.rpt`
- Source commits: c6b80de19cdcad5b7e43fe7835588b629d847f75, INTEGRATED
- Source-data path: `figures/source/figure_data.json`
- Caption: Actual post-route Device View with hierarchy placement overlay, Vivado native MicroBlaze Block Design와 worst setup path
- Evidence scope: Vivado 2020.2, xc7a100tcsg324-1, actual Device View plus routed hierarchy/timing evidence
- Limitations: Hierarchy colors use placed primitive coordinates and are not pblock boundaries; not ASIC layout
