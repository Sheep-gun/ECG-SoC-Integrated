# Reference Vector Manifest

ì´ ë¬¸ìë MATLAB reference input/output vectorì SHA256 hashë¥¼ ì ë¦¬íë¤. ì´ vectorë íì MATLAB-vs-XMODEL equivalence verificationì ê¸°ì¤ì¼ë¡ ì¬ì©ëë¤.

> `source_code_signed_est_5uV_per_code`ë ìë³¸ ECG ìë ¥ ì ì scale ì¶ì ì© estimateì´ë©° AFE ADC output codeê° ìëë¤. XMODEL analog inputì `voltage_V`ë¥¼ ì¬ì©íë¤.

## Output format êµ¬ë¶

- `adc_offset_binary.mem`: physical ADC offset-binary code convention íì¸ì© referenceì´ë¤.
- `adc_signed.txt`: offset-binary codeìì mid-code 2048ì ì ê±°í signed decimal stream referenceì´ë¤.
- `adc_signed_twos_complement.mem`: ê³µì downstream canonical replay formatì´ë¤. signed 12-bit streamì 12-bit two's-complement bit patternì¼ë¡ encodingí 3ìë¦¬ ëë¬¸ì hex `.mem`ì´ë©°, í ì¤ë¹ 1 sampleì ì ì¥íë¤.
- `adc_signed_twos_complement.mem`ì ê° ì¤ì `encoded = mod(adc_signed, 4096)`ì ëì¼íë¤.

## Manifest

| Class | File role | Relative path | Bytes | SHA256 |
|---|---|---|---:|---|
| AFF | adc_offset_binary.mem | `reference_vectors/AFF/adc_offset_binary.mem` | 240000 | `0f03e0e2c8f50e9c188a1c859c5c0e914a80877dbd73d5624993e1f8f96e93d8` |
| AFF | adc_signed.txt | `reference_vectors/AFF/adc_signed.txt` | 206825 | `cedcd000123a013172f9d5bb0b19fca85cc38d9985dc92ab4d41a0eb8e3f3994` |
| AFF | adc_signed_twos_complement.mem | `reference_vectors/AFF/adc_signed_twos_complement.mem` | 240000 | `232a83b062eefbed8fbb81f45e53a61e821f75cf8c5e4704d112b9917306fa46` |
| AFF | input.csv | `reference_vectors/AFF/input.csv` | 1586150 | `d55bba730a8c2a0dd521a1c880ac56dd587182ab981f454686d43ea56bec4d7f` |
| AFF | matlab_stage_outputs.csv | `reference_vectors/AFF/matlab_stage_outputs.csv` | 7450548 | `33c55e2e1f11b0b7d07dc3f97de3c2ba97519eb0fde8cc067076b497c99d3dbb` |
| ARR | adc_offset_binary.mem | `reference_vectors/ARR/adc_offset_binary.mem` | 240000 | `1c218ac363c580317d7acd18a7a869c58ef0c11c7420f12d4b0191083c5bb6ca` |
| ARR | adc_signed.txt | `reference_vectors/ARR/adc_signed.txt` | 219589 | `19e3152e9112afbe04de6c73616f57ac07c8e040f9ce1ce6f5c046621218e7bc` |
| ARR | adc_signed_twos_complement.mem | `reference_vectors/ARR/adc_signed_twos_complement.mem` | 240000 | `3b6b78c5a7a78daf4efdc42dafd49fccf7a82642377f1fd0e45d2c1e249aad7b` |
| ARR | input.csv | `reference_vectors/ARR/input.csv` | 1598628 | `027cd0b0540baf34eaf2c8cd6056dc5ce8d4a8857841df6921556714b04c4646` |
| ARR | matlab_stage_outputs.csv | `reference_vectors/ARR/matlab_stage_outputs.csv` | 7514904 | `e100cbc5eb494474fda71e8db0714953ceefd93d48bbb606701667f2b0512b62` |
| CHF | adc_offset_binary.mem | `reference_vectors/CHF/adc_offset_binary.mem` | 240000 | `ae7ec806059809121fd5524bb634fa8d2ceaaeaa158f38ce833f771fe085a42c` |
| CHF | adc_signed.txt | `reference_vectors/CHF/adc_signed.txt` | 221866 | `7bb51735287c7162df27d5327a4d9199c45bbc07e58ced45dd6addd3eca2d2b6` |
| CHF | adc_signed_twos_complement.mem | `reference_vectors/CHF/adc_signed_twos_complement.mem` | 240000 | `74fa0f79ed8ef44a20e32f555bc904a309e94f127485b26673dec8cec45632b8` |
| CHF | input.csv | `reference_vectors/CHF/input.csv` | 1618855 | `1887226971c87366c7c9116398c89757a4b953562337334c8f1510cf945e5e59` |
| CHF | matlab_stage_outputs.csv | `reference_vectors/CHF/matlab_stage_outputs.csv` | 7507530 | `5d54e59bfe1b65d9853f12d2f79c6192709a9e8ea7cad85b50a8c5d0ef87cb36` |
| NSR | adc_offset_binary.mem | `reference_vectors/NSR/adc_offset_binary.mem` | 240000 | `a9da5909aa345e89bd9a0357f33a7e92bdf8263e6d916e617dd4de26114cb1ba` |
| NSR | adc_signed.txt | `reference_vectors/NSR/adc_signed.txt` | 216136 | `41c790933d3176faec4df796b76138386ce7d45c3644186ca218c8005ec35441` |
| NSR | adc_signed_twos_complement.mem | `reference_vectors/NSR/adc_signed_twos_complement.mem` | 240000 | `e83abe24458b9bfb45c72d58b2c47f3186f2ddb89c4ce8de5e0e15c61ce23051` |
| NSR | input.csv | `reference_vectors/NSR/input.csv` | 1451439 | `f2ac2abd15b15836898089b998561f36cd60f2d08c649ae76c8e9ffab553bb30` |
| NSR | matlab_stage_outputs.csv | `reference_vectors/NSR/matlab_stage_outputs.csv` | 7502567 | `39997fc36a81db72d8083cfb589164eaf332f70e7eb3c3d92de5a72a2276b869` |