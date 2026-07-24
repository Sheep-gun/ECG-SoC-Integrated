// AFE 전용 배치 TB: +pwl=<입력PWL> +endsec=<초> +out=<ADC출력txt>
//  adc_out(unsigned offset-binary 12-bit)를 매 1kSPS 샘플마다 한 줄씩 기록.
`timescale 1ns/1ns
module tb_afe_batch;
  real v_ecg_pos, v_ecg_neg;
  reg clk;
  wire [11:0] adc_out;
  integer f_adc, sample_cnt, fh, sc;
  real t_pwl, v_pwl, t_ns, endsec;
  string pwl_file, out_file;

  ecg_afe_xmodel DUT (.v_ecg_pos(v_ecg_pos), .v_ecg_neg(v_ecg_neg),
                      .clk_samp(clk), .adc_data(adc_out));

  initial begin v_ecg_neg = 0.0; sample_cnt = 0; end
  initial begin clk = 0; forever begin #500000 clk = 1; #500000 clk = 0; end end

  always @(negedge clk) begin
    if ($realtime > 0 && f_adc != 0) begin
      sample_cnt = sample_cnt + 1;
      $fstrobe(f_adc, "%0d", adc_out);
    end
  end

  initial begin : MAIN
    pwl_file = "ecg.pwl"; out_file = "adc_out.txt"; endsec = 60.0; f_adc = 0;
    void'($value$plusargs("pwl=%s", pwl_file));
    void'($value$plusargs("out=%s", out_file));
    void'($value$plusargs("endsec=%f", endsec));
    f_adc = $fopen(out_file, "w");
    fh    = $fopen(pwl_file, "r");
    if (f_adc == 0 || fh == 0) begin
      $display("[Error] file open fail pwl=%s out=%s", pwl_file, out_file); $finish;
    end
    v_ecg_pos = 0.0; #2000;
    while (!$feof(fh)) begin
      sc = $fscanf(fh, "%f %f", t_pwl, v_pwl);
      if (sc == 2) begin
        t_ns = t_pwl * 1.0e9;
        if (t_ns > $realtime) #(t_ns - $realtime);
        v_ecg_pos = v_pwl;
        if ($realtime >= endsec * 1.0e9) break;
      end
    end
    $fclose(fh);
    #100000; $fclose(f_adc);
    $display("AFE_BATCH_DONE samples=%0d out=%s", sample_cnt, out_file);
    $finish;
  end
endmodule
