# Dense 60 Hz Notch Reference

이 문서는 60 Hz mains target에 대한 active Twin-T frequency-domain nominal reference를 정리한다.
50 Hz까지 완전히 제거한다고 주장하지 않는다.

## Bandwidth/Q 정의

- `configured_Q`: MATLAB notch 설계에 사용한 nominal parameter이다.
- `estimated_Q_from_sweep`: 30-100 Hz dense sweep에서 local passband reference magnitude 기준으로 계산한 nominal estimate이다.
- `physical_Q_claim`: 실제 회로 측정 Q가 아니므로 physical Q로 주장하지 않는다.

| target_frequency_Hz | sweep_low_Hz | sweep_high_Hz | notch_center_frequency_Hz | exact_60Hz_attenuation_dB | minimum_attenuation_dB_in_sweep | local_passband_reference_dB | minus3dB_threshold_dB | bandwidth_low_Hz | bandwidth_high_Hz | bandwidth_Hz | estimated_Q_from_sweep | configured_Q | attenuation_at_50Hz_dB | physical_Q_claim | definition_note | scope_note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 60 | 30 | 100 | 60 | -83.5556869284 | -83.5556869284 | -0.113293122521 | -3.11329312252 | 54.425 | 66.146 | 11.721 | 5.11901714871 | 5 | -1.13121616922 | No; nominal MATLAB reference only | Bandwidth is computed relative to the local passband reference magnitude from 30 Hz and 100 Hz endpoints. Estimated Q is a nominal sweep estimate, not a measured physical circuit Q. | 60 Hz mains target; not claimed as complete 50 Hz rejection |
