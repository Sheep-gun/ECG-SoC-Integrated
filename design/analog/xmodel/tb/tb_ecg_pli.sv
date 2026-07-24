// ================================================================
//  60Hz 전원선 간섭(PLI) 주입 시험 테스트벤치
//   실제 ECG(real_ecg_100.pwl) + 60Hz 간섭을 인가하여 AFE의 제거 성능 검증.
//   plusarg:  +vcm=<V>  공통모드 60Hz 진폭 (양 전극 동시)
//             +vdiff=<V> 차동 60Hz 진폭 (양 전극에만)
//   출력: adc_pli.txt  (sample idx, adc code, time)
// ================================================================
`timescale 1ns/1ns
module tb_ecg_pli;
  real v_ecg_pos, v_ecg_neg;
  reg  clk;
  wire [11:0] adc_out;
  integer f_adc, sample_cnt, adc_idx;
  real vcm, vdiff, v_pwl_hold, t_s, noise60;

  ecg_afe_xmodel DUT(.v_ecg_pos(v_ecg_pos), .v_ecg_neg(v_ecg_neg),
                     .clk_samp(clk), .adc_data(adc_out));

  initial begin clk=0; forever begin #500000 clk=1; #500000 clk=0; end end

  initial begin
    sample_cnt = 0; v_pwl_hold = 0.0; vcm = 0.0; vdiff = 0.0;
    void'($value$plusargs("vcm=%f", vcm));
    void'($value$plusargs("vdiff=%f", vdiff));
    f_adc = $fopen("adc_pli.txt", "w");
    $fdisplay(f_adc, "# ECG + 60Hz PLI  vcm=%.4f vdiff=%.4f", vcm, vdiff);
  end

  // ADC 로그 (off-by-one 방지: $fstrobe)
  always @(negedge clk) begin
    if ($realtime > 0) begin
      adc_idx = sample_cnt; sample_cnt = sample_cnt + 1;
      $fstrobe(f_adc, "%0d  %0d  %0t", adc_idx, adc_out, $realtime);
    end
  end

  // 60Hz 간섭을 매 50µs 갱신하여 PWL 홀드값에 더함
  always #50000 begin
    t_s = $realtime/1.0e9;
    noise60 = $sin(2.0*3.14159265358*60.0*t_s);
    v_ecg_pos = v_pwl_hold + vcm*noise60 + vdiff*noise60;
    v_ecg_neg = vcm*noise60;     // 공통모드는 양 전극 동일
  end

  // ECG PWL 구동
  initial begin : STIM
    int fh, sc; real t_pwl, v_pwl, t_ns;
    fh = $fopen("real_ecg_100.pwl", "r");
    if (!fh) begin $display("[Error] PWL 없음"); $finish; end
    v_pwl_hold = 0.0; #2000;
    while (!$feof(fh)) begin
      sc = $fscanf(fh, "%f %f", t_pwl, v_pwl);
      if (sc == 2) begin
        t_ns = t_pwl*1.0e9;
        if (t_ns > $realtime) #(t_ns - $realtime);
        v_pwl_hold = v_pwl;
        if ($realtime >= 5_000_000_000.0) break;
      end
    end
    $fclose(fh);
    #100000; $fclose(f_adc); $finish;
  end
endmodule
