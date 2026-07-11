SNN ECG Model S 통합 프로젝트 안내

팀원에게 전달할 때는 이 폴더 전체를 압축하면 됩니다.

압축 대상:
C:\Users\YangGeon\SNN_ECG_RESTORE_MODEL_S

Vivado에서 열어야 할 단일 통합 프로젝트:
C:\Users\YangGeon\SNN_ECG_RESTORE_MODEL_S\vivado_project\SNN_ECG_ModelS_Unified\SNN_ECG_ModelS_Unified.xpr

합성/비트스트림용 top module:
nexys_a7_model_s_smoke_top

기본 simulation top:
tb_snn_ecg_3feat_record_strict_test

중요 폴더:
SNN_ECG.srcs
- Model S RTL source, board top, testbench가 들어 있습니다.

constraints
- Nexys A7 board용 XDC가 들어 있습니다.

person_data_record_split_strict_varlen
- strict record-wise train/validation/test dataset입니다.

bitstreams
- 이미 생성된 Nexys A7 demo bitstream이 들어 있습니다.

scripts
- Vivado/XSim 실행 스크립트가 들어 있습니다.

기존 legacy Vivado 프로젝트:
vivado_project\SNN_ECG_ModelS_Restore
- core-only 복구/검증용 프로젝트였습니다.
- 보드 핀 constraint가 없는 core top이라 Project Summary 기준으로 보면 안 됩니다.

vivado_project\SNN_ECG_ModelS_BoardSmoke
- 보드 smoke demo 전용으로 먼저 만들었던 프로젝트입니다.
- 이제는 통합 프로젝트 SNN_ECG_ModelS_Unified를 우선 사용하면 됩니다.

정리:
팀원이 Vivado에서 직접 열 프로젝트는 SNN_ECG_ModelS_Unified.xpr 하나입니다.
단, RTL/source/dataset은 프로젝트 폴더 안이 아니라 이 루트 폴더의 공통 경로를 참조하므로, 반드시 SNN_ECG_RESTORE_MODEL_S 폴더 전체를 압축해서 전달해야 합니다.
