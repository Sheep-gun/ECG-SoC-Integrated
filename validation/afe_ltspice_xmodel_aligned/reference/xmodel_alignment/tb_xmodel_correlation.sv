`timescale 1ns/1ns
// Correlation-only wrapper. DUT source remains the fixed commit copy.
module tb_xmodel_correlation;
  real v_ecg_pos, v_ecg_neg, v_pwl_hold;
  reg clk;
  wire [11:0] adc_out;
  integer f_adc, sample_cnt;

  ecg_afe_xmodel DUT(.v_ecg_pos(v_ecg_pos), .v_ecg_neg(v_ecg_neg),
                     .clk_samp(clk), .adc_data(adc_out));

  initial begin
    clk = 0;
    forever begin #500000 clk = 1; #500000 clk = 0; end
  end

  initial begin
    v_ecg_pos = 0.0; v_ecg_neg = 0.0; v_pwl_hold = 0.0; sample_cnt = 0;
    f_adc = $fopen("adc_nominal.txt", "w");
    $fdisplay(f_adc, "# sample_index adc_code aperture_ns");
  end

  // Match the fixed testbench contract: ECG+=held patient sample, ECG-=0,
  // and input update every 50 us. First ADC falling edge is 1.000 ms.
  always #50000 begin
    v_ecg_pos = v_pwl_hold;
    v_ecg_neg = 0.0;
  end

  always @(negedge clk) begin
    if ($realtime > 0) begin
      $fstrobe(f_adc, "%0d %0d %0t", sample_cnt, adc_out, $realtime);
      sample_cnt = sample_cnt + 1;
      if (sample_cnt == 10000) begin
        #1; $fclose(f_adc); $finish;
      end
    end
  end

  initial begin : STIM
    integer fh, sc;
    real t_pwl, v_pwl, t_ns;
    fh = $fopen("patient100_ecg_10s.txt", "r");
    if (!fh) begin $fatal(1, "patient100_ecg_10s.txt not found"); end
    while (!$feof(fh)) begin
      sc = $fscanf(fh, "%f %f", t_pwl, v_pwl);
      if (sc == 2) begin
        t_ns = t_pwl * 1.0e9;
        if (t_ns > $realtime) #(t_ns - $realtime);
        v_pwl_hold = v_pwl;
      end
    end
    $fclose(fh);
  end
endmodule
