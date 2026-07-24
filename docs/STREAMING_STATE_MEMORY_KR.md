# Streaming state와 memory 범위

Pure RTL은 30분 raw ECG 배열을 내부에 저장하지 않는다. 새 표본이 들어올 때 다음 상태만 갱신한다.

- adaptive event와 QRS detector state
- RR interval, PNN, RDM과 ectopic evidence state
- DSCR, RAM, QRS MAF와 RBBB-like morphology state
- 네 class의 Snapshot 및 Final Membrane
- pipeline과 WTA control state

1 kSPS signed 12-bit로 30분 raw input은 약 2.7 MB지만, 이는 구현에서 회피한 입력 window 크기다. 실제 dense baseline을 구현해 측정한 memory saving으로 주장하지 않는다.
