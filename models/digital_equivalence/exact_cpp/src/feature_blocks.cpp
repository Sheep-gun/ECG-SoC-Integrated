#include "model_types.hpp"

#include "fixed_width.hpp"

#include <algorithm>
#include <cstddef>

namespace snn {

constexpr std::array<std::uint16_t, 12> EcgEventEncoderAdaptive::bank_thresholds;
constexpr std::array<std::uint16_t, 15> RdmVariabilityNeuron::thresholds;

void EcgEventEncoderAdaptive::reset() noexcept {
    *this = EcgEventEncoderAdaptive{};
}

void EcgEventEncoderAdaptive::tick(bool sample_valid, bool segment_start,
                                   std::int16_t adc_data) noexcept {
    const EcgEventEncoderAdaptive old = *this;
    EcgEventEncoderAdaptive next = old;
    next.strong_event = false;
    next.up_event = false;
    next.down_event = false;
    next.slope_valid = false;

    if (segment_start) {
        next.adaptive_ready = false;
        next.adaptive_event_th = 5;
        next.calib_count = 0;
        next.hist.fill(0);
        next.bank_count.fill(0);
    }

    if (sample_valid) {
        if (!old.sample_seen) {
            next.prev_sample = adc_data;
            next.delta = 0;
            next.abs_delta = 0;
            next.sample_seen = true;
        } else {
            const std::int32_t delta_calc = static_cast<std::int32_t>(adc_data) - old.prev_sample;
            const std::uint16_t abs_delta_calc = static_cast<std::uint16_t>(
                delta_calc < 0 ? -delta_calc : delta_calc);
            const std::int32_t abs_adc = adc_data < 0 ? -static_cast<std::int32_t>(adc_data) : adc_data;
            const std::int32_t abs_prev = old.prev_sample < 0
                ? -static_cast<std::int32_t>(old.prev_sample) : old.prev_sample;
            constexpr bool enable_amp_event = false;
            const bool amp_cross = enable_amp_event && abs_adc > 4 && abs_prev <= 4;
            const std::uint8_t active_th = old.adaptive_ready ? old.adaptive_event_th : 5;
            next.prev_sample = adc_data;
            next.delta = static_cast<std::int16_t>(delta_calc);
            next.abs_delta = abs_delta_calc;
            next.strong_event = abs_delta_calc > active_th || amp_cross;
            if (delta_calc > 4) {
                next.up_event = true;
                next.slope_valid = true;
            } else if (delta_calc < -4) {
                next.down_event = true;
                next.slope_valid = true;
            }

            if (!old.adaptive_ready) {
                if (old.calib_count < 2000) {
                    const std::size_t bin = (abs_delta_calc >> 6U) != 0
                        ? 63U : static_cast<std::size_t>(abs_delta_calc & 0x3fU);
                    next.hist[bin] = static_cast<std::uint16_t>(
                        fw::wrap_add<16>(old.hist[bin], 1));
                    for (std::size_t i = 0; i < bank_thresholds.size(); ++i) {
                        if (abs_delta_calc > bank_thresholds[i]) {
                            next.bank_count[i] = static_cast<std::uint16_t>(
                                fw::wrap_add<16>(old.bank_count[i], 1));
                        }
                    }
                    next.calib_count = static_cast<std::uint16_t>(
                        fw::wrap_add<16>(old.calib_count, 1));
                }
                // RTL threshold selection observes the old bank counters on the
                // final calibration sample (nonblocking assignment semantics).
                if (old.calib_count == 1999) {
                    std::uint16_t selected = bank_thresholds.back();
                    for (std::size_t i = 0; i < bank_thresholds.size(); ++i) {
                        if (old.bank_count[i] <= 100) {
                            selected = bank_thresholds[i];
                            break;
                        }
                    }
                    next.adaptive_event_th = static_cast<std::uint8_t>(
                        std::max<std::uint16_t>(selected, 4));
                    next.adaptive_ready = true;
                }
            }
        }
    }
    *this = next;
}

void QrsLifDetector::reset() noexcept { *this = QrsLifDetector{}; }

void QrsLifDetector::tick(bool sample_valid, bool strong_event) noexcept {
    const QrsLifDetector old = *this;
    QrsLifDetector next = old;
    next.beat_spike = false;
    if (sample_valid) {
        if (old.refractory_cnt != 0) {
            next.qrs_mem = 0;
            next.refractory_cnt = static_cast<std::uint16_t>(
                fw::wrap_sub<10>(old.refractory_cnt, 1));
        } else {
            const std::uint16_t after_leak = old.qrs_mem; // locked leak is zero
            const std::uint16_t after_event = static_cast<std::uint16_t>(
                after_leak + (strong_event ? 8U : 0U));
            if (after_event >= 16) {
                next.beat_spike = true;
                next.qrs_mem = 0;
                next.refractory_cnt = 280;
            } else {
                next.qrs_mem = static_cast<std::uint16_t>(fw::truncate<12>(after_event));
            }
        }
    }
    *this = next;
}

void PnnRhythmPredictor::reset() noexcept { *this = PnnRhythmPredictor{}; }

std::uint16_t PnnRhythmPredictor::abs_diff(std::uint16_t a,
                                          std::uint16_t b) noexcept {
    return a >= b ? static_cast<std::uint16_t>(a - b)
                  : static_cast<std::uint16_t>(b - a);
}

std::uint16_t PnnRhythmPredictor::hyp_center(std::uint8_t index) noexcept {
    const std::uint32_t center = base_delay + static_cast<std::uint32_t>(index) * delay_step;
    return static_cast<std::uint16_t>(center > max_age ? max_age : center);
}

void PnnRhythmPredictor::tick(bool clear, bool rhythm_tick,
                              bool beat_spike) noexcept {
    if (clear) {
        reset();
        return;
    }
    const PnnRhythmPredictor old = *this;
    PnnRhythmPredictor next = old;
    next.pnn_match_spike = false;
    next.pnn_mismatch_spike = false;

    const std::uint16_t age_eval = old.token_active && rhythm_tick && old.token_age != max_age
        ? static_cast<std::uint16_t>(old.token_age + 1U) : old.token_age;
    const std::uint16_t scan_err = abs_diff(old.eval_age, hyp_center(old.eval_idx));
    const bool scan_better = scan_err < old.eval_best_err;
    const std::uint8_t scan_best_id = scan_better ? old.eval_idx : old.eval_best_id;
    const std::uint16_t scan_best_err = scan_better ? scan_err : old.eval_best_err;
    const std::uint16_t predictor_err = abs_diff(old.eval_age, hyp_center(old.eval_predictor_id));

    if (beat_spike) {
        if (old.token_active) {
            next.rr_interval = age_eval;
            next.eval_age = age_eval;
            next.eval_idx = 0;
            next.eval_best_id = 0;
            next.eval_best_err = max_age;
            next.eval_predictor_id = old.predictor_id;
            next.eval_predictor_valid = old.predictor_valid;
            next.evaluating = true;
        } else {
            next.winner_valid = false;
            next.predictor_valid = false;
            next.predictor_error = max_age;
            next.evaluating = false;
        }
        next.token_active = true;
        next.token_age = 0;
    } else {
        if (old.evaluating && rhythm_tick) {
            if (old.eval_idx == num_hyp - 1U) {
                next.winner_id = scan_best_id;
                next.winner_error = scan_best_err;
                next.winner_valid = true;
                next.predictor_id = scan_best_id;
                next.predictor_valid = true;
                next.evaluating = false;
                if (old.eval_predictor_valid) {
                    next.predictor_error = predictor_err;
                    next.pnn_match_spike = predictor_err <= window_half;
                    next.pnn_mismatch_spike = predictor_err > window_half;
                } else {
                    next.predictor_error = max_age;
                }
            } else {
                next.eval_best_id = scan_best_id;
                next.eval_best_err = scan_best_err;
                next.eval_idx = static_cast<std::uint8_t>(old.eval_idx + 1U);
            }
        }
        if (rhythm_tick && old.token_active) {
            next.token_age = age_eval;
        }
    }
    *this = next;
}

void RdmVariabilityNeuron::reset() noexcept { *this = RdmVariabilityNeuron{}; }

void RdmVariabilityNeuron::tick(bool clear, bool valid,
                                std::uint16_t rr) noexcept {
    const RdmVariabilityNeuron old = *this;
    RdmVariabilityNeuron next = old;
    next.rr_diff_valid_spike = false;
    next.rdm_level_spike = 0;
    next.rdm_level_code = 0;
    if (clear) {
        next.prev_rr_valid = false;
        next.current_rr = 0;
        next.prev_rr = 0;
        next.rr_diff = 0;
    } else if (valid) {
        const std::uint16_t diff = PnnRhythmPredictor::abs_diff(rr, old.prev_rr);
        std::uint16_t level = 0;
        std::uint8_t code = 0;
        for (std::size_t i = 0; i < thresholds.size(); ++i) {
            if (diff >= thresholds[i]) {
                level = static_cast<std::uint16_t>(level | (std::uint16_t{1} << i));
                code = static_cast<std::uint8_t>(i + 1U);
            }
        }
        next.current_rr = rr;
        if (old.prev_rr_valid) {
            next.rr_diff = diff;
            next.rr_diff_valid_spike = true;
            next.rdm_level_spike = level;
            next.rdm_level_code = code;
        }
        next.prev_rr = rr;
        next.prev_rr_valid = true;
    }
    *this = next;
}

void EctopicPairNeuron::reset() noexcept { *this = EctopicPairNeuron{}; }

void EctopicPairNeuron::tick(bool clear, bool valid,
                             std::uint16_t rr) noexcept {
    const EctopicPairNeuron old = *this;
    EctopicPairNeuron next = old;
    next.early_rr_spike = false;
    next.late_rr_spike = false;
    next.ectopic_pair_spike = false;

    std::uint8_t pattern = 0;
    if (old.ref_valid) {
        const std::uint16_t rr_plus = static_cast<std::uint16_t>(fw::wrap_add<12>(rr, 120));
        const std::uint16_t ref_plus = static_cast<std::uint16_t>(fw::wrap_add<12>(old.rr_ref, 120));
        if (rr_plus < old.rr_ref) {
            pattern = 1;
        } else if (rr > ref_plus) {
            pattern = 2;
        }
    }
    const std::uint16_t diff = PnnRhythmPredictor::abs_diff(rr, old.rr_ref);
    const std::uint16_t step = static_cast<std::uint16_t>(diff >> 4U);

    if (clear) {
        next.ref_valid = false;
        next.prev_pattern = 0;
        next.rr_ref = 0;
    } else if (valid) {
        if (!old.ref_valid) {
            next.rr_ref = rr;
            next.ref_valid = true;
            next.prev_pattern = 0;
        } else {
            next.early_rr_spike = pattern == 1;
            next.late_rr_spike = pattern == 2;
            next.ectopic_pair_spike = pattern != 0 && old.prev_pattern != 0 &&
                                      pattern != old.prev_pattern;
            if (pattern != 0) {
                next.prev_pattern = pattern;
            }
            next.rr_ref = static_cast<std::uint16_t>(rr >= old.rr_ref
                ? fw::wrap_add<12>(old.rr_ref, step)
                : fw::wrap_sub<12>(old.rr_ref, step));
        }
    }
    *this = next;
}

void DscrSpikeCounter::reset() noexcept { *this = DscrSpikeCounter{}; }

void DscrSpikeCounter::tick(bool clear, bool sample_valid,
                            std::int16_t adc_data) noexcept {
    if (clear) {
        reset();
        return;
    }
    DscrSpikeCounter next = *this;
    next.valid_slope_spike = false;
    next.sign_flip_spike = false;
    if (sample_valid) {
        if (!sample_seen) {
            next.sample_seen = true;
            next.filt_mem = static_cast<std::int32_t>(fw::signed_value<24>(
                fw::from_signed<24>(static_cast<std::int64_t>(adc_data) << 8U)));
        } else {
            const std::uint64_t adc_fp = fw::from_signed<24>(static_cast<std::int64_t>(adc_data) << 8U);
            const std::uint64_t error = fw::wrap_sub<25>(fw::sign_extend<24, 25>(adc_fp),
                fw::sign_extend<24, 25>(fw::from_signed<24>(filt_mem)));
            const std::int32_t update = static_cast<std::int32_t>(
                fw::signed_value<25>(fw::arithmetic_right<25>(error, 4)));
            next.filt_mem = static_cast<std::int32_t>(fw::signed_value<24>(
                fw::wrap_add<24>(fw::from_signed<24>(filt_mem), fw::from_signed<24>(update))));
            const std::uint32_t magnitude = static_cast<std::uint32_t>(update < 0 ? -update : update);
            const std::uint32_t slope_shifted = magnitude >> 8U;
            const std::uint16_t slope_input = (slope_shifted >> 16U) != 0
                ? 0xffffU : static_cast<std::uint16_t>(slope_shifted);
            std::uint16_t up = up_mem > 8 ? static_cast<std::uint16_t>(up_mem - 8U) : 0;
            std::uint16_t down = down_mem > 8 ? static_cast<std::uint16_t>(down_mem - 8U) : 0;
            std::uint16_t sign = sign_mem; // locked sign leak is zero
            bool slope_spike = false;
            bool slope_sign = false;
            if (update > 0 && slope_input != 0) {
                up = static_cast<std::uint16_t>(fw::saturating_unsigned_add<16>(up, slope_input));
                if (up >= 8) {
                    slope_spike = true;
                    slope_sign = true;
                    up = 0;
                    down = 0;
                }
            } else if (update < 0 && slope_input != 0) {
                down = static_cast<std::uint16_t>(fw::saturating_unsigned_add<16>(down, slope_input));
                if (down >= 8) {
                    slope_spike = true;
                    up = 0;
                    down = 0;
                }
            }
            if (slope_spike) {
                next.valid_slope_spike = true;
                if (prev_slope_valid && slope_sign != prev_slope_sign) {
                    sign = static_cast<std::uint16_t>(fw::saturating_unsigned_add<16>(sign, 1));
                    if (sign >= 1) {
                        next.sign_flip_spike = true;
                        sign = 0;
                    }
                }
                next.prev_slope_valid = true;
                next.prev_slope_sign = slope_sign;
            }
            next.up_mem = up;
            next.down_mem = down;
            next.sign_mem = sign;
        }
    }
    *this = next;
}

void RamPeakAccumulator::reset() noexcept { *this = RamPeakAccumulator{}; }

std::uint8_t RamPeakAccumulator::encode_amp_code(std::int32_t amplitude) noexcept {
    std::uint8_t code = 0;
    for (std::uint8_t i = 0; i < 32; ++i) {
        if (amplitude >= 32 + static_cast<std::int32_t>(i) * 32) {
            code = static_cast<std::uint8_t>(i + 1U);
        }
    }
    return static_cast<std::uint8_t>(fw::truncate<6>(code));
}

void RamPeakAccumulator::tick(bool clear, bool sample_valid,
                              bool ram_window_open, bool beat_spike,
                              std::int16_t adc_data) noexcept {
    if (clear) {
        reset();
        return;
    }
    const RamPeakAccumulator old = *this;
    RamPeakAccumulator next = old;
    next.ram_amp_spike = false;
    next.ram_window_open_d = ram_window_open;
    bool capture = ram_window_open || old.post_hold_active;
    const std::int32_t positive_amp = std::max<std::int32_t>(adc_data, 0);

    if (ram_window_open && !old.ram_window_open_d) {
        next.amp_window_active = true;
        next.amp_window_cnt = 0;
        next.r_peak_abs = 0;
        next.beat_seen = false;
        next.post_hold_active = false;
        next.post_hold_cnt = 0;
        capture = ram_window_open;
    }
    if (capture) {
        std::uint8_t peak = static_cast<std::uint8_t>(fw::truncate<6>(old.r_peak_abs));
        if (sample_valid) {
            peak = std::max(peak, encode_amp_code(positive_amp));
            next.r_peak_abs = peak;
        }
        if (beat_spike && ram_window_open) {
            next.beat_seen = true;
            next.post_hold_active = true;
            next.post_hold_cnt = 80;
        } else if (old.post_hold_active && sample_valid) {
            if (old.post_hold_cnt <= 1) {
                next.post_hold_active = false;
                next.post_hold_cnt = 0;
            } else {
                next.post_hold_cnt = static_cast<std::uint8_t>(fw::wrap_sub<8>(old.post_hold_cnt, 1));
            }
        }
    }
    if (!ram_window_open && old.ram_window_open_d && !old.beat_seen &&
        !old.post_hold_active) {
        next.amp_window_active = false;
        next.amp_window_cnt = static_cast<std::uint8_t>(fw::truncate<6>(old.r_peak_abs));
        next.beat_seen = false;
    }
    if (old.post_hold_active && sample_valid && old.post_hold_cnt <= 1) {
        next.amp_window_active = false;
        next.amp_window_cnt = static_cast<std::uint8_t>(fw::truncate<6>(old.r_peak_abs));
        if (old.beat_seen) {
            next.ram_amp_code = static_cast<std::uint8_t>(fw::truncate<6>(old.r_peak_abs));
            next.ram_amp_spike = true;
        }
        next.beat_seen = false;
    }
    *this = next;
}

void QrsMafNeuron::reset() noexcept { *this = QrsMafNeuron{}; }

std::uint8_t QrsMafNeuron::logical_strong(std::size_t index) const noexcept {
    return pre_strong[(static_cast<std::size_t>(pre_head) + index) % pre_win];
}

void QrsMafNeuron::tick(bool clear, bool sample_valid, std::int16_t adc_data,
                        bool strong_event, bool dscr_flip,
                        bool beat_spike) noexcept {
    if (clear) {
        reset();
        return;
    }
    const QrsMafNeuron old = *this;
    QrsMafNeuron next = old;
    next.qrs_maf_valid_spike = false;
    next.qrs_width_abn_spike = false;
    next.qrs_complex_abn_spike = false;
    next.qrs_energy_abn_spike = false;
    next.pre_qrs_bump_spike = false;

    bool pre_seen = false;
    std::uint8_t pre_first = 0;
    std::uint8_t pre_last = 0;
    for (std::size_t i = 0; i < pre_win; ++i) {
        if (old.logical_strong(pre_win - 1U - i) != 0) {
            if (!pre_seen) {
                pre_seen = true;
                pre_first = static_cast<std::uint8_t>(i);
            }
            pre_last = static_cast<std::uint8_t>(i);
        }
    }
    const std::int32_t signed_adc = adc_data;
    const std::uint32_t magnitude = static_cast<std::uint32_t>(
        signed_adc < 0 ? -signed_adc : signed_adc);
    const std::uint32_t energy_shift = magnitude >> 5U;
    const std::uint8_t energy_code = static_cast<std::uint8_t>(
        energy_shift > 0xffU ? 0xffU : energy_shift);
    const bool event_seen_eval = old.event_seen || strong_event;
    std::uint8_t first_eval = old.first_pos;
    if (!old.event_seen && strong_event) {
        first_eval = static_cast<std::uint8_t>(fw::wrap_add<8>(120, old.post_count));
    }
    const std::uint8_t last_eval = strong_event
        ? static_cast<std::uint8_t>(fw::wrap_add<8>(120, old.post_count))
        : old.last_pos;
    const std::uint8_t width_eval = event_seen_eval
        ? static_cast<std::uint8_t>(fw::wrap_sub<8>(last_eval, first_eval)) : 0;
    const std::uint8_t width_diff = static_cast<std::uint8_t>(
        width_eval >= old.width_ref ? width_eval - old.width_ref : old.width_ref - width_eval);
    const std::uint8_t flip_eval = static_cast<std::uint8_t>(
        fw::wrap_add<8>(old.flip_count, dscr_flip ? 1U : 0U));
    const std::uint16_t energy_sum_eval = old.energy_sum <= 0xffffU - energy_code
        ? static_cast<std::uint16_t>(old.energy_sum + energy_code) : 0xffffU;
    const std::uint16_t energy_shifted = static_cast<std::uint16_t>(energy_sum_eval >> 6U);
    const std::uint8_t energy_next = static_cast<std::uint8_t>(
        energy_shifted > 63 ? 63 : energy_shifted);
    const std::uint8_t energy_diff = static_cast<std::uint8_t>(energy_next >= old.energy_ref
        ? energy_next - old.energy_ref : old.energy_ref - energy_next);
    const std::uint8_t complex_next = std::min<std::uint8_t>(flip_eval, 63);
    const bool wide = width_eval >= 120 || (old.width_ref_valid && width_diff >= 40);
    const bool complex = complex_next >= 6;
    const bool energy_abnormal = old.energy_ref_valid && energy_diff >= 8;

    if (sample_valid) {
        const std::size_t old_tail = (static_cast<std::size_t>(old.pre_head) + pre_win - 1U) % pre_win;
        const std::uint8_t new_head = static_cast<std::uint8_t>(
            (static_cast<std::size_t>(old.pre_head) + pre_win - 1U) % pre_win);
        next.pre_head = new_head;
        next.pre_strong[new_head] = strong_event ? 1U : 0U;
        next.pre_flip[new_head] = dscr_flip ? 1U : 0U;
        next.pre_energy[new_head] = energy_code;
        next.pre_strong_count = static_cast<std::uint8_t>(fw::wrap_sub<8>(
            fw::wrap_add<8>(old.pre_strong_count, strong_event ? 1U : 0U),
            old.pre_strong[old_tail]));
        next.pre_flip_count = static_cast<std::uint8_t>(fw::wrap_sub<8>(
            fw::wrap_add<8>(old.pre_flip_count, dscr_flip ? 1U : 0U),
            old.pre_flip[old_tail]));
        next.pre_energy_sum = static_cast<std::uint16_t>(fw::wrap_sub<16>(
            fw::wrap_add<16>(old.pre_energy_sum, energy_code), old.pre_energy[old_tail]));

        if (beat_spike) {
            next.window_active = true;
            next.post_count = 1;
            next.event_seen = pre_seen || strong_event;
            next.first_pos = pre_seen ? pre_first : (strong_event ? 120U : 0U);
            next.last_pos = strong_event ? 120U : (pre_seen ? pre_last : 0U);
            next.event_count = static_cast<std::uint8_t>(
                fw::wrap_add<8>(old.pre_strong_count, strong_event ? 1U : 0U));
            next.flip_count = static_cast<std::uint8_t>(
                fw::wrap_add<8>(old.pre_flip_count, dscr_flip ? 1U : 0U));
            next.energy_sum = static_cast<std::uint16_t>(
                fw::wrap_add<16>(old.pre_energy_sum, energy_code));
            next.pre_strong_at_beat = old.pre_strong_count;
            next.pre_flip_at_beat = old.pre_flip_count;
            next.pre_energy_at_beat = old.pre_energy_sum;
        } else if (old.window_active) {
            if (strong_event) {
                if (!old.event_seen) {
                    next.event_seen = true;
                    next.first_pos = static_cast<std::uint8_t>(fw::wrap_add<8>(120, old.post_count));
                }
                next.last_pos = static_cast<std::uint8_t>(fw::wrap_add<8>(120, old.post_count));
                if (old.event_count != 0xffU) next.event_count = static_cast<std::uint8_t>(old.event_count + 1U);
            }
            if (dscr_flip && old.flip_count != 0xffU) next.flip_count = static_cast<std::uint8_t>(old.flip_count + 1U);
            next.energy_sum = energy_sum_eval;
            if (old.post_count >= 99) {
                next.window_active = false;
                next.qrs_maf_valid_spike = true;
                next.qrs_width_value = width_eval;
                next.qrs_complex_count = complex_next;
                next.qrs_energy_code = energy_next;
                next.qrs_width_abn_spike = wide;
                next.qrs_complex_abn_spike = complex;
                next.qrs_energy_abn_spike = energy_abnormal;
                next.pre_qrs_bump_spike = old.pre_strong_at_beat != 0 ||
                    old.pre_flip_at_beat >= 2 || old.pre_energy_at_beat >= 32;
                if (!old.width_ref_valid) {
                    next.width_ref = width_eval;
                    next.width_ref_valid = true;
                } else if (width_eval >= old.width_ref) {
                    next.width_ref = static_cast<std::uint8_t>(old.width_ref +
                        ((width_eval - old.width_ref) >> 3U));
                } else {
                    next.width_ref = static_cast<std::uint8_t>(old.width_ref -
                        ((old.width_ref - width_eval) >> 3U));
                }
                if (!old.energy_ref_valid) {
                    next.energy_ref = energy_next;
                    next.energy_ref_valid = true;
                } else if (energy_next >= old.energy_ref) {
                    const std::uint32_t adjusted=static_cast<std::uint32_t>(old.energy_ref) +
                        ((static_cast<std::uint32_t>(energy_next) - old.energy_ref) >> 3U);
                    next.energy_ref = static_cast<std::uint8_t>(fw::truncate<6>(adjusted));
                } else {
                    const std::uint32_t adjusted=static_cast<std::uint32_t>(old.energy_ref) -
                        ((static_cast<std::uint32_t>(old.energy_ref) - energy_next) >> 3U);
                    next.energy_ref = static_cast<std::uint8_t>(fw::truncate<6>(adjusted));
                }
            } else {
                next.post_count = static_cast<std::uint8_t>(fw::wrap_add<8>(old.post_count, 1));
            }
        }
    }
    *this = next;
}

void RbbbQrsDelayBank::reset() noexcept { *this = RbbbQrsDelayBank{}; }

bool RbbbQrsDelayBank::low_irregularity() const noexcept {
    const std::uint32_t total = static_cast<std::uint32_t>(pnn_match_count) + pnn_mismatch_count;
    return total == 0 || static_cast<std::uint32_t>(pnn_mismatch_count) * 100U <= total * 18U;
}

bool RbbbQrsDelayBank::high_rdm_irregularity() const noexcept {
    return rdm_valid_count != 0 &&
        static_cast<std::uint32_t>(rdm_high_count) * 100U >=
        static_cast<std::uint32_t>(rdm_valid_count) * 5U;
}

bool RbbbQrsDelayBank::segment_spike(bool done) const noexcept {
    return done && low_irregularity() && rbbb_like_beat_count >= 5;
}

void RbbbQrsDelayBank::tick(bool clear, bool sample_valid, bool segment_done,
                            bool /*strong_event*/, bool /*slope_valid*/,
                            std::uint16_t abs_delta, bool pnn_match_spike,
                            bool pnn_mismatch_spike, bool rdm_valid_spike,
                            std::uint16_t rdm_level_spike,
                            std::uint8_t rdm_level_code) noexcept {
    if (clear) {
        reset();
        return;
    }
    const RbbbQrsDelayBank old = *this;
    RbbbQrsDelayBank next = old;
    next.qrs_onset_spike = false;
    next.qrs_valid_spike = false;
    next.wide_qrs_spike = false;
    next.terminal_delay_spike = false;
    next.rbbb_like_beat_spike = false;

    // Locked activity mode 1 uses abs-delta >= 5, independent of strong/slope.
    const bool activity = abs_delta >= 5;
    const bool onset = sample_valid && activity && !old.prev_activity &&
                       !old.qrs_active && old.onset_ref_cnt == 0;
    const std::uint8_t age_next = static_cast<std::uint8_t>(fw::wrap_add<8>(old.qrs_age, 1));
    const std::uint8_t gap_next = activity ? 0 :
        (old.activity_gap_cnt == 0xffU ? 0xffU : static_cast<std::uint8_t>(old.activity_gap_cnt + 1U));
    const bool terminal_zone = age_next >= 90 && age_next < 170;
    std::uint16_t hyp_next = old.hyp_match;
    if (activity) {
        constexpr std::array<std::uint8_t, 9> ages = {{80,90,100,110,120,130,140,150,160}};
        for (std::size_t i = 0; i < ages.size(); ++i) {
            if (age_next == ages[i]) hyp_next = static_cast<std::uint16_t>(hyp_next | (1U << i));
        }
    }
    std::uint8_t terminal_next = old.terminal_count_work;
    if (activity && terminal_zone && terminal_next != 0xffU) ++terminal_next;
    const bool qrs_end = sample_valid && old.qrs_active && (age_next >= 200 || gap_next >= 15);
    std::uint8_t last_width = 0;
    constexpr std::array<std::uint8_t, 9> widths = {{80,90,100,110,120,130,140,150,160}};
    for (int bit = 8; bit >= 0; --bit) {
        if ((hyp_next & (1U << bit)) != 0) {
            last_width = widths[static_cast<std::size_t>(bit)];
            break;
        }
    }
    const bool wide = last_width >= 120;
    const bool terminal = terminal_next >= 4;
    const bool like = wide && terminal;

    if (pnn_match_spike && next.pnn_match_count != 0xffffU) ++next.pnn_match_count;
    if (pnn_mismatch_spike && next.pnn_mismatch_count != 0xffffU) ++next.pnn_mismatch_count;
    if (rdm_valid_spike && next.rdm_valid_count != 0xffffU) ++next.rdm_valid_count;
    if (rdm_valid_spike) {
        next.rdm_code_sum = static_cast<std::uint32_t>(
            fw::wrap_add<20>(next.rdm_code_sum, rdm_level_code));
        bool high = false;
        for (unsigned bit = 11; bit < 15; ++bit) high = high || ((rdm_level_spike & (1U << bit)) != 0);
        if (high && next.rdm_high_count != 0xffffU) ++next.rdm_high_count;
    }

    if (sample_valid) {
        next.prev_activity = activity;
        if (old.onset_ref_cnt != 0) next.onset_ref_cnt = static_cast<std::uint8_t>(old.onset_ref_cnt - 1U);
        if (onset) {
            next.qrs_active = true;
            next.qrs_onset_spike = true;
            next.onset_ref_cnt = 200;
            next.qrs_age = 0;
            next.activity_gap_cnt = 0;
            next.hyp_match = 0;
            next.terminal_count_work = 0;
        } else if (old.qrs_active) {
            next.qrs_age = age_next;
            next.activity_gap_cnt = gap_next;
            next.hyp_match = hyp_next;
            next.terminal_count_work = terminal_next;
            if (qrs_end) {
                next.qrs_active = false;
                next.qrs_valid_spike = true;
                next.wide_qrs_spike = wide;
                next.terminal_delay_spike = terminal;
                next.rbbb_like_beat_spike = like;
                next.last_matched_width = last_width;
                next.terminal_activity_count = terminal_next;
                next.max_last_matched_width = std::max(next.max_last_matched_width, last_width);
                if (next.valid_qrs_count != 0xffU) ++next.valid_qrs_count;
                if (wide && next.wide_qrs_count != 0xffU) ++next.wide_qrs_count;
                if (terminal && next.terminal_delay_count != 0xffU) ++next.terminal_delay_count;
                if (like && next.rbbb_like_beat_count != 0xffU) ++next.rbbb_like_beat_count;
            }
        }
    }
    if (segment_done) {
        next.qrs_active = false;
        next.qrs_age = 0;
        next.activity_gap_cnt = 0;
        next.hyp_match = 0;
        next.terminal_count_work = 0;
        next.pnn_match_count = 0;
        next.pnn_mismatch_count = 0;
        next.rdm_valid_count = 0;
        next.rdm_high_count = 0;
        next.rdm_code_sum = 0;
        next.valid_qrs_count = 0;
        next.wide_qrs_count = 0;
        next.terminal_delay_count = 0;
        next.rbbb_like_beat_count = 0;
        next.max_last_matched_width = 0;
    }
    *this = next;
}

}  // namespace snn
