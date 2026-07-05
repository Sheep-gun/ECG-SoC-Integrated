# Locked Model Consistency Check

## Result

| Check | Status | Evidence |
|---|---|---|
| Locked candidate name is consistent | PASS | `structural_guarded_silent_aff_1008710` appears in config, RTL header, reports, README/docs |
| Python locked params hash is recorded | PASS | `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b` |
| RTL generated params hash is recorded | PASS | `rtl/strict_recordwise_locked_params.vh` |
| Python metrics match locked artifact | PASS | train `61/68`, validation `32/32`, final_test `29/36`, record-majority `16/19`, `test_evaluation_count=1` |
| Final test excluded from selection/search/ChatGPT context | PASS | `reports/final_submission/python_locked_model_metrics.json` |
| RTL final membrane uses locked include | PASS | `rtl/final_membrane_layer.v` includes `strict_recordwise_locked_params.vh` |
| XSim vs Python | PASS | final_test 36 cases, final_pred mismatch `0`, final_mem mismatch `0` |
| Vivado pure RTL build after RTL update | PASS | bitstream exists, LUT/FF/BRAM/DSP `9719/5038/0/0`, WNS `8.184 ns`, power `0.099 W` |
| OOC/profile timing | PASS | LUT/FF/BRAM/DSP `9905/5769/0/0`, WNS `0.471 ns`, previous rdm->pred query reports `No timing paths found` |
| IP packaging | PASS | component.xml regenerated, locked header included, interface/register map unchanged |
| MicroBlaze full replay build | PASS | bitstream/XSA/ELF rebuilt, LUT/reg/BRAM/DSP `12485/8480/16/3`, WNS `0.294 ns` |
| Locked board UART replay | PASS/PARTIAL | NSR/CHF/ARR/AFF class-wise transcripts generated; final_pred 4/4 match, final_mem exact 2/4 |
| Locked class-wise board replay documented | PASS | NSR/CHF/ARR/AFF replay transcripts are present |
| Final reporting excludes old chunk-level benchmark | PASS | README/FINAL_REPORT/docs use locked strict record-wise metrics |
| Overclaim search | PASS | Risk-expression search returned no matches |
| `git diff --check` | PASS | Whitespace check passed |

## Verification Commands

```powershell
git diff --check
python -m py_compile tools\recordwise\export_params_for_rtl.py tools\recordwise\recheck_locked_model.py tools\recordwise\run_xsim_strict_recordwise.py scripts\build_snn_ecg_v2_bitstream.py scripts\package_snn_ecg_axi_ip.py scripts\impl_timing_10ns.py scripts\synth_profile_overhead.py scripts\build_microblaze_full_replay_system.py scripts\build_microblaze_full_replay_app.py tools\board_replay\send_full_record_uart.py
python tools\recordwise\recheck_locked_model.py
python tools\recordwise\run_xsim_strict_recordwise.py --split test
rg -n "<overclaim-risk-expression-list>" README.md FINAL_REPORT_KR.md docs reports/final_submission
rg -n "structural_guarded_silent_aff_1008710|89.71|100.00|80.56|84.21|test_evaluation_count|29/36|16/19" README.md FINAL_REPORT_KR.md docs reports/final_submission
```

## Remaining TODO

- Resolve CHF/ARR final_mem exact divergence with gap-injection XSim and sample-clock-enable audit.
- Optionally run the full final_test split as a board batch after the class-wise replay evidence.
