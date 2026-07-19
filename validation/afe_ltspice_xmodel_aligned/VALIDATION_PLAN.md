# Validation plan and execution state

## Variants

1. `as_implemented`: exact connectivity generated from the read-only source schematic.
2. `intent_aligned`: the same component network with only the positive supply renamed from `K_DIV` to `VPLUS`, restoring the documented R15/R16/U5 bootstrap topology.
3. `stress_*`: parameterized intent-aligned copies using exact fixed-XMODEL case levels where available.
4. `finalized_graphical_asc`: LTspice-openable graphical copy with VPLUS/K_DIV separated and full patient directives.

## Planned and completed sequence

| Phase | Method | State | Primary evidence |
|---|---|---|---|
| Preflight | recursive inventory, SHA256, environment and executable probing | COMPLETE | `source_manifest.csv`, `original_sha256.txt`, `environment.txt` |
| Schematic audit | LTspice-generated netlist plus report cross-check | COMPLETE | `audit/` |
| Nominal AC | independent differential AC testbenches and fine notch sweep | COMPLETE | `tables/nominal_ac_metrics.csv` |
| Patient transient | short AFE, short S/H, 10 s runs, 10/5/2.5 us convergence probes | COMPLETE | `tables/nominal_transient_metrics.csv`, `tables/timestep_convergence.csv` |
| S/H and ADC | threshold-defined phases, acquisition/droop extraction, DC/plateau mapping | COMPLETE | `tables/track_hold_metrics.csv`, `tables/adc_mapping_metrics.csv` |
| MATLAB fixed reference | exact commit, MATLAB R2026a execution, zero/best-lag diagnostics | COMPLETE | `tables/matlab_ltspice_comparison.csv` |
| Fixed-XMODEL stress | exact case definitions, hooks, representative deterministic runs | PARTIAL_EXECUTION | `tables/stress_matrix.csv`, `tables/stress_results.csv` |
| Report package | Korean drafts, captions, limitations, evidence paths | COMPLETE | `report/` |
| Final graphical ASC | graphical topology correction, generated-netlist audit, direct AC/transient regression | COMPLETE | `tables/finalized_schematic_regression.csv` |

## Quantitative conventions

- No unstated tolerance is introduced. Target/deviation values use status `MEASURED`.
- AC crossings use scripted interpolation; notch minima use explicitly recorded fine search grids.
- Patient transient is split into 0-1 s initialization and 1-10 s settled windows. Stress transient uses 2-5 s because the generated representative stress runs are 5 s long.
- S/H valid code is sampled at 500 us in each 1 ms period, after the switch is reliably off at about 102 us.
- ADC LSB is `3.3/4095 V`.
- `ADC_SIGNED` is a behavioral voltage whose integer value represents the signed code.
- MATLAB zero-lag results are never silently shifted; best lag is a separate diagnostic.

## Reproduction

Run `powershell -ExecutionPolicy Bypass -File scripts/run_all.ps1` to reproduce all generated nominal, stress, and MATLAB evidence. `-NominalOnly` omits stress and `-SkipMatlab` omits MATLAB. The script verifies the three persistent original SHA256 hashes before running and writes per-run command records alongside logs.

The complete run is intentionally disk- and time-intensive because the 10 s ASCII raw files are hundreds of megabytes to about one gigabyte each.
