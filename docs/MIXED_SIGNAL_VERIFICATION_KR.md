# AFE–RTL 통합 검증 범위

AFE–ADC XMODEL과 고정 Pure RTL 코어를 동일한 SystemVerilog simulation에 직접 연결했다. 36개 30분 입력의 compact acceptance에서는 전달 stream의 SHA-256, 최종 클래스 36/36과 네 Final Membrane 144/144가 기준 RTL/XSim과 일치했다.

저장소가 보유한 실제 30분 원시 XMODEL ADC dump의 독립 재실행 범위는 4/36이다. 두 결과를 구분하며, 36개 원시 dump가 저장소에 포함되었다고 주장하지 않는다.

이 검증은 model-level mixed-domain handoff다. 물리 AFE PCB, ADC silicon 또는 mixed-signal ASIC 검증이 아니다.
