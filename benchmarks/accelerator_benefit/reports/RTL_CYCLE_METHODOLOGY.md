# RTL Cycle Methodology

The committed full-top XSim profile is used at canonical `sample_gap_cycles=2`. Host simulator wall time is not used. The implemented clock is 100 MHz from the 10.000 ns XDC constraint and the committed Vivado timing report.

For each case, active accelerator cycles are `prof_total_cycles - prof_input_wait_cycles`. The input-wait counter increments only while the core is in RUN, ready to accept a sample, and `sample_valid` is absent. Internal back-pressure cycles, snapshot/decision work, and non-RUN control overhead therefore remain in the active interval. Latency = active cycles / 100,000,000; throughput = 1,800,000 / latency; real-time margin = throughput / 1,000.

The XSim active result is 3601290 cycles (36.012900 ms), exactly matching all 36 board-counter differences. The canonical gap-inclusive XSim interval remains 54.012600 ms and is not used as no-stall core latency. All 36 rows validate 1,800,000 accepted samples, 30 windows, one decision, final_pred exact, and final_mem exact. Live ECG still requires 30 minutes to observe the decision window.
