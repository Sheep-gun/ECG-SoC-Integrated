#include "model_types.hpp"

#include "fixed_width.hpp"
#include "locked_parameters.hpp"

#include <array>
#include <cstdint>

namespace snn {
namespace {

constexpr std::array<std::int32_t, 4> biases = {{-5213, -22414, -7298, 32767}};

std::int32_t add32(std::int32_t a, std::int64_t b) noexcept {
    return static_cast<std::int32_t>(fw::signed_value<32>(
        fw::wrap_add<32>(fw::from_signed<32>(a), fw::from_signed<32>(b))));
}

std::int64_t add64(std::int64_t a, std::int64_t b) noexcept {
    return fw::signed_value<64>(
        fw::wrap_add<64>(fw::from_signed<64>(a), fw::from_signed<64>(b)));
}

void add_local(std::array<std::int32_t, 4>& dst,
               const std::array<std::int64_t, 4>& weight,
               std::int64_t scale = 1) noexcept {
    for (std::size_t i = 0; i < 4; ++i) dst[i] = add32(dst[i], weight[i] * scale);
}

void add_c24(std::array<std::int64_t, 4>& dst,
             const std::array<std::int64_t, 4>& weight,
             std::int64_t scale = 1) noexcept {
    for (std::size_t i = 0; i < 4; ++i) dst[i] = add64(dst[i], weight[i] * scale);
}

template <unsigned W>
std::uint64_t inc(std::uint64_t value, bool event) noexcept {
    return event ? fw::wrap_add<W>(value, 1) : fw::truncate<W>(value);
}

bool ge_pct(std::uint64_t num, std::uint64_t den, std::uint64_t threshold) noexcept {
    return den != 0 && num * 100U >= den * threshold;
}
bool le_pct(std::uint64_t num, std::uint64_t den, std::uint64_t threshold) noexcept {
    return den == 0 || num * 100U <= den * threshold;
}
bool ge_avg(std::uint64_t sum, std::uint64_t den, std::uint64_t threshold) noexcept {
    return den != 0 && sum >= den * threshold;
}
bool le_avg(std::uint64_t sum, std::uint64_t den, std::uint64_t threshold) noexcept {
    return den == 0 || sum <= den * threshold;
}

std::uint8_t scale_q4(std::uint32_t ticks) noexcept {
    for (std::uint8_t scale = 1; scale <= 15; ++scale) {
        if (ticks <= static_cast<std::uint32_t>(scale) * 3750U) return scale;
    }
    return 16;
}

std::int32_t scale_score(std::int32_t score, std::uint8_t scale) noexcept {
    const std::int64_t product = static_cast<std::int64_t>(score) * scale;
    const std::uint64_t shifted = fw::arithmetic_right<64>(fw::from_signed<64>(product), 4);
    return static_cast<std::int32_t>(fw::signed_value<32>(fw::truncate<32>(shifted)));
}

std::uint8_t argmax4(const std::array<std::int64_t, 4>& values) noexcept {
    std::uint8_t best = 0;
    for (std::uint8_t i = 1; i < 4; ++i) if (values[i] > values[best]) best = i;
    return best;
}

}  // namespace

void C24ScoreNeurons::reset() noexcept {
    *this = C24ScoreNeurons{};
    local_mem = biases;
    score_mem = biases;
    rbbb_gate_score_mem = biases;
    c24_mem = {{params::C24_MEM_INIT_NSR, params::C24_MEM_INIT_CHF,
                params::C24_MEM_INIT_ARR, params::C24_MEM_INIT_AFF}};
    score_arr_before_eerg = score_mem[2];
}

void C24ScoreNeurons::tick(bool clear, const ScoreInputs& in) noexcept {
    if (clear) {
        reset();
        return;
    }
    C24ScoreNeurons next = *this;
    auto local = local_mem;
    auto score = score_mem;
    auto c24 = c24_mem;
    const auto c24_before_current_events = c24;

    const auto beat_seg = static_cast<std::uint16_t>(inc<16>(beat_seg_count, in.beat_spike));
    const auto dscr_flip_seg = static_cast<std::uint16_t>(inc<16>(dscr_flip_seg_count, in.dscr_sign_flip_spike));
    const auto dscr_slope_seg = static_cast<std::uint16_t>(inc<16>(dscr_slope_seg_count, in.dscr_valid_slope_spike));
    const auto qrs_valid_seg = static_cast<std::uint16_t>(inc<16>(qrs_maf_valid_seg_count, in.qrs_maf_valid_spike));
    const bool qrs_abnormal = in.qrs_width_abn_spike || in.qrs_complex_abn_spike || in.qrs_energy_abn_spike;
    const auto qrs_maf_seg = static_cast<std::uint16_t>(inc<16>(qrs_maf_seg_count, qrs_abnormal));
    const auto qrs_width_seg = static_cast<std::uint16_t>(inc<16>(qrs_width_abn_seg_count, in.qrs_width_abn_spike));
    const auto qrs_energy_seg = static_cast<std::uint16_t>(inc<16>(qrs_energy_abn_seg_count, in.qrs_energy_abn_spike));
    const auto rbbb_valid_seg = static_cast<std::uint16_t>(inc<16>(rbbb_valid_seg_count, in.rbbb_qrs_valid_spike));
    const auto rbbb_wide_seg = static_cast<std::uint16_t>(inc<16>(rbbb_wide_seg_count, in.rbbb_qrs_wide_spike));
    const auto rbbb_terminal_seg = static_cast<std::uint16_t>(inc<16>(rbbb_terminal_seg_count, in.rbbb_qrs_terminal_spike));
    const auto rbbb_like_seg = static_cast<std::uint16_t>(inc<16>(rbbb_like_seg_count, in.rbbb_qrs_like_beat_spike));
    const auto rbbb_segment_seg = static_cast<std::uint16_t>(inc<16>(rbbb_segment_seg_count, in.rbbb_qrs_delay_segment_spike));
    const auto ect_pair_win = static_cast<std::uint8_t>(inc<8>(ectopic_pair_win_count, in.ectopic_pair_spike));
    const auto ect_pair_seg = static_cast<std::uint16_t>(inc<16>(ectopic_pair_seg_count, in.ectopic_pair_spike));
    const auto ect_early_seg = static_cast<std::uint16_t>(inc<16>(ectopic_early_seg_count, in.ectopic_early_spike));
    const auto pre_bump_seg = static_cast<std::uint16_t>(inc<16>(pre_qrs_bump_seg_count, in.pre_qrs_bump_spike));
    const auto pnn_match_win = static_cast<std::uint16_t>(inc<16>(pnn_match_win_count, in.pnn_match_spike));
    const auto pnn_mis_win = static_cast<std::uint16_t>(inc<16>(pnn_mis_win_count, in.pnn_mismatch_spike));
    const auto pnn_match_seg = static_cast<std::uint16_t>(inc<16>(pnn_match_seg_count, in.pnn_match_spike));
    const auto pnn_mis_seg = static_cast<std::uint16_t>(inc<16>(pnn_mis_seg_count, in.pnn_mismatch_spike));
    std::uint16_t rdm_valid_win = rdm_valid_win_count;
    std::uint32_t rdm_code_win = rdm_code_win_sum;
    std::uint16_t rdm_valid_seg = rdm_valid_seg_count;
    std::uint32_t rdm_code_seg = rdm_code_seg_sum;
    std::uint16_t ram_count_window = ram_count_win;
    std::uint32_t ram_code_window = ram_code_win_sum;
    std::uint16_t ram_seg = ram_seg_count;
    std::uint32_t ram_code_seg = ram_code_seg_sum;
    std::uint16_t rdm_ge20 = rdm_ge20_seg_count;
    std::uint16_t rdm_ge50 = rdm_ge50_seg_count;
    std::uint16_t rdm_ge80 = rdm_ge80_seg_count;
    std::uint16_t rdm_ge100 = rdm_ge100_seg_count;

    if (in.pre_qrs_bump_spike) add_c24(c24, params::C24_W_PRE_QRS);
    if (in.rbbb_qrs_like_beat_spike) add_c24(c24, params::C24_W_RBBB_LIKE);
    if (in.rbbb_qrs_delay_segment_spike) add_c24(c24, params::C24_W_RBBB_SEGMENT);
    if (in.pnn_match_spike) { add_c24(c24, params::C24_W_PNN_MATCH); add_local(local, params::W_PNN_MATCH); }
    if (in.pnn_mismatch_spike) { add_c24(c24, params::C24_W_PNN_MIS); add_local(local, params::W_PNN_MIS); }
    if (in.dscr_valid_slope_spike) {
        add_c24(c24, params::C24_W_DSCR_SLOPE);
        local[0] = add32(local[0], params::W_DSCR_SLOPE_NSR);
        local[1] = add32(local[1], params::W_DSCR_SLOPE_CHF);
    }
    if (in.dscr_sign_flip_spike) {
        add_c24(c24, params::C24_W_DSCR_FLIP);
        local[0] = add32(local[0], params::W_DSCR_FLIP_NSR);
        local[1] = add32(local[1], params::W_DSCR_FLIP_CHF);
    }
    if (in.ram_amp_spike) {
        for (std::size_t i = 0; i < 4; ++i)
            c24[i] = add64(c24[i], params::C24_W_RAM_COUNT[i] + params::C24_W_RAM_CODE[i] * in.ram_amp_code);
        local[2] = add32(local[2], params::W_RAM_COUNT_ARR + params::W_RAM_SUM_ARR * in.ram_amp_code);
        local[3] = add32(local[3], params::W_RAM_COUNT_AFF + params::W_RAM_SUM_AFF * in.ram_amp_code);
        ram_count_window = static_cast<std::uint16_t>(fw::wrap_add<16>(ram_count_window, 1));
        ram_code_window = static_cast<std::uint32_t>(fw::wrap_add<22>(ram_code_window, in.ram_amp_code));
        ram_seg = static_cast<std::uint16_t>(fw::wrap_add<16>(ram_seg, 1));
        ram_code_seg = static_cast<std::uint32_t>(fw::wrap_add<22>(ram_code_seg, in.ram_amp_code));
    }
    if (in.rdm_valid_spike) {
        std::uint8_t code = 0;
        for (std::size_t bit = 0; bit < 15; ++bit) if ((in.rdm_level_spike & (1U << bit)) != 0) {
            ++code;
            for (std::size_t cls = 0; cls < 4; ++cls) {
                local[cls] = add32(local[cls], params::LOCAL_RDM_GE[cls][bit]);
                c24[cls] = add64(c24[cls], params::C24_RDM_LEVEL[cls][bit]);
            }
        }
        for (std::size_t cls = 0; cls < 4; ++cls) {
            c24[cls] = add64(c24[cls], params::C24_W_RDM_VALID[cls] + params::C24_W_RDM_CODE[cls] * code);
            local[cls] = add32(local[cls], params::W_RDM_VALID[cls] + params::W_RDM_CODE[cls] * code);
        }
        rdm_valid_win = static_cast<std::uint16_t>(fw::wrap_add<16>(rdm_valid_win, 1));
        rdm_code_win = static_cast<std::uint32_t>(fw::wrap_add<20>(rdm_code_win, code));
        rdm_valid_seg = static_cast<std::uint16_t>(fw::wrap_add<16>(rdm_valid_seg, 1));
        rdm_code_seg = static_cast<std::uint32_t>(fw::wrap_add<20>(rdm_code_seg, code));
        if ((in.rdm_level_spike & (1U << 1)) != 0) rdm_ge20 = static_cast<std::uint16_t>(fw::wrap_add<16>(rdm_ge20, 1));
        if ((in.rdm_level_spike & (1U << 4)) != 0) rdm_ge50 = static_cast<std::uint16_t>(fw::wrap_add<16>(rdm_ge50, 1));
        if ((in.rdm_level_spike & (1U << 7)) != 0) rdm_ge80 = static_cast<std::uint16_t>(fw::wrap_add<16>(rdm_ge80, 1));
        if ((in.rdm_level_spike & (1U << 9)) != 0) rdm_ge100 = static_cast<std::uint16_t>(fw::wrap_add<16>(rdm_ge100, 1));
    }
    if (in.ectopic_pair_spike) { add_c24(c24, params::C24_W_ECT_PAIR); add_local(local, params::W_ECT_PAIR); }
    if (qrs_abnormal) add_c24(c24, params::C24_W_QRS_MAF);
    if (in.qrs_width_abn_spike) { add_c24(c24, params::C24_W_QRS_WIDTH); add_local(local, params::W_QRS_WIDTH_COUNT); }
    if (in.qrs_complex_abn_spike) { add_c24(c24, params::C24_W_QRS_COMPLEX); add_local(local, params::W_QRS_COMPLEX_COUNT); }
    if (in.qrs_energy_abn_spike) { add_c24(c24, params::C24_W_QRS_ENERGY); add_local(local, params::W_QRS_ENERGY_COUNT); }
    if (in.rhythm_tick && ms_count == 999) { add_c24(c24, params::C24_W_SECOND); add_local(local, params::W_SEC); }

    const bool period_done = in.rhythm_tick && subwindow_tick_count == 59999;
    const bool finalize = period_done || (in.segment_done && subwindow_tick_count != 0);
    const std::uint8_t window_scale = period_done ? 16 : scale_q4(subwindow_tick_count);
    const std::uint32_t pnn_decision_win = static_cast<std::uint32_t>(pnn_match_win) + pnn_mis_win;
    const std::uint32_t pnn_decision_seg = static_cast<std::uint32_t>(pnn_match_seg) + pnn_mis_seg;
    const bool arr_high = finalize && pnn_decision_win != 0 &&
        ge_pct(pnn_mis_win, pnn_decision_win, 12) && le_pct(pnn_mis_win, pnn_decision_win, 65) &&
        rdm_valid_win != 0 && ge_avg(rdm_code_win, rdm_valid_win, 5) && le_avg(rdm_code_win, rdm_valid_win, 12) &&
        ram_count_window != 0 && ge_avg(ram_code_window, ram_count_window, 12) &&
        static_cast<std::uint32_t>(ect_pair_win) * 100U >= static_cast<std::uint32_t>(rdm_valid_win) * 4U &&
        static_cast<std::uint32_t>(ect_pair_win) * 100U <= static_cast<std::uint32_t>(rdm_valid_win) * 35U;
    if (c24_readout_busy_ticks != 0) {
        // Newly generated event groups are capture-gated while the physical
        // C24 segment readout/WTA pipeline is busy. Event deltas captured
        // before segment_done have already been folded into this model.
        c24 = c24_before_current_events;
    }
    if (finalize) {
        next.rbbb_gate_score_mem = score;
        for (std::size_t i = 0; i < 4; ++i) score[i] = add32(score[i], scale_score(add32(local[i], -biases[i]), window_scale));
        if (arr_high) { score[2] = add32(score[2], scale_score(static_cast<std::int32_t>(params::W_ARR_HIGH_IRR_TO_ARR), window_scale)); add_c24(c24, params::C24_W_ARR_HIGH_IRR); }
    }

    next.rbbb_qrs_delay_applied = false;
    if (in.segment_done && !finalize && in.rbbb_qrs_delay_segment_spike) {
        if (!(rbbb_gate_score_mem[1] > rbbb_gate_score_mem[2])) {
            score[0] = add32(score[0], -100000);
            score[2] = add32(score[2], 100000);
            next.rbbb_qrs_delay_applied = true;
            // In locked RTL this status pulse is generated during readout.
            // c24_gate_rbbb_delay_capture_reg is qualified by
            // !c24_readout_busy, so the corresponding C24 weight is not
            // captured at this segment boundary.
        }
    }
    const bool eerg = in.segment_done && in.rbbb_qrs_like_count == 0 && pre_bump_seg >= 1 &&
        (ect_early_seg >= 10 || ect_pair_seg >= 3) && pnn_decision_seg != 0 &&
        le_pct(pnn_mis_seg, pnn_decision_seg, 15) && rdm_valid_seg != 0 &&
        le_avg(rdm_code_seg, rdm_valid_seg, 5);
    next.score_arr_before_eerg = score[2];
    next.eerg_applied = false;
    if (in.segment_done && eerg) {
        score[2] = add32(score[2], 25000);
        next.eerg_applied = true;
        add_c24(c24, params::C24_W_EERG_GATE);
        add_c24(c24, params::C24_W_EERG_APPLIED);
    }

#define ADD_IF(condition, weight) do { if (condition) add_c24(c24, params::weight); } while (false)
    if (in.segment_done) {
        ADD_IF(ge_pct(pnn_mis_seg,pnn_decision_seg,3), C24_W_PNN_MIS_GE_3);
        ADD_IF(ge_pct(pnn_mis_seg,pnn_decision_seg,8), C24_W_PNN_MIS_GE_8);
        ADD_IF(ge_pct(pnn_mis_seg,pnn_decision_seg,15), C24_W_PNN_MIS_GE_15);
        ADD_IF(ge_pct(pnn_mis_seg,pnn_decision_seg,25), C24_W_PNN_MIS_GE_25);
        ADD_IF(ge_pct(pnn_mis_seg,pnn_decision_seg,45), C24_W_PNN_MIS_GE_45);
        ADD_IF(le_pct(pnn_mis_seg,pnn_decision_seg,3), C24_W_PNN_MIS_LE_3);
        ADD_IF(le_pct(pnn_mis_seg,pnn_decision_seg,8), C24_W_PNN_MIS_LE_8);
        ADD_IF(le_pct(pnn_mis_seg,pnn_decision_seg,15), C24_W_PNN_MIS_LE_15);
        ADD_IF(ge_avg(rdm_code_seg,rdm_valid_seg,2), C24_W_RDM_AVG_GE_2);
        ADD_IF(ge_avg(rdm_code_seg,rdm_valid_seg,4), C24_W_RDM_AVG_GE_4);
        ADD_IF(ge_avg(rdm_code_seg,rdm_valid_seg,6), C24_W_RDM_AVG_GE_6);
        ADD_IF(ge_avg(rdm_code_seg,rdm_valid_seg,9), C24_W_RDM_AVG_GE_9);
        ADD_IF(ge_avg(rdm_code_seg,rdm_valid_seg,12), C24_W_RDM_AVG_GE_12);
        ADD_IF(le_avg(rdm_code_seg,rdm_valid_seg,2), C24_W_RDM_AVG_LE_2);
        ADD_IF(le_avg(rdm_code_seg,rdm_valid_seg,4), C24_W_RDM_AVG_LE_4);
        ADD_IF(le_avg(rdm_code_seg,rdm_valid_seg,6), C24_W_RDM_AVG_LE_6);
#define PCT4(base, count) \
        ADD_IF(ge_pct(count,rdm_valid_seg,3), base##_GE_3); \
        ADD_IF(ge_pct(count,rdm_valid_seg,8), base##_GE_8); \
        ADD_IF(ge_pct(count,rdm_valid_seg,20), base##_GE_20); \
        ADD_IF(ge_pct(count,rdm_valid_seg,40), base##_GE_40)
        PCT4(C24_W_RDM_GE20, rdm_ge20); PCT4(C24_W_RDM_GE50, rdm_ge50);
        PCT4(C24_W_RDM_GE80, rdm_ge80); PCT4(C24_W_RDM_GE100, rdm_ge100);
#undef PCT4
        ADD_IF(ge_pct(dscr_flip_seg,dscr_slope_seg,1), C24_W_DSCR_GE_1);
        ADD_IF(ge_pct(dscr_flip_seg,dscr_slope_seg,3), C24_W_DSCR_GE_3);
        ADD_IF(ge_pct(dscr_flip_seg,dscr_slope_seg,5), C24_W_DSCR_GE_5);
        ADD_IF(ge_pct(dscr_flip_seg,dscr_slope_seg,8), C24_W_DSCR_GE_8);
        ADD_IF(ge_pct(dscr_flip_seg,dscr_slope_seg,12), C24_W_DSCR_GE_12);
        ADD_IF(le_pct(dscr_flip_seg,dscr_slope_seg,1), C24_W_DSCR_LE_1);
        ADD_IF(le_pct(dscr_flip_seg,dscr_slope_seg,3), C24_W_DSCR_LE_3);
        ADD_IF(le_pct(dscr_flip_seg,dscr_slope_seg,5), C24_W_DSCR_LE_5);
        ADD_IF(ge_avg(ram_code_seg,ram_seg,2), C24_W_RAM_GE_2); ADD_IF(ge_avg(ram_code_seg,ram_seg,4), C24_W_RAM_GE_4);
        ADD_IF(ge_avg(ram_code_seg,ram_seg,6), C24_W_RAM_GE_6); ADD_IF(ge_avg(ram_code_seg,ram_seg,10), C24_W_RAM_GE_10);
        ADD_IF(ge_avg(ram_code_seg,ram_seg,14), C24_W_RAM_GE_14); ADD_IF(le_avg(ram_code_seg,ram_seg,2), C24_W_RAM_LE_2);
        ADD_IF(le_avg(ram_code_seg,ram_seg,4), C24_W_RAM_LE_4); ADD_IF(le_avg(ram_code_seg,ram_seg,6), C24_W_RAM_LE_6);
        ADD_IF(ge_pct(ect_pair_seg,beat_seg,1), C24_W_ECP_GE_1); ADD_IF(ge_pct(ect_pair_seg,beat_seg,3), C24_W_ECP_GE_3);
        ADD_IF(ge_pct(ect_pair_seg,beat_seg,8), C24_W_ECP_GE_8); ADD_IF(ge_pct(ect_pair_seg,beat_seg,15), C24_W_ECP_GE_15);
        ADD_IF(ge_pct(ect_pair_seg,beat_seg,25), C24_W_ECP_GE_25);
        ADD_IF(ge_pct(pre_bump_seg,beat_seg,1), C24_W_PRE_GE_1); ADD_IF(ge_pct(pre_bump_seg,beat_seg,3), C24_W_PRE_GE_3);
        ADD_IF(ge_pct(pre_bump_seg,beat_seg,8), C24_W_PRE_GE_8);
        ADD_IF(ge_pct(qrs_maf_seg,qrs_valid_seg,1), C24_W_QRS_GE_1); ADD_IF(ge_pct(qrs_maf_seg,qrs_valid_seg,3), C24_W_QRS_GE_3);
        ADD_IF(ge_pct(qrs_maf_seg,qrs_valid_seg,8), C24_W_QRS_GE_8); ADD_IF(ge_pct(qrs_maf_seg,qrs_valid_seg,20), C24_W_QRS_GE_20);
        ADD_IF(ge_pct(qrs_maf_seg,qrs_valid_seg,40), C24_W_QRS_GE_40);
        ADD_IF(ge_pct(qrs_width_seg,qrs_valid_seg,1), C24_W_QRS_WIDTH_GE_1); ADD_IF(ge_pct(qrs_width_seg,qrs_valid_seg,3), C24_W_QRS_WIDTH_GE_3);
        ADD_IF(ge_pct(qrs_width_seg,qrs_valid_seg,8), C24_W_QRS_WIDTH_GE_8); ADD_IF(ge_pct(qrs_width_seg,qrs_valid_seg,15), C24_W_QRS_WIDTH_GE_15);
        ADD_IF(ge_pct(qrs_energy_seg,qrs_valid_seg,1), C24_W_QRS_ENERGY_GE_1); ADD_IF(ge_pct(qrs_energy_seg,qrs_valid_seg,3), C24_W_QRS_ENERGY_GE_3);
        ADD_IF(ge_pct(qrs_energy_seg,qrs_valid_seg,8), C24_W_QRS_ENERGY_GE_8); ADD_IF(ge_pct(qrs_energy_seg,qrs_valid_seg,20), C24_W_QRS_ENERGY_GE_20);
        ADD_IF(ge_pct(qrs_energy_seg,qrs_valid_seg,40), C24_W_QRS_ENERGY_GE_40);
        ADD_IF(ge_pct(rbbb_like_seg,beat_seg,1), C24_W_RBBB_GE_1); ADD_IF(ge_pct(rbbb_like_seg,beat_seg,3), C24_W_RBBB_GE_3);
        ADD_IF(ge_pct(rbbb_like_seg,beat_seg,8), C24_W_RBBB_GE_8); ADD_IF(ge_pct(rbbb_like_seg,beat_seg,15), C24_W_RBBB_GE_15);
        ADD_IF(ge_pct(rbbb_wide_seg,rbbb_valid_seg,1), C24_W_RBBB_WIDE_GE_1); ADD_IF(ge_pct(rbbb_wide_seg,rbbb_valid_seg,3), C24_W_RBBB_WIDE_GE_3);
        ADD_IF(ge_pct(rbbb_wide_seg,rbbb_valid_seg,8), C24_W_RBBB_WIDE_GE_8); ADD_IF(ge_pct(rbbb_wide_seg,rbbb_valid_seg,15), C24_W_RBBB_WIDE_GE_15);
        ADD_IF(ge_pct(rbbb_terminal_seg,rbbb_valid_seg,1), C24_W_RBBB_TERMINAL_GE_1); ADD_IF(ge_pct(rbbb_terminal_seg,rbbb_valid_seg,3), C24_W_RBBB_TERMINAL_GE_3);
        ADD_IF(ge_pct(rbbb_terminal_seg,rbbb_valid_seg,8), C24_W_RBBB_TERMINAL_GE_8); ADD_IF(ge_pct(rbbb_terminal_seg,rbbb_valid_seg,15), C24_W_RBBB_TERMINAL_GE_15);
        ADD_IF(le_pct(pnn_mis_seg,pnn_decision_seg,15) && ge_pct(rbbb_like_seg,beat_seg,2), C24_W_GATE_REGULAR_RBBB_RESCUE);
        ADD_IF(le_pct(pnn_mis_seg,pnn_decision_seg,15) && (ge_pct(qrs_width_seg,qrs_valid_seg,2) || ge_pct(qrs_energy_seg,qrs_valid_seg,35)), C24_W_GATE_REGULAR_QRS_ARR_RESCUE);
        ADD_IF(ge_pct(ect_pair_seg,beat_seg,3) && le_pct(pnn_mis_seg,pnn_decision_seg,35) && le_avg(rdm_code_seg,rdm_valid_seg,8), C24_W_GATE_EPISODIC_ECTOPIC_ARR);
        ADD_IF(rbbb_like_seg == 0 && pre_bump_seg >= 1 && (ect_early_seg >= 10 || ect_pair_seg >= 3) && le_pct(pnn_mis_seg,pnn_decision_seg,15) && le_avg(rdm_code_seg,rdm_valid_seg,5), C24_W_GATE_EERG_LIKE);
        ADD_IF(ge_pct(pnn_mis_seg,pnn_decision_seg,25) && ge_avg(rdm_code_seg,rdm_valid_seg,7) && ge_pct(ect_pair_seg,beat_seg,5), C24_W_GATE_AFF_PERSISTENT_IRREG);
        ADD_IF(ge_pct(pnn_mis_seg,pnn_decision_seg,5) && le_pct(pnn_mis_seg,pnn_decision_seg,30) && ge_avg(rdm_code_seg,rdm_valid_seg,2) && le_avg(rdm_code_seg,rdm_valid_seg,9), C24_W_GATE_ARR_MID_IRREG);
        ADD_IF(le_pct(dscr_flip_seg,dscr_slope_seg,3) && le_pct(pnn_mis_seg,pnn_decision_seg,20), C24_W_GATE_CHF_LOW_DSCR_LOW_IRREG);
        ADD_IF(ge_pct(dscr_flip_seg,dscr_slope_seg,5) && le_pct(pnn_mis_seg,pnn_decision_seg,15) && le_avg(rdm_code_seg,rdm_valid_seg,5), C24_W_GATE_NSR_HIGH_DSCR_LOW_IRREG);
        ADD_IF(ge_avg(ram_code_seg,ram_seg,10) && le_pct(pnn_mis_seg,pnn_decision_seg,20), C24_W_GATE_RAM_HIGH_REGULAR);
        ADD_IF(le_avg(ram_code_seg,ram_seg,5) && ge_pct(pnn_mis_seg,pnn_decision_seg,15), C24_W_GATE_RAM_LOW_IRREGULAR);
        next.pred_class = argmax4(c24);
        next.pred_valid = true;
    }
#undef ADD_IF

    next.local_mem = finalize ? biases : local;
    next.score_mem = score;
    next.c24_mem = c24;
    if (in.segment_done) next.c24_readout_busy_ticks = 35;
    else if (c24_readout_busy_ticks != 0) {
        next.c24_readout_busy_ticks = static_cast<std::uint8_t>(c24_readout_busy_ticks - 1U);
    }
    if (in.rhythm_tick) {
        next.ms_count = ms_count == 999 ? 0 : static_cast<std::uint16_t>(ms_count + 1U);
        next.subwindow_tick_count = period_done ? 0 : static_cast<std::uint32_t>(fw::wrap_add<17>(subwindow_tick_count, 1));
    }
    if (in.segment_done) {
        next.eerg_gate = eerg;
        next.eerg_pre_qrs_bump_count = pre_bump_seg;
        next.eerg_early_count = ect_early_seg;
        next.eerg_ecp_count = ect_pair_seg;
        next.eerg_pnn_decision_count = static_cast<std::uint16_t>(pnn_decision_seg);
        next.eerg_pnn_mismatch_count = pnn_mis_seg;
        next.eerg_rdm_valid_count = rdm_valid_seg;
        next.eerg_rdm_code_sum = rdm_code_seg;
        next.beat_seg_count = next.dscr_flip_seg_count = next.dscr_slope_seg_count = 0;
        next.ram_seg_count = 0; next.ram_code_seg_sum = 0;
        next.rdm_ge20_seg_count = next.rdm_ge50_seg_count = next.rdm_ge80_seg_count = next.rdm_ge100_seg_count = 0;
        next.qrs_maf_valid_seg_count = next.qrs_maf_seg_count = next.qrs_width_abn_seg_count = next.qrs_energy_abn_seg_count = 0;
        next.rbbb_valid_seg_count = next.rbbb_wide_seg_count = next.rbbb_terminal_seg_count = next.rbbb_like_seg_count = next.rbbb_segment_seg_count = 0;
        next.ectopic_pair_seg_count = next.ectopic_early_seg_count = next.pre_qrs_bump_seg_count = 0;
        next.pnn_match_seg_count = next.pnn_mis_seg_count = next.rdm_valid_seg_count = 0;
        next.rdm_code_seg_sum = 0;
    } else {
        next.eerg_gate = false;
        next.beat_seg_count=beat_seg; next.dscr_flip_seg_count=dscr_flip_seg; next.dscr_slope_seg_count=dscr_slope_seg;
        next.ram_seg_count=ram_seg; next.ram_code_seg_sum=ram_code_seg;
        next.rdm_ge20_seg_count=rdm_ge20; next.rdm_ge50_seg_count=rdm_ge50; next.rdm_ge80_seg_count=rdm_ge80; next.rdm_ge100_seg_count=rdm_ge100;
        next.qrs_maf_valid_seg_count=qrs_valid_seg; next.qrs_maf_seg_count=qrs_maf_seg; next.qrs_width_abn_seg_count=qrs_width_seg; next.qrs_energy_abn_seg_count=qrs_energy_seg;
        next.rbbb_valid_seg_count=rbbb_valid_seg; next.rbbb_wide_seg_count=rbbb_wide_seg; next.rbbb_terminal_seg_count=rbbb_terminal_seg; next.rbbb_like_seg_count=rbbb_like_seg; next.rbbb_segment_seg_count=rbbb_segment_seg;
        next.ectopic_pair_seg_count=ect_pair_seg; next.ectopic_early_seg_count=ect_early_seg; next.pre_qrs_bump_seg_count=pre_bump_seg;
        next.pnn_match_seg_count=pnn_match_seg; next.pnn_mis_seg_count=pnn_mis_seg; next.rdm_valid_seg_count=rdm_valid_seg; next.rdm_code_seg_sum=rdm_code_seg;
    }
    if (finalize) {
        next.ectopic_pair_win_count=0; next.pnn_match_win_count=0; next.pnn_mis_win_count=0;
        next.rdm_valid_win_count=0; next.rdm_code_win_sum=0; next.ram_count_win=0; next.ram_code_win_sum=0;
    } else {
        next.ectopic_pair_win_count=ect_pair_win; next.pnn_match_win_count=pnn_match_win; next.pnn_mis_win_count=pnn_mis_win;
        next.rdm_valid_win_count=rdm_valid_win; next.rdm_code_win_sum=rdm_code_win; next.ram_count_win=ram_count_window; next.ram_code_win_sum=ram_code_window;
    }
    *this = next;
}

}  // namespace snn
