# Fixed-reference provenance

## MATLAB AFE/ADC pre-validation

- Upstream discovered from the integration project's component provenance: `https://github.com/ferocious-kiwi/ECG-SoC-MATLAB-AFE-ADC-Prevalidation`
- Required and checked-out commit: `907f7e1f081a9d6a5703a32095d962143315a192`
- Local path: `reference/matlab_fixed_907f7e1/`
- Execution: MATLAB 26.1.0.3203278 (R2026a), through `scripts/run_fixed_matlab_patient.m`
- Patient numeric content: line-wise identical to the workspace PWL; fixed copy uses CRLF while workspace uses LF, so byte hashes differ.
- Loader note: the fixed `.txt` branch treats column 1 as voltage for a two-column file. The adapter copies the exact patient bytes to a validation-only `.pwl` filename so the fixed commit's PWL parser consumes time/voltage columns correctly. No fixed source was patched.

## SystemVerilog AFE/ADC XMODEL

- Upstream discovered from the integration project's component provenance: `https://github.com/Hwan-22/ECG-SoC`
- Required commit object verified: `4756a5086023547328ef44fd5fd87da3c250dc39`
- Canonical integrated copy: `design/analog/xmodel/`
- The former `reference/xmodel_fixed_4756a50_subset/` duplicate was removed during workspace consolidation.
- Stress values used by this package come from the fixed component's AFE stress definitions/results, not from an invented Python model.

## Digital RTL/IP/FPGA commit

The digital commit `c6b80de19cdcad5b7e43fe7835588b629d847f75` was not used as LTspice analog evidence. This package does not claim that its analog results prove RTL/IP/FPGA equivalence or classification accuracy.
