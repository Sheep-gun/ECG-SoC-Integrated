// ================================================================
//  [1.3] 전극 DC offset / baseline wander 스트레스 시험
//   실제 ECG에 전극 DC offset과 저주파 baseline wander를 주입하여
//   HPF(IA 이득단 이전)가 이를 제거하고 IA/ADC가 포화하지 않는지 검증.
//   plusarg:  +dcoff=<V>    전극 DC offset (v_ecg_pos에 가산, 차동)
//             +bwamp=<V>    baseline wander 진폭
//             +bwfreq=<Hz>  baseline wander 주파수 (0.1/0.2 등)
//   출력: adc_stress.txt  (idx, adc code, time)
// ================================================================
`timescale 1ns/1ns
module tb_ecg_stress;
  real v_ecg_pos, v_ecg_neg;
  reg  clk;
  wire [11:0] adc_out;
  integer f_adc, sample_cnt, adc_idx;
  real dcoff, bwamp, bwfreq, v_pwl_hold, t_s, wander;

  ecg_afe_xmodel DUT(.v_ecg_pos(v_ecg_pos), .v_ecg_neg(v_ecg_neg),
                     .clk_samp(clk), .adc_data(adc_out));

  initial begin clk=0; forever begin #500000 clk=1; #500000 clk=0; end end

  initial begin
    sample_cnt = 0; v_pwl_hold = 0.0; dcoff = 0.0; bwamp = 0.0; bwfreq = 0.1;
    void'($value$plusargs("dcoff=%f", dcoff));
    void'($value$plusargs("bwamp=%f", bwamp));
    void'($value$plusargs("bwfreq=%f", bwfreq));
    f_adc = $fopen("adc_stress.txt", "w");
    $fdisplay(f_adc, "# ECG + dcoff=%.4fV bwamp=%.4fV bwfreq=%.3fHz", dcoff, bwamp, bwfreq);
  end

  always @(negedge clk) begin
    if ($realtime > 0) begin
      adc_idx = sample_cnt; sample_cnt = sample_cnt + 1;
      $fstrobe(f_adc, "%0d  %0d  %0t", adc_idx, adc_out, $realtime);
    end
  end

  // offset + baseline wander를 매 50µs 갱신 (차동: v_ecg_pos에만, neg=기준0)
  always #50000 begin
    t_s = $realtime/1.0e9;
    wander = bwamp*$sin(2.0*3.14159265358*bwfreq*t_s);
    v_ecg_pos = v_pwl_hold + dcoff + wander;
    v_ecg_neg = 0.0;
  end

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
