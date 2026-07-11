// ================================================================
//  다중 클래스 ECG 검증 TB — NSR/ARR/AFF/CHF
//   plusarg: +pwl=<파일>  +out=<ADC 로그파일>
//   10초 인가(HPF 정착 1.65s 후 ~8.3s 유효 → 클래스별 다수 박동 캡처)
// ================================================================
`timescale 1ns/1ns
module tb_ecg_multiclass;
  real v_ecg_pos, v_ecg_neg;
  reg  clk;
  wire [11:0] adc_out;
  integer f_adc, sample_cnt, adc_idx;
  string pwl_file, out_file;

  ecg_afe_xmodel DUT(.v_ecg_pos(v_ecg_pos), .v_ecg_neg(v_ecg_neg),
                     .clk_samp(clk), .adc_data(adc_out));

  initial begin clk=0; forever begin #500000 clk=1; #500000 clk=0; end end
  initial begin v_ecg_neg = 0.0; sample_cnt = 0; end

  always @(negedge clk) begin
    if ($realtime > 0) begin
      adc_idx = sample_cnt; sample_cnt = sample_cnt + 1;
      $fstrobe(f_adc, "%0d  %0d  %0t", adc_idx, adc_out, $realtime);
    end
  end

  initial begin : STIM
    int fh, sc; real t_pwl, v_pwl, t_ns;
    pwl_file = "ecg.pwl"; out_file = "adc_mc.txt";
    void'($value$plusargs("pwl=%s", pwl_file));
    void'($value$plusargs("out=%s", out_file));
    f_adc = $fopen(out_file, "w");
    $fdisplay(f_adc, "# %s", pwl_file);
    fh = $fopen(pwl_file, "r");
    if (!fh) begin $display("[Error] PWL 없음: %s", pwl_file); $finish; end
    v_ecg_pos = 0.0; #2000;
    while (!$feof(fh)) begin
      sc = $fscanf(fh, "%f %f", t_pwl, v_pwl);
      if (sc == 2) begin
        t_ns = t_pwl*1.0e9;
        if (t_ns > $realtime) #(t_ns - $realtime);
        v_ecg_pos = v_pwl;
        if ($realtime >= 10_000_000_000.0) break;
      end
    end
    $fclose(fh);
    #100000; $fclose(f_adc); $finish;
  end
endmodule
