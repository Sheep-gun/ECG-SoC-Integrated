#pragma once

#include <array>
#include <cstdint>

namespace snn {

struct EcgEventEncoderAdaptive {
    static constexpr std::array<std::uint16_t, 12> bank_thresholds =
        {{4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48}};

    std::int16_t prev_sample = 0;
    std::int16_t delta = 0;
    std::uint16_t abs_delta = 0;
    bool sample_seen = false;
    bool strong_event = false;
    bool up_event = false;
    bool down_event = false;
    bool slope_valid = false;
    bool adaptive_ready = false;
    std::uint8_t adaptive_event_th = 5;
    std::uint16_t calib_count = 0;
    std::array<std::uint16_t, 64> hist{};
    std::array<std::uint16_t, 12> bank_count{};

    void reset() noexcept;
    void tick(bool sample_valid, bool segment_start, std::int16_t adc_data) noexcept;
};

struct QrsLifDetector {
    std::uint16_t qrs_mem = 0;        // 12 bits
    std::uint16_t refractory_cnt = 0; // 10 bits
    bool beat_spike = false;

    void reset() noexcept;
    void tick(bool sample_valid, bool strong_event) noexcept;
};

struct PnnRhythmPredictor {
    static constexpr std::uint16_t max_age = 0x0fff;
    static constexpr std::uint8_t num_hyp = 46;
    static constexpr std::uint16_t base_delay = 250;
    static constexpr std::uint16_t delay_step = 50;
    static constexpr std::uint16_t window_half = 125;

    bool token_active = false;
    std::uint16_t token_age = 0;
    std::uint16_t rr_interval = 0;
    std::uint8_t winner_id = 0;
    std::uint8_t predictor_id = 0;
    bool winner_valid = false;
    bool predictor_valid = false;
    std::uint16_t winner_error = max_age;
    std::uint16_t predictor_error = max_age;
    bool pnn_match_spike = false;
    bool pnn_mismatch_spike = false;
    bool evaluating = false;
    std::uint8_t eval_idx = 0;
    std::uint16_t eval_age = 0;
    std::uint8_t eval_best_id = 0;
    std::uint16_t eval_best_err = max_age;
    std::uint8_t eval_predictor_id = 0;
    bool eval_predictor_valid = false;

    void reset() noexcept;
    void tick(bool clear, bool rhythm_tick, bool beat_spike) noexcept;
    static std::uint16_t abs_diff(std::uint16_t a, std::uint16_t b) noexcept;
    static std::uint16_t hyp_center(std::uint8_t index) noexcept;
};

struct RdmVariabilityNeuron {
    static constexpr std::array<std::uint16_t, 15> thresholds =
        {{10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150}};
    bool prev_rr_valid = false;
    std::uint16_t current_rr = 0;
    std::uint16_t prev_rr = 0;
    std::uint16_t rr_diff = 0;
    bool rr_diff_valid_spike = false;
    std::uint16_t rdm_level_spike = 0; // 15 bits
    std::uint8_t rdm_level_code = 0;   // 4 bits

    void reset() noexcept;
    void tick(bool clear, bool rr_interval_valid_spike,
              std::uint16_t rr_interval_in) noexcept;
};

struct EctopicPairNeuron {
    bool ref_valid = false;
    std::uint8_t prev_pattern = 0;
    std::uint16_t rr_ref = 0; // 12 bits
    bool early_rr_spike = false;
    bool late_rr_spike = false;
    bool ectopic_pair_spike = false;

    void reset() noexcept;
    void tick(bool clear, bool rr_interval_valid_spike,
              std::uint16_t rr_interval_in) noexcept;
};

struct DscrSpikeCounter {
    bool sample_seen = false;
    std::int32_t filt_mem = 0; // signed 24-bit
    std::uint16_t up_mem = 0;
    std::uint16_t down_mem = 0;
    std::uint16_t sign_mem = 0;
    bool prev_slope_valid = false;
    bool prev_slope_sign = false;
    bool valid_slope_spike = false;
    bool sign_flip_spike = false;

    void reset() noexcept;
    void tick(bool clear, bool sample_valid, std::int16_t adc_data) noexcept;
};

struct RamPeakAccumulator {
    bool amp_window_active = false;
    std::uint8_t amp_window_cnt = 0;
    std::uint8_t r_peak_abs = 0; // encoded 6-bit peak
    bool ram_amp_spike = false;
    std::uint8_t ram_amp_code = 0;
    bool ram_window_open_d = false;
    bool beat_seen = false;
    bool post_hold_active = false;
    std::uint8_t post_hold_cnt = 0;

    void reset() noexcept;
    void tick(bool clear, bool sample_valid, bool ram_window_open,
              bool beat_spike, std::int16_t adc_data) noexcept;
    static std::uint8_t encode_amp_code(std::int32_t amplitude) noexcept;
};

struct QrsMafNeuron {
    static constexpr std::size_t pre_win = 120;
    std::array<std::uint8_t, pre_win> pre_strong{};
    std::array<std::uint8_t, pre_win> pre_flip{};
    std::array<std::uint8_t, pre_win> pre_energy{};
    std::uint8_t pre_head = 0; // physical index of logical newest entry
    std::uint8_t pre_strong_count = 0;
    std::uint8_t pre_flip_count = 0;
    std::uint16_t pre_energy_sum = 0;
    bool window_active = false;
    std::uint8_t post_count = 0;
    bool event_seen = false;
    std::uint8_t first_pos = 0;
    std::uint8_t last_pos = 0;
    std::uint8_t event_count = 0;
    std::uint8_t flip_count = 0;
    std::uint16_t energy_sum = 0;
    std::uint8_t pre_strong_at_beat = 0;
    std::uint8_t pre_flip_at_beat = 0;
    std::uint16_t pre_energy_at_beat = 0;
    std::uint8_t width_ref = 0;
    std::uint8_t energy_ref = 0;
    bool width_ref_valid = false;
    bool energy_ref_valid = false;
    bool qrs_maf_valid_spike = false;
    bool qrs_width_abn_spike = false;
    bool qrs_complex_abn_spike = false;
    bool qrs_energy_abn_spike = false;
    bool pre_qrs_bump_spike = false;
    std::uint8_t qrs_width_value = 0;
    std::uint8_t qrs_complex_count = 0;
    std::uint8_t qrs_energy_code = 0;

    void reset() noexcept;
    void tick(bool clear, bool sample_valid, std::int16_t adc_data,
              bool strong_event, bool dscr_sign_flip_spike,
              bool beat_spike) noexcept;
    std::uint8_t logical_strong(std::size_t index) const noexcept;
};

struct RbbbQrsDelayBank {
    bool qrs_active = false;
    bool prev_activity = false;
    std::uint8_t onset_ref_cnt = 0;
    std::uint8_t qrs_age = 0;
    std::uint8_t activity_gap_cnt = 0;
    std::uint16_t hyp_match = 0; // 9 bits
    std::uint8_t terminal_count_work = 0;
    std::uint16_t pnn_match_count = 0;
    std::uint16_t pnn_mismatch_count = 0;
    std::uint16_t rdm_valid_count = 0;
    std::uint16_t rdm_high_count = 0;
    std::uint32_t rdm_code_sum = 0; // 20 bits
    bool qrs_onset_spike = false;
    bool qrs_valid_spike = false;
    bool wide_qrs_spike = false;
    bool terminal_delay_spike = false;
    bool rbbb_like_beat_spike = false;
    std::uint8_t last_matched_width = 0;
    std::uint8_t terminal_activity_count = 0;
    std::uint8_t max_last_matched_width = 0;
    std::uint8_t valid_qrs_count = 0;
    std::uint8_t wide_qrs_count = 0;
    std::uint8_t terminal_delay_count = 0;
    std::uint8_t rbbb_like_beat_count = 0;

    void reset() noexcept;
    void tick(bool clear, bool sample_valid, bool segment_done,
              bool strong_event, bool slope_valid, std::uint16_t abs_delta,
              bool pnn_match_spike, bool pnn_mismatch_spike,
              bool rdm_valid_spike, std::uint16_t rdm_level_spike,
              std::uint8_t rdm_level_code) noexcept;
    bool low_irregularity() const noexcept;
    bool high_rdm_irregularity() const noexcept;
    bool segment_spike(bool segment_done) const noexcept;
};

struct ScoreInputs {
    bool rhythm_tick = false;
    bool segment_done = false;
    bool beat_spike = false;
    bool qrs_maf_valid_spike = false;
    bool rbbb_qrs_valid_spike = false;
    bool rbbb_qrs_wide_spike = false;
    bool rbbb_qrs_terminal_spike = false;
    bool rbbb_qrs_like_beat_spike = false;
    bool pnn_match_spike = false;
    bool pnn_mismatch_spike = false;
    bool dscr_valid_slope_spike = false;
    bool dscr_sign_flip_spike = false;
    bool ram_amp_spike = false;
    std::uint8_t ram_amp_code = 0;
    bool rdm_valid_spike = false;
    std::uint16_t rdm_level_spike = 0;
    std::uint8_t rdm_level_code = 0;
    bool ectopic_pair_spike = false;
    bool ectopic_early_spike = false;
    bool pre_qrs_bump_spike = false;
    bool qrs_width_abn_spike = false;
    bool qrs_complex_abn_spike = false;
    bool qrs_energy_abn_spike = false;
    bool rbbb_qrs_delay_segment_spike = false;
    std::uint8_t rbbb_qrs_like_count = 0;
};

struct C24ScoreNeurons {
    std::array<std::int32_t, 4> local_mem{};
    std::array<std::int32_t, 4> score_mem{};
    // The locked RTL delays the RBBB gate evaluation until after window
    // finalization has started, but before the pipelined score commit lands.
    std::array<std::int32_t, 4> rbbb_gate_score_mem{};
    std::array<std::int64_t, 4> c24_mem{};
    // Remaining post-segment physical clocks for which c24_readout_busy is
    // asserted in the locked 29-stage readout/WTA pipeline.
    std::uint8_t c24_readout_busy_ticks = 0;
    std::uint16_t ms_count = 0; // 10 bits
    std::uint32_t subwindow_tick_count = 0; // 17 bits
    std::uint16_t beat_seg_count = 0;
    std::uint16_t dscr_flip_seg_count = 0;
    std::uint16_t dscr_slope_seg_count = 0;
    std::uint16_t ram_seg_count = 0;
    std::uint32_t ram_code_seg_sum = 0; // 22 bits
    std::uint16_t rdm_ge20_seg_count = 0;
    std::uint16_t rdm_ge50_seg_count = 0;
    std::uint16_t rdm_ge80_seg_count = 0;
    std::uint16_t rdm_ge100_seg_count = 0;
    std::uint16_t qrs_maf_valid_seg_count = 0;
    std::uint16_t qrs_maf_seg_count = 0;
    std::uint16_t qrs_width_abn_seg_count = 0;
    std::uint16_t qrs_energy_abn_seg_count = 0;
    std::uint16_t rbbb_valid_seg_count = 0;
    std::uint16_t rbbb_wide_seg_count = 0;
    std::uint16_t rbbb_terminal_seg_count = 0;
    std::uint16_t rbbb_like_seg_count = 0;
    std::uint16_t rbbb_segment_seg_count = 0;
    std::uint8_t ectopic_pair_win_count = 0;
    std::uint16_t ectopic_pair_seg_count = 0;
    std::uint16_t ectopic_early_seg_count = 0;
    std::uint16_t pre_qrs_bump_seg_count = 0;
    std::uint16_t pnn_match_win_count = 0;
    std::uint16_t pnn_mis_win_count = 0;
    std::uint16_t pnn_match_seg_count = 0;
    std::uint16_t pnn_mis_seg_count = 0;
    std::uint16_t rdm_valid_win_count = 0;
    std::uint32_t rdm_code_win_sum = 0; // 20 bits
    std::uint16_t rdm_valid_seg_count = 0;
    std::uint32_t rdm_code_seg_sum = 0; // 20 bits
    std::uint16_t ram_count_win = 0;
    std::uint32_t ram_code_win_sum = 0; // 22 bits
    bool eerg_gate = false;
    bool eerg_applied = false;
    std::uint16_t eerg_pre_qrs_bump_count = 0;
    std::uint16_t eerg_early_count = 0;
    std::uint16_t eerg_ecp_count = 0;
    std::uint16_t eerg_pnn_decision_count = 0;
    std::uint16_t eerg_pnn_mismatch_count = 0;
    std::uint16_t eerg_rdm_valid_count = 0;
    std::uint32_t eerg_rdm_code_sum = 0;
    bool rbbb_qrs_delay_applied = false;
    std::int32_t score_arr_before_eerg = 0;
    std::uint8_t pred_class = 0;
    bool pred_valid = false;

    void reset() noexcept;
    void tick(bool clear, const ScoreInputs& in) noexcept;
};

}  // namespace snn
