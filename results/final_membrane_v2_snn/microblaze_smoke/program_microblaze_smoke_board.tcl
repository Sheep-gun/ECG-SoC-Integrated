connect -url tcp:127.0.0.1:3121
puts "XSDB targets after connect:"
targets
targets -set -nocase -filter {name =~ "*xc7a100t*"}
fpga -file "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.bit"
after 1000
puts "XSDB targets after fpga:"
targets
targets -set -nocase -filter {name =~ "*MicroBlaze*#0"}
rst -processor
dow "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/microblaze_smoke/vitis_workspace/snn_ecg_mb_smoke_app/Debug/snn_ecg_mb_smoke_app.elf"
con
puts "SNN_ECG_MB_XSDB_PROGRAM_DONE"
exit
