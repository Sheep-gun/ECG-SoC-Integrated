// ================================================================
//  [2.4] op-amp finite GBW / VOS 측정 tb (ecg_afe_xmodel_op 구동)
//   parameter GBW_HZ, VOS는 vsim -g로 오버라이드. 실제 ECG 구동.
//   출력: adc_op.txt (idx, code, time)
// ================================================================
`timescale 1ns/1ns
module tb_afe_op #(parameter real GBW_HZ = 1.0e9, parameter real VOS = 0.0);
  real v_ecg_pos, v_ecg_neg;
  reg  clk;
  wire [11:0] adc_out;
  integer f_adc, sample_cnt, adc_idx;
  real v_pwl_hold;

  ecg_afe_xmodel_op #(.GBW_HZ(GBW_HZ), .VOS(VOS)) DUT
     (.v_ecg_pos(v_ecg_pos), .v_ecg_neg(v_ecg_neg), .clk_samp(clk), .adc_data(adc_out));

  initial begin clk=0; forever begin #500000 clk=1; #500000 clk=0; end end

  initial begin
    sample_cnt = 0; v_pwl_hold = 0.0; v_ecg_neg = 0.0;
    f_adc = $fopen("adc_op.txt", "w");
    $fdisplay(f_adc, "# GBW_HZ=%.0f VOS=%.5f", GBW_HZ, VOS);
  end

  always @(negedge clk) begin
    if ($realtime > 0) begin
      adc_idx = sample_cnt; sample_cnt = sample_cnt + 1;
      $fstrobe(f_adc, "%0d  %0d  %0t", adc_idx, adc_out, $realtime);
    end
  end

  always #50000 v_ecg_pos = v_pwl_hold;   // ECG(차동), neg=0

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
