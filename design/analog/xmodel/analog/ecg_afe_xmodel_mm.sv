// ================================================================
//  [1.2] R/C mismatch 스윕용 AFE 변형 (ecg_afe_xmodel.sv 기반)
//   parameter real MM = mismatch 분율(0.001=0.1%). 최악방향 섭동:
//     IA diff-amp(R5/R7/R8/R9)·이득(R2/R4)·Twin-T(RT/CT/RB/CB)를 (1±MM)로.
//   원본과 동일 구조, 값만 MM 적용. x_opamp는 원본 재사용(별 컴파일).
// ================================================================
`timescale 1ns/1ns
import xmodel_pkg::*;

module ecg_afe_xmodel_mm #(parameter real MM = 0.0) (
    input  real v_ecg_pos,
    input  real v_ecg_neg,
    input  wire clk_samp,
    output logic [11:0] adc_data
);
    localparam real P = 1.0 + MM;   // plus 방향
    localparam real N = 1.0 - MM;   // minus 방향

    xreal ana_pos, ana_neg, gnd;
    xreal n_hpfp, n_hpfn, n_fb1, n_fb2, n_u1out, n_u2out;
    xreal n_u3p, n_u3n, ia_out;
    xreal n_tT1, n_tB1, n_notch, n_notch_buf, n_k, vk, n_bw, buf_out;

    real gnd_val = 0.0;
    real_to_xreal GND_CONV (.out(gnd), .in(gnd_val));
    real_to_xreal POS_CONV (.out(ana_pos), .in(v_ecg_pos));
    real_to_xreal NEG_CONV (.out(ana_neg), .in(v_ecg_neg));

    // HPF (매칭 민감 아님 — 원본값 유지)
    capacitor #(.C(33e-9)) C1 (ana_pos, n_hpfp);
    resistor  #(.R(10e6))  R6 (n_hpfp,  gnd);
    capacitor #(.C(33e-9)) C2 (ana_neg, n_hpfn);
    resistor  #(.R(10e6))  R3 (n_hpfn,  gnd);

    // IA 1단 — 이득저항 비대칭(R2 vs R4)
    resistor #(.R(100e3*P)) R2 (n_u1out, n_fb1);
    resistor #(.R(1e3))     Rg (n_fb1,   n_fb2);
    resistor #(.R(100e3*N)) R4 (n_u2out, n_fb2);
    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U1 (.inp(n_hpfp), .inn(n_fb1), .out(n_u1out));
    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U2 (.inp(n_hpfn), .inn(n_fb2), .out(n_u2out));

    // IA 2단 차동증폭 — R8/R7 ≠ R9/R5 최악 mismatch (CMRR 지배 요인)
    resistor #(.R(10e3*N)) R7 (n_u2out, n_u3n);
    resistor #(.R(10e3*P)) R8 (n_u3n,   ia_out);
    resistor #(.R(10e3*P)) R5 (n_u1out, n_u3p);
    resistor #(.R(10e3*N)) R9 (n_u3p,   gnd);
    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U3 (.inp(n_u3p), .inn(n_u3n), .out(ia_out));

    // 60Hz 능동 Twin-T — R/C 비대칭(노치 detune)
    resistor  #(.R(26.526e3*P)) RT1 (ia_out, n_tT1);
    resistor  #(.R(26.526e3*N)) RT2 (n_tT1,  n_notch);
    capacitor #(.C(200e-9*P))   CT  (n_tT1,  vk);
    capacitor #(.C(100e-9*N))   CB1 (ia_out, n_tB1);
    capacitor #(.C(100e-9*P))   CB2 (n_tB1,  n_notch);
    resistor  #(.R(13.263e3*N)) RB  (n_tB1,  vk);

    // 노치 버퍼 + 부트스트랩 + LPF (원본값)
    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U_nbuf (.inp(n_notch), .inn(n_notch_buf), .out(n_notch_buf));
    resistor #(.R(5e3))  Rk1 (n_notch_buf, n_k);
    resistor #(.R(95e3)) Rk2 (n_k, gnd);
    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U_nB (.inp(n_k), .inn(vk), .out(vk));
    resistor  #(.R(1e3))     R_lpf (n_notch_buf, n_bw);
    capacitor #(.C(1.06e-6)) C_lpf (n_bw, gnd);
    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U_buf (.inp(n_bw), .inn(buf_out), .out(buf_out));

    // 12-bit SAR ADC
    real real_buf_out;
    xreal_to_real BUF_CONV (.out(real_buf_out), .in(buf_out));
    always @(negedge clk_samp) begin : ADC_SAMPLE
        integer q;
        q = $rtoi(((real_buf_out + 1.65) / 3.3) * 4095.0);
        if      (q > 4095) adc_data <= 12'd4095;
        else if (q < 0)    adc_data <= 12'd0;
        else               adc_data <= q[11:0];
    end
endmodule
