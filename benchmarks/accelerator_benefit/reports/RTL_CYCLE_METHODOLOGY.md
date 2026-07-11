# RTL Cycle Methodology

The committed full-top XSim profile is used at canonical `sample_gap_cycles=2`. Host simulator wall time is not used. The implemented clock is 100 MHz from the 10.000 ns XDC constraint and the committed Vivado timing report.

For each case: latency = cycles / 100,000,000; throughput = 1,800,000 / latency; real-time margin = throughput / 1,000. All 36 rows validate 1,800,000 accepted samples, 30 windows, one decision, final_pred exact, and final_mem exact.

Stored-data processing latency is 54.012600 ms. Live ECG still requires 30 minutes to observe the decision window.
