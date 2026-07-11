setws "C:/Users/YangGeon/_snn_ecg_accelerator_benchmark_app_work/vitis_workspace"
platform create -name snn_ecg_mb_full_replay_platform -hw "C:/Users/YangGeon/_snn_ecg_accelerator_benchmark_app_work/hw/snn_ecg_mb_full_replay.xsa" -proc microblaze_0 -os standalone
platform active snn_ecg_mb_full_replay_platform
domain active standalone_domain
catch {bsp config stdin axi_uartlite_0} stdin_msg
if {$stdin_msg ne ""} {puts "WARN BSP stdin config: $stdin_msg"}
catch {bsp config stdout axi_uartlite_0} stdout_msg
if {$stdout_msg ne ""} {puts "WARN BSP stdout config: $stdout_msg"}
catch {bsp regenerate} bsp_msg
if {$bsp_msg ne ""} {puts "WARN BSP regenerate: $bsp_msg"}
platform generate
app create -name snn_ecg_mb_full_replay_benchmark -platform snn_ecg_mb_full_replay_platform -domain standalone_domain -template {Empty Application}
importsources -name snn_ecg_mb_full_replay_benchmark -path "C:/Users/YangGeon/_snn_ecg_accelerator_benchmark_app_work/src"
app build -name snn_ecg_mb_full_replay_benchmark
exit
