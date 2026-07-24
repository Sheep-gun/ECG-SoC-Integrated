// ================================================================
//  [2.4] op-amp finite GBW / input offset 모델 AFE 변형
//   x_opamp_ni: 원본 vcvs 모델 + 단일 dominant pole(유한 GBW) + 입력 offset(VOS).
//     pole f_p = GBW_HZ / A_OL_LIN (RC로 구현), 폐루프 대역 = GBW/이득.
//   ecg_afe_xmodel_op: 전 opamp를 x_opamp_ni로, GBW_HZ 공통, VOS는 U1(+)/U2(−) 차동.
//   parameter: GBW_HZ(기본 1e9=이상), VOS(기본 0). vsim -g로 오버라이드.
// ================================================================
`timescale 1ns/1ns
import xmodel_pkg::*;

module x_opamp_ni #(
    parameter real A_OL_DB = 100.0,
    parameter real CMRR_DB = 110.0,
    parameter real VCC     =  1.65,
    parameter real VEE     = -1.65,
    parameter real GBW_HZ  = 1.0e9,   // 유한 GBW (기본 사실상 이상)
    parameter real VOS     = 0.0      // 입력 오프셋 [V]
)(
    input  xreal inp,
    input  xreal inn,
    output xreal out
);
    localparam real PI       = 3.14159265358979;
    localparam real A_OL_LIN = 10.0 ** (A_OL_DB / 20.0);
    localparam real CMRR_LIN = 10.0 ** (CMRR_DB / 20.0);
    localparam real A_CM     = A_OL_LIN / (2.0 * CMRR_LIN);
    localparam real FP       = GBW_HZ / A_OL_LIN;        // dominant pole [Hz]
    localparam real RP       = 1000.0;
    localparam real CP       = 1.0 / (2.0 * PI * FP * RP);

    xreal gnd_n, vos_x, n1, n2, n3, osum, opole;
    real  zero = 0.0;
    real  vos_r = VOS;
    real_to_xreal GN (.out(gnd_n), .in(zero));
    real_to_xreal VN (.out(vos_x), .in(vos_r));

    // V(osum) = A_OL·(inp−inn) + A_OL·VOS + A_CM·inp + A_CM·inn
    vcvs #(.scale(A_OL_LIN)) Ediff (.pos(osum), .neg(n1),    .in_pos(inp),   .in_neg(inn));
    vcvs #(.scale(A_OL_LIN)) Eos   (.pos(n1),   .neg(n2),    .in_pos(vos_x), .in_neg(gnd_n));
    vcvs #(.scale(A_CM))     Ecm1  (.pos(n2),   .neg(n3),    .in_pos(inp),   .in_neg(gnd_n));
    vcvs #(.scale(A_CM))     Ecm2  (.pos(n3),   .neg(gnd_n), .in_pos(inn),   .in_neg(gnd_n));

    // dominant pole (유한 GBW): RC 저역통과
    resistor  #(.R(RP)) Rp (osum,  opole);
    capacitor #(.C(CP)) Cp (opole, gnd_n);

    // 출력 저항 + 레일 리미터
    resistor #(.R(1.0)) Rout (opole, out);
    vlimit #(.Vmax(VCC), .Vmin(VEE)) LIM (out, gnd_n);
endmodule


module ecg_afe_xmodel_op #(parameter real GBW_HZ = 1.0e9, parameter real VOS = 0.0) (
    input  real v_ecg_pos,
    input  real v_ecg_neg,
    input  wire clk_samp,
    output logic [11:0] adc_data
);
    xreal ana_pos, ana_neg, gnd;
    xreal n_hpfp, n_hpfn, n_fb1, n_fb2, n_u1out, n_u2out;
    xreal n_u3p, n_u3n, ia_out;
    xreal n_tT1, n_tB1, n_notch, n_notch_buf, n_k, vk, n_bw, buf_out;

    real gnd_val = 0.0;
    real_to_xreal GND_CONV (.out(gnd), .in(gnd_val));
    real_to_xreal POS_CONV (.out(ana_pos), .in(v_ecg_pos));
    real_to_xreal NEG_CONV (.out(ana_neg), .in(v_ecg_neg));

    capacitor #(.C(33e-9)) C1 (ana_pos, n_hpfp);
    resistor  #(.R(10e6))  R6 (n_hpfp,  gnd);
    capacitor #(.C(33e-9)) C2 (ana_neg, n_hpfn);
    resistor  #(.R(10e6))  R3 (n_hpfn,  gnd);

    resistor #(.R(100e3)) R2 (n_u1out, n_fb1);
    resistor #(.R(1e3))   Rg (n_fb1,   n_fb2);
    resistor #(.R(100e3)) R4 (n_u2out, n_fb2);
    // VOS: U1(+VOS)/U2(−VOS) 차동 입력 오프셋 최악
    x_opamp_ni #(.GBW_HZ(GBW_HZ), .VOS(+VOS)) U1 (.inp(n_hpfp), .inn(n_fb1), .out(n_u1out));
    x_opamp_ni #(.GBW_HZ(GBW_HZ), .VOS(-VOS)) U2 (.inp(n_hpfn), .inn(n_fb2), .out(n_u2out));

    resistor #(.R(10e3)) R7 (n_u2out, n_u3n);
    resistor #(.R(10e3)) R8 (n_u3n,   ia_out);
    resistor #(.R(10e3)) R5 (n_u1out, n_u3p);
    resistor #(.R(10e3)) R9 (n_u3p,   gnd);
    x_opamp_ni #(.GBW_HZ(GBW_HZ)) U3 (.inp(n_u3p), .inn(n_u3n), .out(ia_out));

    resistor  #(.R(26.526e3)) RT1 (ia_out, n_tT1);
    resistor  #(.R(26.526e3)) RT2 (n_tT1,  n_notch);
    capacitor #(.C(200e-9))   CT  (n_tT1,  vk);
    capacitor #(.C(100e-9))   CB1 (ia_out, n_tB1);
    capacitor #(.C(100e-9))   CB2 (n_tB1,  n_notch);
    resistor  #(.R(13.263e3)) RB  (n_tB1,  vk);

    x_opamp_ni #(.GBW_HZ(GBW_HZ)) U_nbuf (.inp(n_notch), .inn(n_notch_buf), .out(n_notch_buf));
    resistor #(.R(5e3))  Rk1 (n_notch_buf, n_k);
    resistor #(.R(95e3)) Rk2 (n_k, gnd);
    x_opamp_ni #(.GBW_HZ(GBW_HZ)) U_nB (.inp(n_k), .inn(vk), .out(vk));
    resistor  #(.R(1e3))     R_lpf (n_notch_buf, n_bw);
    capacitor #(.C(1.06e-6)) C_lpf (n_bw, gnd);
    x_opamp_ni #(.GBW_HZ(GBW_HZ)) U_buf (.inp(n_bw), .inn(buf_out), .out(buf_out));

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
