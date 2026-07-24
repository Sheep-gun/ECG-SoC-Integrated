connect -url tcp:127.0.0.1:3121
puts "XSDB targets after connect:"
targets
targets -set -nocase -filter {name =~ "*xc7a100t*"}
fpga -file "<LOCAL_DIGITAL_REPOSITORY>/results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit"
after 1000
puts "XSDB targets after fpga:"
targets
targets -set -nocase -filter {name =~ "*MicroBlaze*#0"}
rst -processor
dow "<LOCAL_DIGITAL_REPOSITORY>/results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf"
con
puts "SNN_ECG_FULL_REPLAY_XSDB_PROGRAM_DONE"
exit
