#include "exact_model.hpp"

#include "fixed_width.hpp"

#include <cstddef>
#include <stdexcept>

namespace snn {
namespace {
void hash_byte(std::uint64_t& hash, std::uint8_t value) noexcept {
    hash ^= value;
    hash *= 1099511628211ULL;
}
void hash_value(std::uint64_t& hash, bool value) noexcept {
    hash_byte(hash, value ? 1U : 0U);
}
template <typename T>
void hash_value(std::uint64_t& hash, T value) noexcept {
    using U = typename std::make_unsigned<T>::type;
    const U bits = static_cast<U>(value);
    for (std::size_t i = 0; i < sizeof(T); ++i)
        hash_byte(hash, static_cast<std::uint8_t>(bits >> (i * 8U)));
}
}

void SnapshotFrontEnd::reset() noexcept {
    *this = SnapshotFrontEnd{};
    event.reset(); qrs.reset(); pnn.reset(); rdm.reset(); ectopic.reset();
    dscr.reset(); ram.reset(); qrs_maf.reset(); rbbb.reset(); score.reset();
}

void SnapshotFrontEnd::tick(bool sample_valid, bool rhythm_tick,
                            bool segment_start, bool segment_done,
                            std::int16_t adc_data) noexcept {
    const bool old_qrs_sample_valid = qrs_sample_valid;
    const std::int16_t old_adc_d = adc_frontend_d;
    const bool old_rr_delay = rdm_rr_valid_delay;
    const bool old_strong = event.strong_event;
    const bool old_slope_valid = event.slope_valid;
    const std::uint16_t old_abs_delta = event.abs_delta;
    const bool old_beat = qrs.beat_spike;
    const bool old_pnn_match = pnn.pnn_match_spike;
    const bool old_pnn_mis = pnn.pnn_mismatch_spike;
    const bool old_token_active = pnn.token_active;
    const std::uint16_t old_rr = pnn.rr_interval;
    const bool old_rdm_valid = rdm.rr_diff_valid_spike;
    const std::uint16_t old_rdm_level = rdm.rdm_level_spike;
    const std::uint8_t old_rdm_code = rdm.rdm_level_code;
    const bool old_ect_pair = ectopic.ectopic_pair_spike;
    const bool old_ect_early = ectopic.early_rr_spike;
    const bool old_dscr_valid = dscr.valid_slope_spike;
    const bool old_dscr_flip = dscr.sign_flip_spike;
    const bool old_ram_spike = ram.ram_amp_spike;
    const std::uint8_t old_ram_code = ram.ram_amp_code;
    const bool old_maf_valid = qrs_maf.qrs_maf_valid_spike;
    const bool old_width = qrs_maf.qrs_width_abn_spike;
    const bool old_complex = qrs_maf.qrs_complex_abn_spike;
    const bool old_energy = qrs_maf.qrs_energy_abn_spike;
    const bool old_pre = qrs_maf.pre_qrs_bump_spike;
    const bool old_rbbb_valid = rbbb.qrs_valid_spike;
    const bool old_rbbb_wide = rbbb.wide_qrs_spike;
    const bool old_rbbb_terminal = rbbb.terminal_delay_spike;
    const bool old_rbbb_like = rbbb.rbbb_like_beat_spike;
    const std::uint8_t old_rbbb_like_count = rbbb.rbbb_like_beat_count;
    const bool rbbb_segment_now = rbbb.segment_spike(segment_done);
    const bool old_rbbb_applied = score.rbbb_qrs_delay_applied;
    const std::uint16_t center = PnnRhythmPredictor::hyp_center(pnn.predictor_id);
    const std::uint16_t error = PnnRhythmPredictor::abs_diff(pnn.token_age, center);
    const bool old_ram_window = pnn.token_active && pnn.predictor_valid && error <= 125;

    if (old_beat) qrs_count = static_cast<std::uint32_t>(fw::wrap_add<32>(qrs_count, 1));
    if (old_pnn_match) pnn_match_count = static_cast<std::uint32_t>(fw::wrap_add<32>(pnn_match_count, 1));
    if (old_pnn_mis) pnn_mismatch_count = static_cast<std::uint32_t>(fw::wrap_add<32>(pnn_mismatch_count, 1));
    if (old_rdm_valid) {
        rdm_valid_count = static_cast<std::uint32_t>(fw::wrap_add<32>(rdm_valid_count, 1));
        rdm_code_sum = static_cast<std::uint32_t>(fw::wrap_add<32>(rdm_code_sum, old_rdm_code));
        for (std::size_t i=0;i<15;++i) if ((old_rdm_level & (1U<<i)) != 0)
            rdm_ge_count[i] = static_cast<std::uint32_t>(fw::wrap_add<32>(rdm_ge_count[i],1));
    }
    if (old_ect_pair) ectopic_pair_count = static_cast<std::uint32_t>(fw::wrap_add<32>(ectopic_pair_count,1));
    if (old_dscr_valid) dscr_slope_count = static_cast<std::uint32_t>(fw::wrap_add<32>(dscr_slope_count,1));
    if (old_dscr_flip) dscr_flip_count = static_cast<std::uint32_t>(fw::wrap_add<32>(dscr_flip_count,1));
    if (old_ram_spike) {
        ram_code_count = static_cast<std::uint32_t>(fw::wrap_add<32>(ram_code_count,1));
        ram_code_sum = static_cast<std::uint32_t>(fw::wrap_add<32>(ram_code_sum,old_ram_code));
    }
    if (old_maf_valid) ++qrs_maf_valid_count;
    if (old_width || old_complex || old_energy) ++qrs_maf_count;
    if (old_width) ++qrs_width_abn_count;
    if (old_complex) ++qrs_complex_abn_count;
    if (old_energy) ++qrs_energy_abn_count;
    if (old_pre) ++pre_qrs_bump_count;
    if (old_rbbb_valid) ++rbbb_delay_valid_count;
    if (old_rbbb_wide) ++rbbb_delay_wide_count;
    if (old_rbbb_terminal) ++rbbb_delay_terminal_count;
    if (old_rbbb_like) ++rbbb_delay_like_count;
    if (rbbb_segment_now) ++rbbb_delay_segment_count;
    if (old_rbbb_applied) ++rbbb_delay_applied_count;

    ScoreInputs inputs;
    inputs.rhythm_tick=rhythm_tick; inputs.segment_done=segment_done; inputs.beat_spike=old_beat;
    inputs.qrs_maf_valid_spike=old_maf_valid; inputs.rbbb_qrs_valid_spike=old_rbbb_valid;
    inputs.rbbb_qrs_wide_spike=old_rbbb_wide; inputs.rbbb_qrs_terminal_spike=old_rbbb_terminal;
    inputs.rbbb_qrs_like_beat_spike=old_rbbb_like; inputs.pnn_match_spike=old_pnn_match;
    inputs.pnn_mismatch_spike=old_pnn_mis; inputs.dscr_valid_slope_spike=old_dscr_valid;
    inputs.dscr_sign_flip_spike=old_dscr_flip; inputs.ram_amp_spike=old_ram_spike;
    inputs.ram_amp_code=old_ram_code; inputs.rdm_valid_spike=old_rdm_valid;
    inputs.rdm_level_spike=old_rdm_level; inputs.rdm_level_code=old_rdm_code;
    inputs.ectopic_pair_spike=old_ect_pair; inputs.ectopic_early_spike=old_ect_early;
    inputs.pre_qrs_bump_spike=old_pre; inputs.qrs_width_abn_spike=old_width;
    inputs.qrs_complex_abn_spike=old_complex; inputs.qrs_energy_abn_spike=old_energy;
    inputs.rbbb_qrs_delay_segment_spike=rbbb_segment_now; inputs.rbbb_qrs_like_count=old_rbbb_like_count;
    score.tick(segment_start, inputs);

    event.tick(sample_valid, segment_start, adc_data);
    qrs.tick(old_qrs_sample_valid, old_strong);
    pnn.tick(segment_start, rhythm_tick, old_beat);
    rdm.tick(segment_start, old_rr_delay, old_rr);
    ectopic.tick(segment_start, old_rr_delay, old_rr);
    dscr.tick(segment_start, sample_valid, adc_data);
    ram.tick(segment_start, sample_valid, old_ram_window, old_beat, adc_data);
    qrs_maf.tick(segment_start, old_qrs_sample_valid, old_adc_d, old_strong,
                 old_dscr_flip, old_beat);
    rbbb.tick(segment_start, old_qrs_sample_valid, segment_done, old_strong,
              old_slope_valid, old_abs_delta, old_pnn_match, old_pnn_mis,
              old_rdm_valid, old_rdm_level, old_rdm_code);
    if (sample_valid) adc_frontend_d = adc_data;
    qrs_sample_valid = sample_valid;
    rdm_rr_valid_delay = old_beat && old_token_active && !segment_start;
    if (event.strong_event) ++strong_event_count;
}

SnapshotTrace SnapshotFrontEnd::finish(std::uint32_t index,
                                       std::uint64_t accepted) const noexcept {
    SnapshotTrace out;
    out.snapshot_index=index; out.accepted_samples=accepted; out.snapshot_pred=score.pred_class;
    out.snapshot_scores=score.c24_mem; out.beat_count=qrs_count;
    out.pnn_match_count=pnn_match_count; out.pnn_mismatch_count=pnn_mismatch_count;
    out.dscr_flip_count=dscr_flip_count; out.dscr_slope_count=dscr_slope_count;
    out.ram_code_sum=ram_code_sum; out.ram_code_count=ram_code_count;
    out.rdm_valid_count=rdm_valid_count; out.rdm_code_sum=rdm_code_sum;
    out.ectopic_pair_count=ectopic_pair_count; out.qrs_maf_count=qrs_maf_count;
    out.qrs_width_abn_count=qrs_width_abn_count; out.qrs_complex_abn_count=qrs_complex_abn_count;
    out.qrs_energy_abn_count=qrs_energy_abn_count; out.rbbb_delay_like_count=rbbb_delay_like_count;
    out.rbbb_delay_applied_count=rbbb_delay_applied_count; out.pre_qrs_bump_count=pre_qrs_bump_count;
    out.abnormal_evidence_count=pnn_mismatch_count+ectopic_pair_count+qrs_maf_count+
        qrs_width_abn_count+qrs_complex_abn_count+qrs_energy_abn_count+rbbb_delay_like_count;
    out.rhythm_irregular_evidence_count=pnn_mismatch_count+rdm_code_sum+ectopic_pair_count;
    out.morphology_evidence_count=dscr_flip_count+qrs_maf_count+qrs_width_abn_count+
        qrs_complex_abn_count+qrs_energy_abn_count+rbbb_delay_like_count;
    out.state_hash=architectural_state_hash();
    return out;
}

std::uint64_t SnapshotFrontEnd::architectural_state_hash() const noexcept {
    std::uint64_t h=1469598103934665603ULL;
    hash_value(h,event.prev_sample); hash_value(h,event.delta); hash_value(h,event.abs_delta);
    hash_value(h,event.sample_seen); hash_value(h,event.adaptive_ready); hash_value(h,event.adaptive_event_th);
    hash_value(h,qrs.qrs_mem); hash_value(h,qrs.refractory_cnt); hash_value(h,pnn.token_active);
    hash_value(h,pnn.token_age); hash_value(h,pnn.rr_interval); hash_value(h,pnn.predictor_id);
    hash_value(h,pnn.predictor_valid); hash_value(h,pnn.evaluating); hash_value(h,pnn.eval_idx);
    hash_value(h,rdm.prev_rr_valid); hash_value(h,rdm.prev_rr); hash_value(h,ectopic.rr_ref);
    hash_value(h,dscr.filt_mem); hash_value(h,dscr.up_mem); hash_value(h,dscr.down_mem);
    hash_value(h,ram.r_peak_abs); hash_value(h,ram.post_hold_active); hash_value(h,ram.post_hold_cnt);
    hash_value(h,qrs_maf.window_active); hash_value(h,qrs_maf.post_count); hash_value(h,qrs_maf.width_ref);
    hash_value(h,rbbb.qrs_active); hash_value(h,rbbb.qrs_age); hash_value(h,rbbb.rbbb_like_beat_count);
    for(auto v:score.c24_mem) hash_value(h,v);
    hash_value(h,score.subwindow_tick_count);
    hash_value(h,qrs_count); hash_value(h,pnn_match_count); hash_value(h,pnn_mismatch_count);
    hash_value(h,dscr_flip_count); hash_value(h,ram_code_sum); hash_value(h,rdm_code_sum);
    return h;
}

std::uint64_t SnapshotFrontEnd::accepted_sample_state_hash() const noexcept {
    // Cross-model checkpoint: persistent feature architecture only. Physical
    // class-score/readout staging and aggregate trace counters are excluded.
    std::uint64_t h=1469598103934665603ULL;
    hash_value(h,event.prev_sample); hash_value(h,event.delta); hash_value(h,event.abs_delta);
    hash_value(h,event.sample_seen); hash_value(h,event.adaptive_ready); hash_value(h,event.adaptive_event_th);
    hash_value(h,qrs.qrs_mem); hash_value(h,qrs.refractory_cnt); hash_value(h,pnn.token_active);
    hash_value(h,pnn.token_age); hash_value(h,pnn.rr_interval); hash_value(h,pnn.predictor_id);
    hash_value(h,pnn.predictor_valid); hash_value(h,pnn.evaluating); hash_value(h,pnn.eval_idx);
    hash_value(h,rdm.prev_rr_valid); hash_value(h,rdm.prev_rr); hash_value(h,ectopic.rr_ref);
    hash_value(h,dscr.filt_mem); hash_value(h,dscr.up_mem); hash_value(h,dscr.down_mem);
    hash_value(h,ram.r_peak_abs); hash_value(h,ram.post_hold_active); hash_value(h,ram.post_hold_cnt);
    hash_value(h,qrs_maf.window_active); hash_value(h,qrs_maf.post_count); hash_value(h,qrs_maf.width_ref);
    hash_value(h,rbbb.qrs_active); hash_value(h,rbbb.qrs_age); hash_value(h,rbbb.rbbb_like_beat_count);
    return h;
}

void ExactModel::reset() noexcept {
    frontend_.reset(); final_.reset(); traces_.clear(); final_result_=FinalResult{};
    accepted_samples_=0; last_accepted_sample_state_hash_=0; snapshot_count_=0;
    segment_samples_=0; segment_active_=false;
}

void ExactModel::begin_segment() noexcept {
    frontend_.reset();
    frontend_.tick(false,false,true,false,0);
    segment_samples_=0; segment_active_=true;
}

void ExactModel::process_sample(std::int16_t sample) {
    if (!segment_active_) begin_segment();
    if (sample < -2048 || sample > 2047) throw std::out_of_range("sample is not signed 12-bit");
    if (segment_samples_ >= 60000) throw std::logic_error("segment already contains 60000 samples");
    frontend_.tick(true,true,false,false,sample);
    last_accepted_sample_state_hash_=frontend_.accepted_sample_state_hash();
    ++accepted_samples_; ++segment_samples_;
    if (segment_samples_ == 60000) {
        // The boundary spike moves the RTL FSM directly from RUN to
        // SEG_DONE. Canonical inter-sample idle clocks exist only between
        // non-boundary accepted samples.
        end_segment_or_flush();
    } else {
        frontend_.tick(false,false,false,false,0);
        frontend_.tick(false,false,false,false,0);
    }
}

void ExactModel::end_segment_or_flush() {
    if (!segment_active_ || segment_samples_ != 60000)
        throw std::logic_error("Snapshot flush requires exactly 60000 accepted samples");
    frontend_.tick(false,false,false,true,0);
    // POST_DONE_TICKS is 37 physical FLUSH states. On the edge that leaves
    // FLUSH, ST_COMMIT and the final layer sample the pre-NBA architectural
    // values, so only 36 completed flush updates are observable at commit.
    for (int i=0;i<36;++i) frontend_.tick(false,false,false,false,0);
    SnapshotTrace trace=frontend_.finish(snapshot_count_,accepted_samples_);
    const bool done=snapshot_count_==29;
    final_result_=final_.commit(trace,done,accepted_samples_,snapshot_count_+1);
    trace.final_mem_after=final_.current_membrane();
    trace.structural_gates=final_.current_structural_gates();
#if EXACT_CPP_TRACE
    traces_.push_back(trace);
#endif
    ++snapshot_count_; segment_active_=false;
}

std::uint64_t ExactModel::get_architectural_state_hash() const noexcept {
    return frontend_.architectural_state_hash();
}

}  // namespace snn
