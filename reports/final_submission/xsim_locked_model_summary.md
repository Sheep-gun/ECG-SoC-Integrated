# XSim Locked Model Summary

| 항목 | 결과 |
|---|---|
| status | `pass` |
| split | `test` |
| case_count | `36` |
| final_pred_mismatch | `0` |
| final_mem_mismatch | `0` |
| predictions | `reports\final_submission\xsim_locked_model_predictions.csv` |
| mismatch | `reports\final_submission\xsim_locked_model_mismatch.csv` |
| xsim_log | `reports\final_submission\xsim_locked_model_work\xsim.log` |

## Interpretation

이 결과는 locked Final Membrane RTL 단독 계층이 Python golden과 동일한 snapshot evidence stream을 받을 때 final prediction 및 final membrane vector가 일치하는지 확인한다.
full top-level ECG stream XSim, Vivado implementation, Vitis board replay를 대체하지 않는다.
