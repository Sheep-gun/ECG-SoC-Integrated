// ================================================================
//  AFE 특성 측정 테스트벤치 (주파수 응답 + CMRR)
//  plusarg:  +freq=<Hz>  +amp=<V>  +cm (있으면 공통모드, 없으면 차동)
//  측정: HPF 정착 후 2.5~3.5s 구간에서 buf_out peak-to-peak → 이득 산출
// ================================================================
`timescale 1ns/1ns
module tb_afe_char;
  real vp, vn;
  reg  clk;
  wire [11:0] adc;
  real r_buf, vmin, vmax;
  real freq, amp, t_s;
  integer is_cm;

  ecg_afe_xmodel DUT(.v_ecg_pos(vp), .v_ecg_neg(vn), .clk_samp(clk), .adc_data(adc));
  xreal_to_real TBUF(.out(r_buf), .in(DUT.buf_out));

  initial begin clk=0; forever begin #500000 clk=1; #500000 clk=0; end end

  initial begin
    freq = 20.0; amp = 0.0005;
    void'($value$plusargs("freq=%f", freq));
    void'($value$plusargs("amp=%f", amp));
    is_cm = $test$plusargs("cm");
    vp = 0.0; vn = 0.0;
  end

  // 사인 입력 (매 50µs 갱신)
  always #50000 begin
    t_s = $realtime/1.0e9;
    vp = amp*$sin(2.0*3.14159265358*freq*t_s);
    vn = is_cm ? vp : 0.0;
  end

  // 정착 후 측정 구간에서 buf_out 최소/최대 추적
  initial begin
    vmin =  1.0e9; vmax = -1.0e9;
    forever begin
      #20000;
      if ($realtime >= 2_500_000_000.0 && $realtime <= 3_500_000_000.0) begin
        if (r_buf < vmin) vmin = r_buf;
        if (r_buf > vmax) vmax = r_buf;
      end
    end
  end

  initial begin
    #3_600_000_000;
    $display("CHAR_RESULT freq=%.2f mode=%s in_p2p=%.6e out_p2p=%.6e gain=%.3f gain_dB=%.2f",
       freq, (is_cm? "CM":"DIFF"), 2.0*amp, vmax-vmin, (vmax-vmin)/(2.0*amp),
       20.0*$log10(((vmax-vmin)/(2.0*amp))));
    $finish;
  end
endmodule
