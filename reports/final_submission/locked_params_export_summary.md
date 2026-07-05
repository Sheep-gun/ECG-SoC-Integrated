# Locked Final Membrane Parameter Export Summary

| 항목 | 값 |
|---|---|
| run_id | `recordwise_resplit_seed20260808` |
| split_seed | `20260808` |
| locked_candidate | `structural_guarded_silent_aff_1008710` |
| locked_family | `F1_F6_F10_guarded_rescue_silent_aff` |
| locked_params_hash | `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b` |
| base_candidate | `balanced_0202881` |
| base_params_hash | `be2afbcba95a0edda4c77713217ceac5e83ae3afd6a71d98a6da065ebe2e631f` |
| RTL include | `rtl\strict_recordwise_locked_params.vh` |
| generated SV package | `rtl\generated\strict_recordwise_locked_params_pkg.sv` |
| RTL interface changed | `false` |

## 적용 범위

- `best_final_membrane_structural_grid_locked.json`을 source of truth로 사용한다.
- RTL은 `rtl/strict_recordwise_locked_params.vh`를 include하여 같은 정수 파라미터를 사용한다.
- Python 재검증은 JSON을 직접 읽고, RTL은 생성된 include를 사용한다.
- top-level port 및 AXI register map은 바뀌지 않는다.
