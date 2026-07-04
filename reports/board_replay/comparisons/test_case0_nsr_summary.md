# test_case0_nsr board full-record replay summary

- mem: `C:\Users\YangGeon\SNN ECG Classifier\fullrec_afe_30min_annotation_valid_balanced\test\NSR\16786\16786_30min_w035.mem`
- expected source: `C:\Users\YangGeon\SNN ECG Classifier\results\final_membrane_v2_snn\xsim_snn_ecg_v2_test_first10_predictions.csv`
- transcript: `C:\Users\YangGeon\SNN ECG Classifier\reports\board_replay\transcripts\test_case0_nsr_uart_full_replay.txt`
- comparison: `C:\Users\YangGeon\SNN ECG Classifier\reports\board_replay\comparisons\test_case0_nsr_expected_vs_board.csv`
- board internal pass marker: `True`
- expected-vs-board match: `True`

| metric | value |
|---|---:|
| samples_received | 1800000 |
| samples_sent_to_ip | 1800000 |
| samples_accepted | 1800000 |
| samples_consumed | 1800000 |
| snapshot_count | 30 |
| decision_count | 1 |
| final_pred | 0 |
| final_mem_nsr | 31 |
| final_mem_chf | 0 |
| final_mem_arr | 1 |
| final_mem_aff | 0 |
| snn_error | 0 |
| feeder_error | 0 |
