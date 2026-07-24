# DOCX structural extraction summary

Source: `ECG_AFE_ADC_Schematic_정리.docx` (read-only original; SHA256 in `original_sha256.txt`). A shared-read snapshot was saved under `audit/docx_snapshot/` because Microsoft Word intermittently held the original open. Python `python-docx` structural extraction found 117 paragraphs and 26 tables.

## Extracted design statements

- Signal flow: differential ECG input, differential HPF, three-op-amp IA, active Twin-T 60 Hz notch, 150 Hz LPF/buffer, 1 kSPS Track-and-Hold, behavioral 12-bit ADC, signed stream.
- Supply: +5 V / -5 V.
- HPF: 10 Mohm and 33 nF, stated cutoff about 0.4823 Hz.
- IA: stated differential gain about 201 V/V.
- Twin-T: 26.526 kohm/13.263 kohm and 100 nF/200 nF ratios; stated center about 60 Hz.
- Bootstrap: 5 kohm/95 kohm and stated ratio about 0.95.
- LPF: 1 kohm and 1.06 uF, stated cutoff about 150.15 Hz.
- Sampling: 1 ms period and about 100 us track duration.
- ADC: +/-1.65 V input, endpoint mapping 0..4095, `ADC_CODE-2048` signed conversion, LSB `3.3/4095 V`.
- Scope limitation: the ADC is described as behavioral rather than a physical transistor-level SAR conversion circuit.

## Extracted validation intent versus source directive

The document describes short-run stabilization and full patient transient/AC validation workflows. The actual source schematic contains `.tran 0 20m 0 10u` and no `.ac` directive. The generated validation testbenches implement the missing independent AC analyses, short AFE/S&H checks, and 10 s runs without modifying the source schematic.

## Visual-edit decision

LibreOffice was unavailable and Word COM PDF export did not complete reliably while the source document was open. Therefore no modified DOCX was produced. This avoids presenting an unverified or layout-damaged document; `report/report_update_draft_ko.md` is the report-ready update source.
