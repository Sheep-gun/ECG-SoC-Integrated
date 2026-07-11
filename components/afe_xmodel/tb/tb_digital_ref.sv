// 디지털 단독 기준 TB: 원본 .mem(signed)을 core에 직접 주입 (AFE 없음).
//  팀원 dataset tb의 drive_sample 프로토콜 그대로 → core 분류 기준치 확보.
//  plusarg: +mem=<.mem 파일> +nsamp=<샘플수>
`timescale 1ns/1ns
module tb_digital_ref;
  reg clk, rst, sample_valid, rhythm_tick, segment_start, segment_done;
  reg signed [11:0] adc_data;
  wire [1:0] pred_class; wire pred_valid;
  reg [11:0] mem [0:60000-1];
  string mem_file; integer nsamp, i, startidx;

  snn_ecg_model_a_plus_core CORE(.clk(clk), .rst(rst), .sample_valid(sample_valid),
    .rhythm_tick(rhythm_tick), .segment_start(segment_start), .segment_done(segment_done),
    .adc_data(adc_data), .pred_class(pred_class), .pred_valid(pred_valid));

  initial begin clk=0; forever #5 clk=~clk; end

  task drive_sample(input [11:0] v);
    begin
      @(negedge clk); adc_data=v; sample_valid=1; rhythm_tick=1;
      @(posedge clk); #1; sample_valid=0; rhythm_tick=0;
    end
  endtask

  initial begin
    mem_file="x.mem"; nsamp=60000; startidx=0;
    void'($value$plusargs("mem=%s", mem_file));
    void'($value$plusargs("nsamp=%d", nsamp));
    void'($value$plusargs("start=%d", startidx));
    rst=1; sample_valid=0; rhythm_tick=0; segment_start=0; segment_done=0; adc_data=0;
    $readmemh(mem_file, mem);
    repeat(4) @(posedge clk); @(negedge clk); rst=0;
    @(negedge clk); segment_start=1; @(posedge clk); #1; segment_start=0;
    for(i=startidx;i<startidx+nsamp;i=i+1) drive_sample(mem[i]);
    @(negedge clk); segment_done=1; @(posedge clk); #1; segment_done=0;
    repeat(40) @(posedge clk);
    $display("DIGREF mem=%s nsamp=%0d pred_valid=%0d pred_class=%0d", mem_file, nsamp, pred_valid, pred_class);
    $finish;
  end
endmodule
