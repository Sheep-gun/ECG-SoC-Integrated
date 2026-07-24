# LTspice schematic audit

## Audit basis

The only original LTspice schematic found was `FULL_AFE_ADC_SH.asc`; it is therefore the top-level implementation. It references `patient100_ecg_10s.txt` and contains all required stage and ADC labels. The authoritative connectivity evidence is LTspice 26.0.1's generated netlist at `schematics/nominal/FULL_AFE_ADC_SH_original_snapshot.net`. The original files were not edited.

## Executive finding

The HPF, three-op-amp IA, Twin-T component ratios, LPF, S/H, and behavioral ADC equations match the documented component intent. One major topology defect exists in the source schematic: `K_DIV` is simultaneously the +5 V supply rail and the R15/R16 bootstrap-divider midpoint. Ideal source V1 therefore clamps `K_DIV` to +5 V. Consequently the documented 0.95 active bootstrap is not implemented as an AC feedback divider; U5 follows a fixed +5 V input and operates near its upper rail. All report-eligible nominal figures are therefore separated into:

- `as_implemented`: exact source topology, including the K_DIV/+5 collision.
- `intent_aligned`: validation-only copy/netlist in which op-amp V+ uses a separate `VPLUS` node while K_DIV remains the R15/R16 midpoint. No original file was changed.
- `finalized_graphical_asc`: LTspice-openable `FULL_AFE_ADC_SH_validated.asc` with the same correction applied to the actual drawing. Its generated netlist and direct AC/10 s transient regression are in `tables/finalized_schematic_regression.csv`.

## A. Input

- V3 is a differential source from `INP_RAW` to `INN_RAW`: `PWL file=patient100_ecg_10s.txt AC 1`.
- R10 and R11 provide symmetric 1 Gohm DC returns to ground.
- A positive file voltage means `V(INP_RAW,INN_RAW)>0`. The HPF pair and U3 difference stage preserve this differential sign, so positive HPF differential events produce positive `IA_OUT`; after the offset-binary conversion they increase `ADC_SIGNED`.

## B. Differential HPF

- Positive channel: C1=33 nF series, R1=10 Mohm shunt, output `HPF_P`.
- Negative channel: C2=33 nF series, R2=10 Mohm shunt, output `HPF_N`.
- The channels are nominally symmetric. The ideal single-pole expression gives `1/(2*pi*10 Mohm*33 nF) = 0.48229 Hz`; the simulated differential cutoff is tabulated independently.

## C. Three-op-amp IA

- U1 non-inverting input is `HPF_P`; U2 non-inverting input is `HPF_N`.
- R3=R4=100 kohm feedback and R9=1 kohm gain-setting give `1+2R/Rg=201` for the first differential stage.
- U3 uses R5=R6=R7=R8=10 kohm. R8 is a real negative-feedback path from `IA_OUT` to the inverting input.
- U3 forms `U1_OUT-U2_OUT`, hence `IA_OUT` has the same sign as `V(HPF_P,HPF_N)`.

## D. Active Twin-T notch

- `NOTCH_IN` aliases `IA_OUT`; `NOTCH_OUT` aliases `LPF_IN`.
- Resistive T: R12=R13=26.526 kohm, midpoint N004, C3=200 nF to VK.
- Capacitive T: C4=C5=100 nF, midpoint N007, R14=13.263 kohm to VK.
- The two T-network midpoints are not shorted. `NOTCH_SENSE` and `VK` are distinct.
- U4 is wired as a voltage follower.
- R15=5 kohm and R16=95 kohm nominally imply `95/(5+95)=0.95`, and the component expression gives about 59.9995 Hz.
- Defect: the divider midpoint `K_DIV` is also V1's +5 V supply node. The source topology therefore lacks the intended small-signal bootstrap action. The exact topology measured -61.548 dB at 60 Hz; the validation-only intent-aligned topology measured -83.546 dB.

## E. LPF and buffer

- R17=1 kohm from `NOTCH_OUT/LPF_IN` to `LPF_NODE`, C6=1.06 uF to ground.
- U6 is a follower from `LPF_NODE` to `AFE_OUT`, isolating the passive pole from the S/H load.
- The component expression is about 150.146 Hz.

## F. Track-and-Hold

- S1 signal path is `AFE_OUT` to `ADC_HOLD`; control is `CLK` relative to ground.
- `SW_ADC`: Ron=1 ohm, Roff=1 Gohm, Vt=2.5 V, Vh=0.1 V.
- C7=10 nF and R18=1 Gohm give a defined held node and leakage path.
- CLK is `PULSE(0 5 0 1u 1u 100u 1m)`. Threshold analysis gives track start 0.52 us, track end 101.52 us, reliably-off reference 102 us, and this package samples at the fixed 500 us hold phase.

## G. Behavioral ADC

- B1 reads `ADC_HOLD` and creates distinct node `ADC_CLIP` with +/-1.65 V limiting.
- B2 reads `ADC_CLIP` and creates distinct node `ADC_CODE` using `floor((x+1.65)/3.3*4095)`, bounded to 0..4095.
- B3 reads `ADC_CODE` and creates distinct node `ADC_SIGNED=ADC_CODE-2048`.
- The three sources are not wire-connected in series and their output nodes are distinct.
- `ADC_SIGNED` is a behavioral voltage representation of an integer, not twelve bit lines. The circuit is not a physical or transistor-level SAR ADC.

## H. Op-amp model

U1-U6 use LTspice `UniversalOpamp2`, level 2. The generated instances contain: Avol=1Meg V/V, GBW=10Meg Hz, Slew=10Meg V/s (10 V/us), Ilimit=25 mA, Rail=0 V, Vos=0 V, En/Enk/In/Ink=0, and Rin=500 Mohm. The installed `UniversalOpAmp2.lib` sets Rout=100 Mohm and computes `Cout=Avol/(GBW*2*pi*Rout)`, about 159.15 pF for these values; rail limiting is implemented by level-2 switches with Rail=0 V. The library and exact model source are hashed/identified in `original_sha256.txt` and `environment.txt`. This is a generic behavioral output model rather than a selected physical device, so these parameters do not establish a particular op-amp's silicon behavior.

## Original directive and convergence observation

The source schematic contains only `.tran 0 20m 0 10u`; it does not itself run the report's full 10 s patient interval or any AC analysis. The original copied 20 ms run completed after direct Newton failed and Gmin stepping recovered. This is recorded as a recovered operating-point warning, not hidden as a clean direct-Newton start. Generated intent-aligned runs completed without fatal, singular-matrix, or timestep-too-small errors.

Detailed item status, node aliases, and reference-designator mappings are in `report_vs_schematic.csv`, `node_map.csv`, and `component_crosswalk.csv`.
