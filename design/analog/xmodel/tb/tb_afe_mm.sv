// ================================================================
//  [1.2] R/C mismatch 측정 tb (ecg_afe_xmodel_mm 구동)
//   parameter MM은 vsim -gMM=<val>로 오버라이드.
//   +mode=cmrr : ECG 없이 공통모드 1V@10Hz 주입 → 출력 leakage로 CMRR 산출
//   +mode=pli60: ECG + 60Hz(vcm0.5,vdiff1mV) → 노치 detune 잔차·클리핑
//   출력: adc_mm.txt (idx, code, time)
// ================================================================
`timescale 1ns/1ns
module tb_afe_mm #(parameter real MM = 0.0);
  real v_ecg_pos, v_ecg_neg;
  reg  clk;
  wire [11:0] adc_out;
  integer f_adc, sample_cnt, adc_idx;
  real v_pwl_hold, t_s, s10, s60;
  string mode;

  ecg_afe_xmodel_mm #(.MM(MM)) DUT(.v_ecg_pos(v_ecg_pos), .v_ecg_neg(v_ecg_neg),
                                   .clk_samp(clk), .adc_data(adc_out));

  initial begin clk=0; forever begin #500000 clk=1; #500000 clk=0; end end

  initial begin
    sample_cnt = 0; v_pwl_hold = 0.0; mode = "cmrr";
    void'($value$plusargs("mode=%s", mode));
    f_adc = $fopen("adc_mm.txt", "w");
    $fdisplay(f_adc, "# mode=%s MM=%.4f", mode, MM);
  end

  always @(negedge clk) begin
    if ($realtime > 0) begin
      adc_idx = sample_cnt; sample_cnt = sample_cnt + 1;
      $fstrobe(f_adc, "%0d  %0d  %0t", adc_idx, adc_out, $realtime);
    end
  end

  // 자극 갱신 (50µs)
  always #50000 begin
    t_s = $realtime/1.0e9;
    s10 = $sin(2.0*3.14159265358*10.0*t_s);
    s60 = $sin(2.0*3.14159265358*60.0*t_s);
    if (mode == "cmrr") begin
      // 순수 공통모드 1V@10Hz (양전극 동일), ECG 없음
      v_ecg_pos = 1.0*s10;
      v_ecg_neg = 1.0*s10;
    end else begin
      // ECG + 60Hz PLI (공통 0.5V + 차동 1mV)
      v_ecg_pos = v_pwl_hold + 0.5*s60 + 0.001*s60;
      v_ecg_neg = 0.5*s60;
    end
  end

  initial begin : STIM
    int fh, sc; real t_pwl, v_pwl, t_ns;
    v_pwl_hold = 0.0; #2000;
    if (mode == "pli60") begin
      fh = $fopen("real_ecg_100.pwl", "r");
      if (!fh) begin $display("[Error] PWL 없음"); $finish; end
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
    end else begin
      #(5.0e9);   // cmrr: 5s 구동
    end
    #100000; $fclose(f_adc); $finish;
  end
endmodule
