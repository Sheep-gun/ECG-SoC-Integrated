# Nexys A7 Idle/Active Differential Power Protocol

## Current evidence boundary

Vivado `report_power` estimates FPGA on-chip power; JTAG/XSDB reports target
state but does not measure Nexys A7 supply current. No external power meter or
rail-current instrument is available in this workspace, so physical board
power remains **NOT MEASURED**.

The Digilent Nexys A7 reference manual documents USB-JTAG or external-supply
board power through JP3 and describes the 5 V input as a whole-board supply; it
does not expose a calibrated software rail-power monitor:
<https://digilent.com/reference/_media/reference/programmable-logic/nexys-a7/nexys-a7_rm.pdf>.

## Required equipment

- calibrated inline USB power meter with data passthrough, or a bench supply
  plus current measurement with adequate transient bandwidth;
- preferably a current shunt/current probe on each rail of interest if the
  objective is FPGA-core IP power rather than whole-board input power;
- a fixed ambient condition and a warm-up interval;
- the committed BIT/ELF hashes and UART transcript capture.

An inline USB reading is whole-board input power and includes regulator loss,
USB/JTAG circuitry, LEDs, memories, and static FPGA power. It must not be
reported as accelerator on-chip power.

## Three board states

1. **Idle**: programmed bitstream and firmware, accelerator held idle after
   initialization, UART quiescent.
2. **Streaming 1 kS/s**: real ECG delivered at one sample per millisecond for
   a steady measurement interval.
3. **Preloaded burst**: the same ECG preloaded into BRAM/DDR or streamed from a
   local feeder, with UART excluded from the timed/averaged active window.

For each state, collect at least 60 seconds after thermal stabilization and
repeat at least five times. Record mean, median, standard deviation, min/max,
ambient temperature and supply voltage.

## Derived quantities

Let `P_idle`, `P_stream`, and `P_burst` be measured whole-board input powers.

- streaming incremental board power: `P_stream - P_idle`
- burst incremental board power: `P_burst - P_idle`
- burst incremental energy/decision: `(P_burst - P_idle) * active_latency`
- total board energy/decision: `P_burst * active_latency`

Report both incremental and total results. Do not subtract the idle baseline
from a Vivado on-chip estimate or combine rail measurements with a different
clock/bitstream.

## Capture schema

Use `board_rail_measurement_template.csv`. The template intentionally contains
no invented current or power readings.
