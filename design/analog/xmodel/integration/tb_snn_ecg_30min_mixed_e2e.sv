// =====================================================================
//  tb_snn_ecg_30min_mixed_e2e.sv
//  XMODEL AFE+ADC  --직접연결--  snn_ecg_30min_final_top (commit c6b80de)
//
//  목적 : 팀원 요청(1)의 "직접 통합" End-to-End 검증.
//         파일 재생(file-replay)이 아니라, 아날로그 ECG PWL을 XMODEL AFE에
//         실제로 통과시켜 얻은 12-bit ADC code를 같은 testbench 안에서
//         곧바로 RTL top으로 흘려보낸다.
//
//  파이프라인:
//    ECG PWL -> ecg_afe_xmodel -> 12b offset-binary ADC
//            -> signed 변환 {~adc[11],adc[10:0]}
//            -> sample_valid/sample_ready handshake
//            -> snn_ecg_30min_final_top -> final_pred_class + 4 Final Membrane
//
//  산출:
//    - +dump=<file> : RTL이 "실제로 수락한" signed 12-bit code를 3-hex/줄로 저장
//                     (== golden .mem과 동일 포맷) -> SHA256 비교용
//    - E2E_RESULT   : case_id, final_valid, final_pred_class, 4 membrane,
//                     accepted_samples, windows, decisions, prof cadence
//
//  중요(정직성):
//    * class/membrane의 bit-exact는 "수락된 1.8M signed code 시퀀스"에만 의존한다.
//      RTL clock cadence(=prof_total_cycles)는 golden(sample_gap_cycles=2)과
//      다를 수 있으며 그것은 분류 결과에 영향을 주지 않는다. 실제 cadence는
//      아래에서 그대로 로그로 남긴다(요청 사항).
//    * 이 TB는 "AFE 샘플 1개당 RTL 수락 1개"를 보장한다(1.8M accepted samples).
// =====================================================================
`timescale 1ns/1ns

module tb_snn_ecg_30min_mixed_e2e #(
    parameter integer ADC_WIDTH            = 12,
    parameter integer SNAPSHOT_SAMPLES     = 60000,
    parameter integer SNAPSHOTS_PER_CHUNK  = 30,
    parameter integer POST_DONE_TICKS      = 37,
    parameter integer EXPECTED_SAMPLES     = 1800000,
    // AFE 1kSPS 샘플 주기(ns). 1 kHz -> 1e6 ns.
    parameter integer AFE_SAMPLE_PERIOD_NS = 1000000,
    // RTL core clock 반주기(ns). 핵심: AFE 실시간 전체를 100MHz로 돌리면 사이클 폭발
    //  (30분 = 1800억 clk). core는 handshake 기반이므로 샘플(1ms)당 ~20 clock이면 충분.
    //  25us 반주기 -> 50us 주기 -> 1ms당 20 core clock. 30분에도 ~3600만 clock으로 실행가능.
    parameter integer CORE_CLK_HALF_NS     = 25000,
    // HPF 등 AFE 정착(settling) 대기 시간(초). 오프라인 생성기와 동일하게 맞춘다.
    parameter real    SETTLING_SKIP_SEC    = 2.0
)();

  // ---------------- 신호 ----------------
  real  v_ecg_pos, v_ecg_neg;      // 차동 ECG 입력(AFE)
  reg   samp_clk;                  // AFE 1kSPS 샘플 클럭
  wire [ADC_WIDTH-1:0] afe_adc;    // AFE offset-binary ADC 출력

  reg   clk, rst, start, sample_valid;
  reg  signed [ADC_WIDTH-1:0] adc_data;
  wire  sample_ready, busy, final_valid;
  wire [1:0] final_pred_class;
  wire signed [31:0] final_mem_nsr, final_mem_chf, final_mem_arr, final_mem_aff;
  wire [5:0] snapshot_index_dbg;
  wire [63:0] prof_total_cycle_counter, prof_busy_cycle_counter, prof_run_cycle_counter,
              prof_input_wait_cycle_counter, prof_accepted_sample_counter,
              prof_window_counter, prof_decision_counter,
              prof_last_window_latency, prof_max_window_latency, prof_last_decision_latency;

  // signed 변환(=README, 기존 어댑터와 동일): offset-binary -> 2의보수
  wire signed [ADC_WIDTH-1:0] afe_adc_signed = {~afe_adc[ADC_WIDTH-1], afe_adc[ADC_WIDTH-2:0]};

  // ---------------- AFE (아날로그, XMODEL) ----------------
  ecg_afe_xmodel AFE (
      .v_ecg_pos (v_ecg_pos),
      .v_ecg_neg (v_ecg_neg),
      .clk_samp  (samp_clk),
      .adc_data  (afe_adc)
  );

  // ---------------- DUT: 신 top (c6b80de) ----------------
  snn_ecg_30min_final_top #(
      .ADC_WIDTH(ADC_WIDTH),
      .SNAPSHOT_SAMPLES(SNAPSHOT_SAMPLES),
      .SNAPSHOTS_PER_CHUNK(SNAPSHOTS_PER_CHUNK),
      .POST_DONE_TICKS(POST_DONE_TICKS),
      .PROFILE_EN(1),
      .PROF_COUNTER_W(64)
  ) dut (
      .clk(clk), .rst(rst), .start(start),
      .sample_valid(sample_valid), .adc_data(adc_data),
      .sample_ready(sample_ready), .busy(busy),
      .final_valid(final_valid), .final_pred_class(final_pred_class),
      .final_mem_nsr(final_mem_nsr), .final_mem_chf(final_mem_chf),
      .final_mem_arr(final_mem_arr), .final_mem_aff(final_mem_aff),
      .snapshot_index_dbg(snapshot_index_dbg),
      .prof_total_cycle_counter(prof_total_cycle_counter),
      .prof_busy_cycle_counter(prof_busy_cycle_counter),
      .prof_run_cycle_counter(prof_run_cycle_counter),
      .prof_input_wait_cycle_counter(prof_input_wait_cycle_counter),
      .prof_accepted_sample_counter(prof_accepted_sample_counter),
      .prof_window_counter(prof_window_counter),
      .prof_decision_counter(prof_decision_counter),
      .prof_last_window_latency(prof_last_window_latency),
      .prof_max_window_latency(prof_max_window_latency),
      .prof_last_decision_latency(prof_last_decision_latency)
  );

  // ---------------- 클럭 ----------------
  initial begin clk = 1'b0; forever #(CORE_CLK_HALF_NS) clk = ~clk; end
  // AFE 1kSPS: 반주기마다 토글 -> negedge에서 새 ADC code 확정(모듈 구현에 맞춤)
  initial begin
    samp_clk = 1'b0;
    forever begin
      #(AFE_SAMPLE_PERIOD_NS/2) samp_clk = 1'b1;
      #(AFE_SAMPLE_PERIOD_NS/2) samp_clk = 1'b0;
    end
  end

  // ---------------- plusargs ----------------
  string pwl_file, dump_file, case_name;
  integer case_id, expected_class;
  initial begin
    pwl_file  = "ecg.pwl";
    dump_file = "accepted_adc.mem";
    case_name = "CASE";
    case_id = 0; expected_class = 0;
    void'($value$plusargs("pwl=%s",       pwl_file));
    void'($value$plusargs("dump=%s",      dump_file));
    void'($value$plusargs("case=%s",      case_name));
    void'($value$plusargs("case_id=%d",   case_id));
    void'($value$plusargs("expected=%d",  expected_class));
  end

  // ---------------- ECG PWL -> AFE 입력 ----------------
  // PWL 형식: "<time_sec> <volt>" 한 줄에 하나(단조 증가 time).
  integer fh, sc;
  real t_pwl, v_pwl, t_ns;
  initial begin : STIM
    v_ecg_pos = 0.0; v_ecg_neg = 0.0;
    #1;
    fh = $fopen(pwl_file, "r");
    if (fh == 0) begin $display("FAIL cannot open PWL: %s", pwl_file); $finish; end
    while (!$feof(fh)) begin
      sc = $fscanf(fh, "%f %f\n", t_pwl, v_pwl);
      if (sc == 2) begin
        t_ns = t_pwl * 1.0e9;
        if (t_ns > $realtime) #(t_ns - $realtime);
        v_ecg_pos = v_pwl;   // 단극 구동(neg=0). 차동 구동 시 v_ecg_neg도 세팅.
      end
    end
    $fclose(fh);
  end

  // ---------------- 수락 샘플 dump ----------------
  integer dump_fd;
  integer accepted;
  initial begin accepted = 0; dump_fd = $fopen(dump_file, "w");
    if (dump_fd == 0) begin $display("FAIL cannot open dump: %s", dump_file); $finish; end
  end

  // 한 handshake 수락 시 3-hex로 기록(음수는 12b 2의보수 & 0xFFF)
  task dump_accepted(input signed [ADC_WIDTH-1:0] s);
    reg [ADC_WIDTH-1:0] u;
    begin u = s; $fdisplay(dump_fd, "%03h", u); accepted = accepted + 1; end
  endtask

  // ---------------- 통제 타임라인 + 샘플 구동 ----------------
  // AFE 샘플 1개당 RTL 수락 1개. settling 후 start, 이후 매 AFE 샘플에서
  // sample_ready를 기다렸다가 정확히 1회 handshake.
  integer i;
  real    t_first_accept_ns, t_last_accept_ns;
  reg     armed;
  initial begin : CTRL
    rst = 1'b1; start = 1'b0; sample_valid = 1'b0; adc_data = 0; armed = 1'b0;
    t_first_accept_ns = 0.0; t_last_accept_ns = 0.0;
    // 리셋
    repeat (8) @(posedge clk);
    @(negedge clk); rst = 1'b0;

    // HPF/노치 정착 대기(오프라인 생성기의 settling_skip_sec과 동일하게)
    #(SETTLING_SKIP_SEC * 1.0e9);

    // start 펄스
    @(negedge clk); start = 1'b1; @(posedge clk); #1; @(negedge clk); start = 1'b0;
    armed = 1'b1;

    // 정확히 EXPECTED_SAMPLES개를 AFE 페이스로 공급
    for (i = 0; i < EXPECTED_SAMPLES; i = i + 1) begin
      @(negedge samp_clk);           // 새 AFE ADC code 확정 시점
      adc_data     = afe_adc_signed; // 이번 샘플 값 래치
      // sample_ready가 될 때까지 대기 후 1회 수락
      sample_valid = 1'b0;
      @(negedge clk);
      while (sample_ready !== 1'b1) @(negedge clk);
      sample_valid = 1'b1;           // 이 사이클에서 수락(ready&&valid)
      if (accepted == 0) t_first_accept_ns = $realtime;
      dump_accepted(adc_data);
      @(posedge clk); #1;
      t_last_accept_ns = $realtime;
      @(negedge clk); sample_valid = 1'b0;
    end

    // 남은 파이프라인 진행 -> final_valid 대기
    i = 0;
    while ((final_valid !== 1'b1) && (i < 200000)) begin @(posedge clk); i = i + 1; end

    $fclose(dump_fd);

    // ---- 결과/카 ден스 로그 ----
    $display("E2E_RESULT case=%0s case_id=%0d expected=%0d final_valid=%0d pred=%0d mem_nsr=%0d mem_chf=%0d mem_arr=%0d mem_aff=%0d accepted=%0d dumped=%0d windows=%0d decisions=%0d",
             case_name, case_id, expected_class, final_valid, final_pred_class,
             final_mem_nsr, final_mem_chf, final_mem_arr, final_mem_aff,
             prof_accepted_sample_counter, accepted,
             prof_window_counter, prof_decision_counter);
    $display("E2E_CADENCE case=%0s prof_total_cycles=%0d prof_run_cycles=%0d prof_input_wait_cycles=%0d accepted_samples=%0d avg_cycles_per_accept=%0d note=AFE_1kSPS_paced(golden_ref_gap=2)",
             case_name, prof_total_cycle_counter, prof_run_cycle_counter,
             prof_input_wait_cycle_counter, prof_accepted_sample_counter,
             (prof_accepted_sample_counter>0)? (prof_total_cycle_counter/prof_accepted_sample_counter):0);
    $display("E2E_TIMING case=%0s first_accept_ns=%0.0f last_accept_ns=%0.0f", case_name, t_first_accept_ns, t_last_accept_ns);
    $finish;
  end

  // ---------------- 안전 타임아웃 ----------------
  initial begin
    // 30분 sim + 여유. AFE 1kSPS x 1.8M = 1800s sim-time = 1.8e12 ns. 2.2e12로 여유.
    #(2200000000000.0);
    $display("E2E_TIMEOUT case=%0s accepted=%0d final_valid=%0d snapshot=%0d", case_name, accepted, final_valid, snapshot_index_dbg);
    $finish;
  end

endmodule
