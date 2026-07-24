# Finalized graphical schematic change record

## Deliverable

`schematics/nominal/FULL_AFE_ADC_SH_validated.asc` is the validation-only graphical LTspice schematic derived from the read-only source. It can be opened directly in LTspice. Its SHA256 is recorded in `tables/finalized_artifact_sha256.txt`.

## Exact topology correction

The source wire `WIRE 2848 80 1120 80` joined the U5 bootstrap input/divider branch to the global positive-supply trunk. The finalized copy omits this wire and adds `FLAG 1120 80 VPLUS` to the supply trunk while retaining `FLAG 2944 256 K_DIV` on the divider node.

LTspice 26.0.1 generated-netlist checks confirm:

- `V1 VPLUS 0 5`.
- U1-U6 positive-supply pins use `VPLUS`.
- `R15 K_DIV LPF_IN` and `R16 K_DIV 0`.
- U5 has non-inverting input `K_DIV`, inverting input `VK`, positive supply `VPLUS`, and output `VK`.
- No independent voltage/behavioral source clamps `K_DIV` to ground or +5 V.

No component value, signal-path polarity, HPF/IA/Twin-T/LPF component, switch model, hold capacitor, leakage resistor, ADC expression, or original source file was changed.

## Final schematic directives

- Patient transient: `.tran 0 10 0 5u`.
- Compression disabled: `.options plotwinsize=0`.
- Required stage, S/H, ADC, K_DIV, and VK nodes are explicitly saved.
- PWL filename remains `patient100_ecg_10s.txt`, with a validation copy in the same directory.

## Regression result

The finalized ASC itself completed the 10 s run in LTspice 26.0.1 with direct Newton operating-point success and no fatal/convergence signature. Direct AC decks were derived from its LTspice-generated netlist.

- HPF cutoff: 0.491817 Hz.
- IA gain at 10 Hz: 200.959 V/V.
- Notch at 60 Hz: -83.5465 dB; minimum 59.9995 Hz and -95.4969 dB.
- LPF cutoff: 150.211 Hz.
- Bootstrap K_DIV and VK AC ratios at 10 Hz: 0.949991 and 0.949990 V/V relative to LPF_IN.
- Settled AFE_OUT: -0.0537732 to +0.246147 V; no continuous or sampled clipping.
- T/H acquisition error: 0.15621 LSB maximum; hold droop 0.02706 LSB maximum.
- 10,000 valid ADC codes; zero code mismatch versus the prior intent-aligned reference.

The analog valid-phase differences versus the independently constructed intent-aligned deck were at most 18.143 uV on AFE_OUT and 77.611 uV on ADC_HOLD. These are solver trajectory/netlist-order differences below one endpoint-convention LSB and did not change any exported code.
