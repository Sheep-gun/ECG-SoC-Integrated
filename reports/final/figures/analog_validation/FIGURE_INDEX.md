# Analog Validation Figure Index

이 폴더의 그림은 2026-07-19 아날로그 팀 handoff 폴더 `C:\Users\YangGeon\Desktop\Figure`에서 선별해 이름만 정규화한 사본이다. 픽셀·벡터 내용은 변경하지 않았다. LTspice 단계가 빠진 구버전 `설계회로 검증.svg`는 최종 보고서 흐름과 맞지 않아 사용하지 않았다.

| Figure | Repository file | Original file | SHA-256 | Use |
|---|---|---|---|---|
| A-1 | `01_analog_afe_architecture.svg` | `아날로그 회로 구조도.svg` | `abdeaeecfbcb52e79a467e376fc586d1966f112786167314ddb0a1ae862ca2c6` | AFE signal path and non-ideality injection |
| A-4 | `02_ltspice_xmodel_aligned_schematic.jpg` | `full schematic by LTspice.jpg` | `9440e2287f789a1427245c83a87556091e62ced00a32418ce1d162b493bc9490` | LTspice implementation evidence |
| A-2 | `03_matlab_ltspice_afe_response.png` | `Overall AFE Frequency Response Comparison.png` | `41f2dede9e31b09ca35eabd375615cf8445409bd26f4497a7f4a1de1bbf60181` | MATLAB-LTspice full AFE comparison |
| A-3 | `04_matlab_ltspice_notch_response.png` | `60 HZ Active Twin-T Notch Response Comparison.png` | `54129359411767150e513d235fdddb46a7a66d5bf9871c246d0ee9e5dcdf067c` | MATLAB-LTspice 60 Hz notch comparison |
| A-5 | `05_xmodel_ltspice_adc_waveform_full.png` | `xmodel vs LTspice/adc_waveform_full.png` | `405c99c24da8637bf63516db9b433d1f41d8af109cdb23a1be2600eac168bb27` | Full 10-second ADC overlay |
| A-6 | `06_xmodel_ltspice_adc_waveform_zoom.png` | `xmodel vs LTspice/adc_waveform_zoom_2_3s.png` | `bd1794967515cebc76cfd186a5e20443f4337a889fa4ef0c6d1af2bcaab72ee6` | QRS-scale ADC overlay |
| A-7 | `07_xmodel_ltspice_adc_error.png` | `xmodel vs LTspice/adc_error_lsb.png` | `b431c7511b8e62ce71206103304563975e7833b99832855f04eae05fa29bb34f` | Per-sample error location |
| A-10 | `08_xmodel_ltspice_adc_error_histogram.png` | `xmodel vs LTspice/adc_error_histogram.png` | `f076853dce4cb35a71c073a56071d3e327ef81b55a8cb53e43c553082a7a3b49` | Error distribution supplement |
| A-9 | `09_xmodel_ltspice_adc_agreement.png` | `xmodel vs LTspice/ADC Code Agreement by Error Range.png` | `75faf5f2fef3a5b4b75b3ab2cfdceea675f69a7598717cc67255a1ae80a30ff4` | ±5/±10 LSB coverage |
| A-8 | `10_xmodel_ltspice_adc_metrics.png` | `xmodel vs LTspice/XMODEL-LTspice ADC output Quantitative Comparison.png` | `8b6d60ca26ba71dae6fc6235acbf5588b2591b08716af3cb6eb726b8d41a2d0f` | Quantitative summary table |

Main report use: A-1, A-2, A-4, A-8, A-9. Detailed analog report additionally uses A-3, A-5, A-6, A-7 and A-10.
