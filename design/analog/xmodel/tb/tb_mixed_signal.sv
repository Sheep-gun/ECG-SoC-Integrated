// ================================================================
//  Mixed-signal 통합 TB: AFE(XModel) ──[어댑터2개]── 디지털 SNN core
//   ecg_afe_xmodel(아날로그) + snn_ecg_model_a_plus_core(디지털)를 한 TB에 인스턴스화.
//   어댑터1: offset-binary(unsigned,2048중심) → 2의보수 signed  ({~adc[11],adc[10:0]})
//   어댑터2: AFE 매 샘플(negedge clk_samp)마다 core에 sample_valid·rhythm_tick 1펄스
//   HPF 정착(START_SEC) 후 segment_start, 이후 깨끗한 ECG를 core에 전달, 끝에 segment_done.
//   plusarg: +pwl=<파일> +endsec=<초> +startsec=<초>
//   결과: MIXED_RESULT ... pred_valid pred_class (0=NSR 1=CHF 2=ARR 3=AFF)
// ================================================================
`timescale 1ns/1ns
module tb_mixed_signal;
  real v_ecg_pos, v_ecg_neg;
  reg  samp_clk;
  wire [11:0] afe_adc;
  reg  core_clk, rst, sample_valid, rhythm_tick, segment_start, segment_done;
  wire signed [11:0] core_adc;
  wire [1:0] pred_class;
  wire pred_valid;
  reg  core_active;
  string pwl_file;
  real endsec, startsec, t_pwl, v_pwl, t_ns;
  integer fh, sc;

  // ── AFE (아날로그) ──
  ecg_afe_xmodel AFE (.v_ecg_pos(v_ecg_pos), .v_ecg_neg(v_ecg_neg),
                      .clk_samp(samp_clk), .adc_data(afe_adc));
  // ── 어댑터1: offset-binary → signed (= adc-2048, MSB 반전) ──
  assign core_adc = {~afe_adc[11], afe_adc[10:0]};
  // ── 디지털 core ──
  snn_ecg_model_a_plus_core CORE (
      .clk(core_clk), .rst(rst), .sample_valid(sample_valid), .rhythm_tick(rhythm_tick),
      .segment_start(segment_start), .segment_done(segment_done),
      .adc_data(core_adc), .pred_class(pred_class), .pred_valid(pred_valid));

  // 클럭: core_clk 20µs주기(50kHz), AFE samp_clk 1kHz
  initial begin core_clk=0; forever #10000 core_clk=~core_clk; end
  initial begin samp_clk=0; forever begin #500000 samp_clk=1; #500000 samp_clk=0; end end

  // ── 어댑터2: AFE 매 샘플마다 core에 1펄스 (정착 후, core_active 시) ──
  always @(negedge samp_clk) begin
    if (core_active) begin
      @(negedge core_clk);
      sample_valid <= 1'b1; rhythm_tick <= 1'b1;
      @(posedge core_clk); #1;
      sample_valid <= 1'b0; rhythm_tick <= 1'b0;
    end
  end

  // ── ECG PWL → AFE 입력 ──
  initial begin : STIM
    pwl_file="ecg.pwl"; endsec=12.0;
    void'($value$plusargs("pwl=%s", pwl_file));
    void'($value$plusargs("endsec=%f", endsec));
    v_ecg_pos=0.0; v_ecg_neg=0.0;
    fh=$fopen(pwl_file,"r");
    if(!fh) begin $display("[Error] PWL 없음: %s", pwl_file); $finish; end
    #2000;
    while(!$feof(fh)) begin
      sc=$fscanf(fh,"%f %f",t_pwl,v_pwl);
      if(sc==2) begin
        t_ns=t_pwl*1.0e9;
        if(t_ns>$realtime) #(t_ns-$realtime);
        v_ecg_pos=v_pwl;
        if($realtime>=endsec*1.0e9) break;
      end
    end
    $fclose(fh);
  end

  // ── core 제어 타임라인 + 판정 읽기 ──
  initial begin : CTRL
    startsec=2.0; endsec=12.0;
    void'($value$plusargs("startsec=%f", startsec));
    void'($value$plusargs("endsec=%f", endsec));
    rst=1; sample_valid=0; rhythm_tick=0; segment_start=0; segment_done=0; core_active=0;
    repeat(8) @(posedge core_clk); @(negedge core_clk); rst=0;
    // HPF 정착 대기
    #(startsec*1.0e9);
    @(negedge core_clk); segment_start=1'b1; @(posedge core_clk); #1; segment_start=1'b0;
    core_active=1'b1;
    // 정착~끝까지 깨끗한 ECG 전달
    #((endsec-startsec)*1.0e9);
    core_active=1'b0;
    #2000;   // 마지막 펄스 정리 여유
    @(negedge core_clk); segment_done=1'b1; @(posedge core_clk); #1; segment_done=1'b0;
    repeat(40) @(posedge core_clk);
    $display("MIXED_RESULT pwl=%s startsec=%.1f endsec=%.1f pred_valid=%0d pred_class=%0d",
             pwl_file, startsec, endsec, pred_valid, pred_class);
    $finish;
  end
endmodule
