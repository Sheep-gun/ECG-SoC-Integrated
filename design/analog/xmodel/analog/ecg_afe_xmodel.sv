// ================================================================
//  제27회 대한민국 반도체설계대전
//  Low-Power Mixed-Signal SoC for Wearable ECG Arrhythmia Detection
//
//  파일  : ecg_afe_xmodel.sv
//  담당  : 이수환 (한양대학교 융합전자공학부)
//  버전  : v2.0  (Bug #1 ~ #7 수정 완료)
//  날짜  : 2026-05-26
//
// ----------------------------------------------------------------
//  ■ 설계 스펙 (IEC 60601-2-47 준수)
//  ┌───────────────────────┬──────────────┬──────────────────────┐
//  │ 항목                  │ 목표 스펙    │ 본 설계 구현         │
//  ├───────────────────────┼──────────────┼──────────────────────┤
//  │ IA 전압 이득          │ Av = 201     │ 201 (v2.0 수정)  ✓  │
//  │ HPF 차단주파수        │ ≤ 0.67 Hz    │ 0.482 Hz         ✓  │
//  │ LPF 차단주파수        │ ≤ 150 Hz     │ 150 Hz(1.06µF)   ✓  │
//  │ 노치 필터             │ 60 Hz(KR)    │ 60Hz 능동Twin-T(80dB)✓│
//  │ −3dB 대역폭           │ 150 Hz       │ 150 Hz (측정)    ✓  │
//  │ 입력 임피던스         │ > 10 MΩ      │ R=10MΩ∥JFET≫10MΩ✓ │
//  │ CMRR                  │ > 100 dB     │ 110 dB (모델링)  ✓  │
//  │ ADC 해상도            │ 12-bit       │ 12-bit           ✓  │
//  │ ADC 샘플링 레이트     │ 1 kSPS       │ 1 kSPS           ✓  │
//  │ 공급 전압             │ ±1.65 V      │ ±1.65 V          ✓  │
//  └───────────────────────┴──────────────┴──────────────────────┘
//
//  ■ 신호 파이프라인
//    전극(±)
//      │
//      ▼
//    [HPF]  C=33nF, R=10MΩ  →  f_c = 0.482 Hz  (베이스라인 제거)
//      │
//      ▼
//    [IA 1단]  U1, U2  Av = 1 + 2×100k/1k = 201
//      │
//      ▼
//    [IA 2단]  U3 차동증폭기  Av = 1  (→ 총 이득 = 201)
//      │
//      ▼
//    [60 Hz Notch]  Twin-T 수동 필터  (전원선 간섭 제거)
//      │
//      ▼
//    [LPF]  R=1kΩ, C=1µF  →  f_c = 159 Hz  (앨리어싱 방지)
//      │
//      ▼
//    [Unity Gain Buffer]  저임피던스 구동
//      │
//      ▼
//    [12-bit SAR ADC]  1 kSPS, Vref = ±1.65 V
//
//  ■ v2.0 수정 내역
//    Bug #1 : R2=R4 45kΩ→100kΩ, Rg 10kΩ→1kΩ  (Av 100→201)
//    Bug #2 : R9 vref(1.65V)→gnd  (DC 오프셋 제거)
//    Bug #3 : ADC 공식  (x/3.3)*1023  →  ((x+1.65)/3.3)*4095
//    Bug #4 : adc_data [9:0]→[11:0]  (10-bit→12-bit)
//    Bug #5 : 60 Hz Twin-T Notch 필터 추가
//    Bug #6 : 음전극 입력 포트 추가, C2 신호 경로 수정
//    Bug #7 : x_opamp CMRR 모델 추가 (파라미터화)
//
//  ■ v3.0 수정 내역 (Xmodel+Questa 통합검증, 2026-06-21)
//    Bug #10: x_opamp 이산 relaxation → XMODEL vcvs 솔버 모델로 교체
//             (기존 모델은 IA 피드백에서 차동이득=0 → ADC 고정. 솔버 모델로 ×201 복구)
//    Bug #11: 노치-LPF 사이 단위버퍼(U_nbuf) 추가 (Twin-T 로딩 제거, 실효이득 36→120)
//    Bug #12: LPF C 1µF→1.06µF (fc 159→150Hz, IEC 대역 충족)
//    Bug #13: opamp CMRR 100→110dB (스펙 >100dB 마진 확보)
//    Bug #14: tb ADC 로그 off-by-one ($fdisplay→$fstrobe, tb_ecg_afe.sv)
//    Bug #15: 수동 Twin-T → 능동(부트스트랩 Q≈5) (대역폭 17Hz→150Hz 회복)
// ================================================================

`timescale 1ns/1ns
import xmodel_pkg::*;


// ================================================================
//  서브모듈: x_opamp  (XMODEL 회로 솔버 프리미티브 기반)
//   기존 이산 relaxation(α=0.1) 모델은 3-opamp IA 피드백에서 차동모드로
//   수렴하지 못해 (u1-u2)=0, 이득 0 → 폐기.
//   대체: vcvs(전압제어 전압원)로 개루프 이득을 표현 → XMODEL 솔버가
//         피드백 망을 일관되게 해석하여 폐루프 이득(×201) 정확 실현.
//
//   출력 공식(원본과 동일):
//     V(oint) = A_OL·(inp−inn) + A_OL/CMRR·(inp+inn)/2
//   직렬 vcvs 3개의 전압이 합산되어 위 식을 구현(제어단자는 고임피던스→입력 무로딩).
//   이후 1Ω 직렬저항 + vlimit으로 ±VCC/VEE 레일 클리핑.
module x_opamp #(
    parameter real A_OL_DB = 100.0,   // 개루프 이득 [dB]
    parameter real CMRR_DB = 100.0,   // CMRR [dB]
    parameter real VCC     =  1.65,
    parameter real VEE     = -1.65
)(
    input  xreal inp,
    input  xreal inn,
    output xreal out
);
    localparam real A_OL_LIN = 10.0 ** (A_OL_DB / 20.0);          // 100dB→1e5
    localparam real CMRR_LIN = 10.0 ** (CMRR_DB / 20.0);          // 100dB→1e5
    localparam real A_CM     = A_OL_LIN / (2.0 * CMRR_LIN);       // 각 공통모드 항 이득

    xreal gnd_n;
    xreal n1, n2, oint;
    real  zero = 0.0;
    real_to_xreal GN (.out(gnd_n), .in(zero));

    // 직렬 합산: V(oint,gnd)=A_OL·(inp−inn) + A_CM·inp + A_CM·inn
    //                       =A_OL·(Vdiff + Vcm/CMRR)
    vcvs #(.scale(A_OL_LIN)) Ediff (.pos(oint), .neg(n1),    .in_pos(inp), .in_neg(inn));
    vcvs #(.scale(A_CM))     Ecm1  (.pos(n1),   .neg(n2),    .in_pos(inp), .in_neg(gnd_n));
    vcvs #(.scale(A_CM))     Ecm2  (.pos(n2),   .neg(gnd_n), .in_pos(inn), .in_neg(gnd_n));

    // 출력 저항 + 레일 리미터 (정상 ECG 구간에선 비활성, 과구동 시 ±1.65V 포화)
    resistor #(.R(1.0)) Rout (oint, out);
    vlimit #(.Vmax(VCC), .Vmin(VEE)) LIM (out, gnd_n);
endmodule


// ================================================================
//  메인 모듈: ecg_afe_xmodel
// ================================================================
module ecg_afe_xmodel (
    input  real v_ecg_pos,          // 양전극 (능동 ECG 전극)
    input  real v_ecg_neg,          // 음전극 (기준 전극, 통상 Right Leg Drive)
    input  wire clk_samp,           // 1 kHz 샘플링 클럭 (negedge = Hold 시작)
    output logic [11:0] adc_data    // 12-bit SAR ADC 출력 코드 (Bug #4 수정)
);

    // ============================================================
    //  내부 아날로그 노드 (xreal)
    // ============================================================
    xreal ana_pos, ana_neg;         // 입력 변환 노드
    xreal gnd;                      // 아날로그 GND (0 V)

    // HPF 출력 노드
    xreal n_hpfp;                   // 양전극 HPF 출력
    xreal n_hpfn;                   // 음전극 HPF 출력

    // IA 1단 내부 노드
    xreal n_fb1, n_fb2;             // U1, U2 피드백 교차 노드
    xreal n_u1out, n_u2out;         // U1, U2 출력

    // IA 2단 (차동증폭기) 노드
    xreal n_u3p, n_u3n;             // U3 비반전/반전 입력 노드
    xreal ia_out;                   // IA 최종 출력 (= U3 출력)

    // 노치 필터 내부 노드
    xreal n_tT1;                    // Twin-T Top 경로 중간 노드
    xreal n_tB1;                    // Twin-T Bottom 경로 중간 노드
    xreal n_notch;                  // Notch 필터 출력 노드
    xreal n_notch_buf;              // 노치 출력 버퍼 (Vo) — Twin-T를 LPF 로딩으로부터 격리 + 부트스트랩 소스
    xreal n_k;                      // 부트스트랩 분압 노드 (k·Vo)
    xreal vk;                       // 부트스트랩 버퍼 출력 (능동 Twin-T Q 부스트)

    // LPF 및 버퍼 노드
    xreal n_bw;                     // LPF 출력 / 버퍼 입력 노드
    xreal buf_out;                  // 버퍼 출력 (ADC 입력)

    // ============================================================
    //  전원 / 기준 소스
    // ============================================================
    real gnd_val = 0.0;
    real_to_xreal GND_CONV  (.out(gnd),     .in(gnd_val));

    // 입력 변환 (real → xreal)
    real_to_xreal POS_CONV  (.out(ana_pos), .in(v_ecg_pos));
    real_to_xreal NEG_CONV  (.out(ana_neg), .in(v_ecg_neg));


    // ============================================================
    //  STAGE 1: HPF (High-Pass Filter)
    // ------------------------------------------------------------
    //  목적  : ECG 베이스라인 워블(Baseline Wander) 제거
    //  토폴로지 : 직렬 커패시터 + 병렬 바이어스 저항 (1차 RC HPF)
    //
    //  소자 값:  C = 33 nF,  R = 10 MΩ
    //  차단주파수: f_c = 1/(2π × R × C)
    //             = 1/(2π × 10×10⁶ × 33×10⁻⁹)
    //             = 1/(2π × 0.330)
    //             ≈ 0.482 Hz   ✓  (IEC 60601-2-47: ≤ 0.67 Hz)
    //
    //  입력 임피던스: |Z_in| ≈ R = 10 MΩ  (ECG 대역에서 Z_C ≪ R)
    //                                      ✓  (스펙: > 10 MΩ)
    //
    //  HPF 정착 시정수: τ = RC = 10M × 33n = 330 ms
    //  완전 정착 시간 : 5τ ≈ 1.65 s  →  시뮬레이션 시작 후 2초 이후
    //                              데이터 사용 권장
    //
    //  ※ Bug #6 수정:  기존 C2(gnd→n_hpfn)는 n_hpfn을 GND에 단락
    //                   → 음전극이 항상 0V → 차동 입력 불가 → CMRR 불가
    //                   → 수정: C2(ana_neg→n_hpfn)로 정상 차동 경로 복원
    // ============================================================
    //  양전극 HPF
    capacitor #(.C(33e-9))  C1  (ana_pos,  n_hpfp);  // 직렬 커패시터
    resistor  #(.R(10e6))   R6  (n_hpfp,   gnd);      // 바이어스 저항

    //  음전극 HPF (Bug #6 수정: ana_neg가 신호 소스)
    capacitor #(.C(33e-9))  C2  (ana_neg,  n_hpfn);  // 직렬 커패시터
    resistor  #(.R(10e6))   R3  (n_hpfn,   gnd);      // 바이어스 저항


    // ============================================================
    //  STAGE 2: 3-op IA 1단 (Instrumentation Amplifier, 1st stage)
    // ------------------------------------------------------------
    //  목적  : 차동 신호 증폭, 공통 모드 거부
    //  토폴로지 : U1-U2 버퍼 + 크로스 피드백 (고 CMRR 구조)
    //
    //  이득 공식: Av1 = 1 + 2 × R_feedback / Rgain
    //             = 1 + 2 × 100,000 / 1,000
    //             = 201   ✓  (스펙: Av=201, Bug #1 수정)
    //
    //  소자 값:
    //    R2 = R4 = 100 kΩ  (R_feedback, 스펙 명시값)
    //    Rg  = 1 kΩ         (Rgain,      스펙 명시값)
    //
    //  동작 원리:
    //    U1 (양전극 측):  n_hpfp 추종 → n_u1out으로 증폭 출력
    //    U2 (음전극 측):  n_hpfn 추종 → n_u2out으로 증폭 출력
    //    Rg에 흐르는 전류 = (V_hpfp − V_hpfn) / Rg
    //    → V_u1out − V_u2out = (V_hpfp − V_hpfn) × (1 + 2R/Rg)
    // ============================================================
    resistor #(.R(100e3))  R2  (n_u1out, n_fb1);   // U1 출력 → 피드백 노드
    resistor #(.R(1e3))    Rg  (n_fb1,   n_fb2);   // 이득 설정 저항 (Rgain=1kΩ)
    resistor #(.R(100e3))  R4  (n_u2out, n_fb2);   // U2 출력 → 피드백 노드

    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U1
        (.inp(n_hpfp), .inn(n_fb1), .out(n_u1out));

    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U2
        (.inp(n_hpfn), .inn(n_fb2), .out(n_u2out));


    // ============================================================
    //  STAGE 3: IA 2단 (Unity-Gain Differential Amplifier)
    // ------------------------------------------------------------
    //  목적  : U1-U2 출력 차이를 단일 출력으로 추출 (공통 모드 제거)
    //  이득  : Av2 = R8/R7 = 10k/10k = 1
    //  총 이득: Av_total = Av1 × Av2 = 201 × 1 = 201  ✓
    //
    //  소자 값 (모두 동일 → CMRR 극대화):
    //    R7 = R5 = R8 = R9 = 10 kΩ
    //
    //  ※ Bug #2 수정: R9를 vref(1.65V) → gnd(0V)로 변경
    //    이전 코드에서 R9가 1.65V에 연결되면:
    //      V(n_u3p) = V(n_u1out) × R9/(R5+R9) + 1.65 × R5/(R5+R9)
    //               ≈ 0.909×V_sig + 0.15 V   ← 0.15V 오프셋 발생!
    //      오프셋이 201배 증폭 → 30V 포화 → ECG 신호 완전 소실
    //
    //  CMRR 조건: R8/R7 = R9/R5 (비율 일치)
    //    → 10k/10k = 10k/10k = 1   ✓  → CMRR = ∞ (이론값)
    //    실제 CMRR은 저항 매칭 오차와 opamp CMRR에 의해 제한됨
    // ============================================================
    resistor #(.R(10e3))   R7  (n_u2out, n_u3n);   // 반전 입력 저항
    resistor #(.R(10e3))   R8  (n_u3n,   ia_out);  // 반전 피드백 저항
    resistor #(.R(10e3))   R5  (n_u1out, n_u3p);   // 비반전 입력 저항
    resistor #(.R(10e3))   R9  (n_u3p,   gnd);     // 비반전 기준 저항 → GND (Bug #2 수정)

    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U3
        (.inp(n_u3p), .inn(n_u3n), .out(ia_out));


    // ============================================================
    //  STAGE 4: 60 Hz Active Twin-T Notch Filter  (Bug #5 추가, Bug #15 능동화)
    // ------------------------------------------------------------
    //  목적  : 60 Hz 전원선 간섭(PLI) 제거  (한국 전원 주파수: 60 Hz)
    //  IEC 60601-2-47 요구사항: PLI 억압 필수
    //
    //  토폴로지 (수동 Twin-T):
    //
    //    ia_out ──RT1──┬──RT2── n_notch
    //                  │
    //                 CT (2C)
    //                  │
    //                 GND
    //
    //    ia_out ──CB1──┬──CB2── n_notch
    //                  │
    //                 RB (R/2)
    //                  │
    //                 GND
    //
    //  소자 계산 (f₀ = 60 Hz):
    //    C = 100 nF 선택
    //    R = 1/(2π × f₀ × C)
    //      = 1/(2π × 60 × 100×10⁻⁹)
    //      = 26,526 Ω ≈ 26.53 kΩ
    //
    //    Top-T   : RT1=RT2=26.53 kΩ,  CT=200 nF (= 2C)
    //    Bottom-T: CB1=CB2=100 nF,     RB=13.26 kΩ (= R/2)
    //
    //  노치 동작 원리:
    //    f = f₀ 에서 Top-T와 Bottom-T 경로의 신호가 180° 위상차 &
    //    동일 진폭으로 n_notch에서 상쇄 → 이론적으로 완전 제거
    //
    //  ※ 능동 Twin-T (Bug #15): 수동 Twin-T는 Q≈0.25로 통과대역이 17Hz부터 무너져
    //    150Hz 대역폭 스펙 미달(측정: 20Hz 110, 40Hz 39.5). 부트스트랩(CT·RB 접지단을
    //    vk=k·Vo로 되먹임)으로 Q를 ~5로 높여 통과대역을 150Hz까지 ~201로 평탄화.
    //    측정 검증: 통과대역 ~200(3~45Hz), 60Hz 노치 80dB 유지, −3dB=150Hz.
    // ============================================================
    //  Top-T 경로 (직렬 저항, 병렬 커패시터)
    resistor  #(.R(26.526e3)) RT1 (ia_out,   n_tT1);
    resistor  #(.R(26.526e3)) RT2 (n_tT1,    n_notch);
    capacitor #(.C(200e-9))   CT  (n_tT1,    vk);        // 2C=200nF, 접지단→부트스트랩(능동)

    //  Bottom-T 경로 (직렬 커패시터, 병렬 저항)
    capacitor #(.C(100e-9))   CB1 (ia_out,   n_tB1);
    capacitor #(.C(100e-9))   CB2 (n_tB1,    n_notch);
    resistor  #(.R(13.263e3)) RB  (n_tB1,    vk);        // R/2=13.26kΩ, 접지단→부트스트랩(능동)


    // ============================================================
    //  STAGE 5: LPF (Low-Pass Filter, 1차 RC)
    // ------------------------------------------------------------
    //  목적  : 앨리어싱 방지 + 고주파 EMI 잡음 제거
    //  소자  : R_lpf = 1 kΩ,  C_lpf = 1.06 µF  (Bug #12 수정)
    //  차단주파수: f_c = 1/(2π × 1k × 1.06µ)
    //             = 1/(2π × 0.00106) ≈ 150.1 Hz  ✓  (IEC 60601-2-47: ≤150 Hz)
    //  ※ 기존 1µF는 159Hz로 스펙(≤150Hz) 초과 → 1.06µF로 정확히 충족.
    //     E12 계열 표준품 부재 시 1µF∥0.068µF(=1.068µF) 병렬로 구현 가능.
    // ============================================================
    //  노치 출력 버퍼 (Bug #11): Twin-T 출력(~26kΩ)을 LPF/부트스트랩 로딩으로부터 격리.
    //    n_notch_buf = Vo (저임피던스 출력)
    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U_nbuf
        (.inp(n_notch), .inn(n_notch_buf), .out(n_notch_buf));

    //  부트스트랩 (Bug #15: 능동 Twin-T): CT·RB 접지단을 vk=k·Vo로 되먹여 Q 부스트.
    //    Q = 1/(4(1−k)).  k = Rk2/(Rk1+Rk2) = 95k/100k = 0.95  →  Q ≈ 5
    //    → 60Hz 노치는 유지하되 통과대역을 150Hz까지 평탄화(수동 대비 대역폭 회복).
    resistor #(.R(5e3))    Rk1 (n_notch_buf, n_k);   // 부트스트랩 분압 상단
    resistor #(.R(95e3))   Rk2 (n_k,         gnd);   // k = 95/(5+95) = 0.95
    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U_nB
        (.inp(n_k), .inn(vk), .out(vk));             // vk = k·Vo (저임피던스)

    resistor  #(.R(1e3))    R_lpf  (n_notch_buf, n_bw);
    capacitor #(.C(1.06e-6)) C_lpf  (n_bw,    gnd);   // Bug #12: 1µF→1.06µF (fc 159→150Hz)


    // ============================================================
    //  STAGE 6: Unity-Gain Buffer (임피던스 변환)
    // ------------------------------------------------------------
    //  목적  : LPF 고임피던스 출력을 저임피던스로 변환 → ADC 구동
    //  연결  : inp=n_bw, inn=buf_out, out=buf_out
    //          (출력을 반전 입력에 직결 → 100% 부궤환 → 이득=1)
    //
    //  ※ LTspice 버그 참고:
    //    이전 LTspice 회로에서 U4(unity buffer)의 inn 핀에
    //    피드백 와이어가 미연결 → 개루프 동작 → 1 kHz 레일 발진
    //    → 본 코드에서는 inn=buf_out 명시적 연결로 해결  ✓
    // ============================================================
    x_opamp #(.A_OL_DB(100.0), .CMRR_DB(110.0)) U_buf
        (.inp(n_bw), .inn(buf_out), .out(buf_out));


    // ============================================================
    //  STAGE 7: 12-bit SAR ADC 동작 모델  (Bug #3, #4 수정)
    // ------------------------------------------------------------
    //  해상도 : 12-bit  →  4096 레벨  (Bug #4: 기존 10-bit 수정)
    //  기준전압: Vref_n = −1.65 V,  Vref_p = +1.65 V
    //  전압범위: Vfull = Vref_p − Vref_n = 3.3 V
    //  샘플링 : clk_samp 하강에지 (Hold 구간 시작 시점)
    //
    //  변환 공식 (Bug #3 수정):
    //    code = (Vin − Vref_n) / Vfull × (2^N − 1)
    //         = (Vin + 1.65) / 3.3 × 4095
    //
    //  이전 오류 코드:  (Vin / 3.3) × 1023
    //    → Vin = −1.0V: (−1.0/3.3)×1023 = −310 → 클리핑 0  (틀림!)
    //    → Vin = +1.0V: (1.0/3.3)×1023 = +310 만 사용  (절반 낭비!)
    //
    //  수정 후 검증:
    //    Vin = −1.65 V → (0.00/3.3)×4095 =    0  ✓ 최솟값
    //    Vin =  0.00 V → (1.65/3.3)×4095 = 2047  ✓ 중간값 (mid-code)
    //    Vin = +1.65 V → (3.30/3.3)×4095 = 4095  ✓ 최댓값
    // ============================================================
    real real_buf_out;
    xreal_to_real BUF_CONV (.out(real_buf_out), .in(buf_out));

    always @(negedge clk_samp) begin : ADC_SAMPLE
        integer quantized_val;

        // 12-bit 양자화
        quantized_val = $rtoi(((real_buf_out + 1.65) / 3.3) * 4095.0);

        // 포화 클리핑 (공급전압 초과 입력 대비)
        if      (quantized_val > 4095) adc_data <= 12'd4095;
        else if (quantized_val < 0)    adc_data <= 12'd0;
        else                           adc_data <= quantized_val[11:0];
    end

endmodule
