// ================================================================
//  제27회 대한민국 반도체설계대전
//  Low-Power Mixed-Signal SoC for Wearable ECG Arrhythmia Detection
//
//  파일  : tb_ecg_afe.sv  (검증 테스트벤치)
//  담당  : 이수환 (한양대학교 융합전자공학부)
//  버전  : v2.0  (Bug #8~#10 수정 완료)
//
// ----------------------------------------------------------------
//  ■ 검증 목표
//    1. MIT-BIH 실제 ECG PWL 파일 인가 (real_ecg_100.pwl)
//    2. 12-bit ADC 출력 로그 저장 → adc_output.txt
//    3. 전체 계층 파형 VCD 저장 → ecg_result.vcd
//    4. 시뮬레이션 5초 = 5,000 샘플 @ 1 kSPS
//       (HPF 완전 정착: τ=330ms, 5τ≈1.65s → t≥2s 이후 데이터 유효)
//
//  ■ v2.0 수정 내역
//    Bug #8  : 시뮬레이션 시간  200ms → 5,000ms (5,000 샘플)
//    Bug #9  : $dumpvars depth  1 → 0  (전체 계층 VCD 덤프)
//    Bug #10 : 클럭 듀티비  99%/1% → 50%/50%  (Track 500µs / Hold 500µs)
//              + 차동 입력 포트 (v_ecg_neg 추가)
//              + 12-bit ADC 출력 포트 ([11:0])
//
//  ■ 데이터 후처리 권장사항
//    adc_output.txt 포맷: "sample_idx  adc_code  time_ns"
//    유효 데이터 필터  : sample_idx >= 2000  (t >= 2s, HPF 정착 후)
//    Python 예시:
//      import numpy as np
//      data = np.loadtxt('adc_output.txt', comments='#')
//      valid = data[data[:,0] >= 2000]
//      ecg_v = (valid[:,1] / 4095.0) * 3.3 - 1.65   # ADC code → Voltage
// ================================================================
`timescale 1ns/1ns

module tb_ecg_afe;

    // ============================================================
    //  포트 / 신호 선언
    // ============================================================
    real        v_ecg_pos;      // 양전극 구동 (PWL 파일)
    real        v_ecg_neg;      // 음전극 구동 (기준 전극 = 0V 고정)
    reg         clk;
    wire [11:0] adc_out;        // 12-bit ADC 출력 (Bug #4 수정 반영)

    integer f_adc;              // ADC 출력 로그 파일 핸들
    integer sample_cnt;         // 샘플 인덱스 카운터
    integer adc_idx;            // 로그용 샘플 인덱스 고정 (off-by-one 방지)

    // ============================================================
    //  DUT 인스턴스
    //  ※ Bug #6 수정 반영: 차동 입력 포트 (v_ecg_pos / v_ecg_neg)
    // ============================================================
    ecg_afe_xmodel DUT (
        .v_ecg_pos  (v_ecg_pos),
        .v_ecg_neg  (v_ecg_neg),
        .clk_samp   (clk),
        .adc_data   (adc_out)
    );

    // ============================================================
    //  음전극 초기화: Right Leg Drive 기준 = 0 V 고정
    //  (단일 리드 ECG 측정: 음전극은 기준 전위)
    // ============================================================
    initial begin
        v_ecg_neg = 0.0;
        sample_cnt = 0;
    end

    // ============================================================
    //  클럭 생성: 1 kSPS  (주기 = 1 ms = 1,000,000 ns)
    // ------------------------------------------------------------
    //  ■ Bug #10 수정: 99%/1% → 50%/50% 듀티비
    //    이전: HIGH 990µs / LOW 10µs  (물리적으로 부자연스러움)
    //    수정: HIGH 500µs / LOW 500µs
    //
    //  ■ 클럭 위상 설명:
    //    HIGH (t=0→500µs) : Tracking Phase
    //                        S/H 스위치 ON → 커패시터가 입력 전압 추종
    //    negedge (t=500µs): Hold Phase 시작
    //                        스위치 OFF → 커패시터가 전압 고정
    //                        ADC 변환 시작 (always @negedge 구동)
    //    LOW (t=500→1000µs): Hold + SAR 변환 구간 (500µs = 5× 여유)
    // ============================================================
    initial begin
        clk = 0;
        forever begin
            #500000  clk = 1;   // 500 µs HIGH  (Tracking)
            #500000  clk = 0;   // 500 µs LOW   (Hold / Convert)
        end
    end

    // ============================================================
    //  VCD 덤프 설정
    //  ■ Bug #9 수정: $dumpvars(1,...) → $dumpvars(0,...)
    //    depth=1 : tb_ecg_afe 모듈 최상위 신호만 덤프 (DUT 내부 없음)
    //    depth=0 : 전체 계층 (tb + DUT 내 모든 analog 노드) 덤프  ✓
    //    → ia_out, n_hpfp, n_notch 등 내부 노드 파형 관찰 가능
    // ============================================================
    initial begin
        $dumpfile("ecg_result.vcd");
        $dumpvars(0, tb_ecg_afe);    // Bug #9 수정: depth=0

        f_adc = $fopen("adc_output.txt", "w");
        if (!f_adc) begin
            $display("[Error] Cannot open adc_output.txt for writing.");
            $finish;
        end

        // 헤더 기록
        $fdisplay(f_adc, "# ECG AFE ADC Output Log");
        $fdisplay(f_adc, "# Format: sample_index  adc_code  time_ns");
        $fdisplay(f_adc, "# Note: HPF settling ~1.65s → valid data: sample_index >= 2000");
        $fdisplay(f_adc, "# ADC code to voltage: V = (code/4095)*3.3 - 1.65");
        $display("[Info] Output files ready: ecg_result.vcd, adc_output.txt");
    end

    // ============================================================
    //  ADC 출력 로그 기록 (매 샘플마다, negedge 기준)
    //  포맷: "샘플번호  ADC코드  시뮬레이션시간[ns]"
    // ============================================================
    //  ※ Bug #14 수정: DUT가 negedge에서 adc_data를 non-blocking 갱신하므로
    //    같은 시점 $fdisplay는 직전 샘플값을 기록(off-by-one). $fstrobe(타임스텝
    //    종료 시 기록)로 갱신된 adc_out을 읽고, 인덱스는 증가 전 값으로 고정.
    always @(negedge clk) begin
        if ($realtime > 0) begin
            adc_idx = sample_cnt;          // 이번 샘플 인덱스 고정
            sample_cnt = sample_cnt + 1;
            $fstrobe(f_adc, "%0d  %0d  %0t", adc_idx, adc_out, $realtime);

            // 진행 상황 콘솔 출력 (500 샘플마다)
            if (sample_cnt % 500 == 0)
                $strobe("[Info] t=%.3f s | Sample #%0d | ADC=%0d",
                         $realtime / 1.0e9, sample_cnt, adc_out);
        end
    end

    // ============================================================
    //  ECG PWL 파일 읽기 및 v_ecg_pos 구동
    // ------------------------------------------------------------
    //  파일  : real_ecg_100.pwl  (MIT-BIH Record 100, NSR)
    //  포맷  : "시간[초]  전압[V]"  (wfdb 변환 파일)
    //
    //  ■ Bug #8 수정: 시뮬레이션 종료 시간 200ms → 5,000ms
    //    이전: 200ms = 200 샘플 (부정맥 분류 불가)
    //    수정: 5,000ms = 5,000 샘플  (ECG 5초 = 평균 6~7 박동 캡처)
    //
    //  ■ HPF 정착 구간 안내:
    //    t = 0 ~ 1.65s : HPF 과도응답 구간 (베이스라인 서서히 안정)
    //    t ≥ 2.0s      : 정상 동작 구간 (유효 데이터)
    //    → 분류 알고리즘에는 sample_index >= 2000 데이터 사용 권장
    // ============================================================
    initial begin : ECG_STIMULUS
        int    fh;          // PWL 파일 핸들
        int    sc;          // $fscanf 반환값
        real   t_pwl;       // PWL 시간 [초]
        real   v_pwl;       // PWL 전압 [V]
        real   t_ns;        // 목표 시간 [ns]

        $display("[Info] Simulation Start. Loading real_ecg_100.pwl ...");

        fh = $fopen("real_ecg_100.pwl", "r");
        if (!fh) begin
            $display("[Error] PWL file not found: real_ecg_100.pwl");
            $display("[Hint]  파일 경로를 확인하거나 data/ 폴더 내 파일을 확인하세요.");
            $finish;
        end

        v_ecg_pos = 0.0;
        #2000;              // 2 µs 초기 안정화 (전원 인가 딜레이 모사)

        while (!$feof(fh)) begin
            sc = $fscanf(fh, "%f %f", t_pwl, v_pwl);

            if (sc == 2) begin
                t_ns = t_pwl * 1.0e9;   // 초 → 나노초

                // 목표 시간까지 대기 (이미 지난 시간은 skip)
                if (t_ns > $realtime)
                    #(t_ns - $realtime);

                v_ecg_pos = v_pwl;      // 전압 인가

                // Bug #8 수정: 5초 후 종료
                if ($realtime >= 5_000_000_000.0) begin
                    $display("[Info] 5 sec reached. Collected %0d samples. Stopping.",
                             sample_cnt);
                    break;
                end

            end else if (!$feof(fh)) begin
                // 포맷 오류 라인 경고 (빈 줄, 주석 등은 무시)
                $display("[Warning] PWL parse error at sim_time=%.6f s. Skipping line.",
                         $realtime / 1.0e9);
            end
        end

        $fclose(fh);

        $display("[Info] Simulation complete.");
        $display("[Info] Total samples collected: %0d", sample_cnt);
        $display("[Info] Valid samples (t >= 2s): %0d", sample_cnt - 2000);
        $display("[Info] Results: ecg_result.vcd, adc_output.txt");

        // f_adc는 지연 기록($fstrobe)이 모두 flush된 뒤 닫음 (Bug #14 관련 fd 경합 방지)
        #100_000;
        $fclose(f_adc);
        $finish;            // 100 µs 후 최종 종료
    end

endmodule
