# Analog validation Figure handoff

이 디렉터리는 팀이 별도 handoff 폴더로 제공한 아날로그 검증 Figure를 저장소에 등록하기 위한 provenance manifest다. 공개 문서와 checker에는 개인 로컬 경로를 사용하지 않고 아래 원본명·저장소명·SHA-256만 기록한다.

| 원본명 | 저장소 파일 | SHA-256 |
|---|---|---|
| `아날로그 회로 구조도.svg` | `figures/final/SPICE-01_analog_afe_architecture.svg` | `abdeaeecfbcb52e79a467e376fc586d1966f112786167314ddb0a1ae862ca2c6` |
| `full schematic by LTspice.jpg` | `figures/final/SPICE-02_ltspice_xmodel_aligned_schematic.jpg` | `9440e2287f789a1427245c83a87556091e62ced00a32418ce1d162b493bc9490` |
| `Overall AFE Frequency Response Comparison.png` | `figures/final/SPICE-03_matlab_ltspice_afe_response.png` | `41f2dede9e31b09ca35eabd375615cf8445409bd26f4497a7f4a1de1bbf60181` |
| `60 HZ Active Twin-T Notch Response Comparison.png` | `figures/final/SPICE-04_matlab_ltspice_notch_response.png` | `54129359411767150e513d235fdddb46a7a66d5bf9871c246d0ee9e5dcdf067c` |
| `adc_waveform_full.png` | `figures/final/SPICE-05_xmodel_ltspice_adc_waveform_full.png` | `405c99c24da8637bf63516db9b433d1f41d8af109cdb23a1be2600eac168bb27` |
| `adc_waveform_zoom_2_3s.png` | `figures/final/SPICE-06_xmodel_ltspice_adc_waveform_zoom.png` | `bd1794967515cebc76cfd186a5e20443f4337a889fa4ef0c6d1af2bcaab72ee6` |
| `adc_error_lsb.png` | `figures/final/SPICE-07_xmodel_ltspice_adc_error.png` | `b431c7511b8e62ce71206103304563975e7833b99832855f04eae05fa29bb34f` |
| `adc_error_histogram.png` | `figures/final/SPICE-08_xmodel_ltspice_adc_error_histogram.png` | `f076853dce4cb35a71c073a56071d3e327ef81b55a8cb53e43c553082a7a3b49` |
| `ADC Code Agreement by Error Range.png` | `figures/final/SPICE-09_xmodel_ltspice_adc_agreement.png` | `75faf5f2fef3a5b4b75b3ab2cfdceea675f69a7598717cc67255a1ae80a30ff4` |
| `XMODEL-LTspice ADC output Quantitative Comparison.png` | `figures/final/SPICE-10_xmodel_ltspice_adc_metrics.png` | `8b6d60ca26ba71dae6fc6235acbf5588b2591b08716af3cb6eb726b8d41a2d0f` |

Figure는 crop, resampling, annotation 변경 없이 원본 byte로 복사한다. 보고서 해석의 수치 근거는 `validation/afe_ltspice_xmodel_aligned/tables/`의 CSV와 함께 사용한다.
