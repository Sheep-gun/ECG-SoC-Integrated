#pragma once

#include "model_types.hpp"
#include "trace_types.hpp"

#include <array>
#include <cstdint>
#include <vector>

namespace snn {

struct SnapshotFrontEnd {
    EcgEventEncoderAdaptive event;
    QrsLifDetector qrs;
    PnnRhythmPredictor pnn;
    RdmVariabilityNeuron rdm;
    EctopicPairNeuron ectopic;
    DscrSpikeCounter dscr;
    RamPeakAccumulator ram;
    QrsMafNeuron qrs_maf;
    RbbbQrsDelayBank rbbb;
    C24ScoreNeurons score;
    bool qrs_sample_valid = false;
    std::int16_t adc_frontend_d = 0;
    bool rdm_rr_valid_delay = false;
    std::uint32_t qrs_count = 0;
    std::uint32_t pnn_match_count = 0;
    std::uint32_t pnn_mismatch_count = 0;
    std::uint32_t dscr_flip_count = 0;
    std::uint32_t dscr_slope_count = 0;
    std::uint32_t ram_code_sum = 0;
    std::uint32_t ram_code_count = 0;
    std::uint32_t rdm_valid_count = 0;
    std::uint32_t rdm_code_sum = 0;
    std::array<std::uint32_t, 15> rdm_ge_count{};
    std::uint32_t ectopic_pair_count = 0;
    std::uint32_t qrs_maf_valid_count = 0;
    std::uint32_t qrs_maf_count = 0;
    std::uint32_t qrs_width_abn_count = 0;
    std::uint32_t qrs_complex_abn_count = 0;
    std::uint32_t qrs_energy_abn_count = 0;
    std::uint32_t pre_qrs_bump_count = 0;
    std::uint32_t rbbb_delay_valid_count = 0;
    std::uint32_t rbbb_delay_wide_count = 0;
    std::uint32_t rbbb_delay_terminal_count = 0;
    std::uint32_t rbbb_delay_like_count = 0;
    std::uint32_t rbbb_delay_segment_count = 0;
    std::uint32_t rbbb_delay_applied_count = 0;
    std::uint32_t strong_event_count = 0;

    void reset() noexcept;
    void tick(bool sample_valid, bool rhythm_tick, bool segment_start,
              bool segment_done, std::int16_t adc_data) noexcept;
    SnapshotTrace finish(std::uint32_t snapshot_index,
                         std::uint64_t accepted_samples) const noexcept;
    std::uint64_t architectural_state_hash() const noexcept;
    std::uint64_t accepted_sample_state_hash() const noexcept;
};

struct FinalMembrane {
    std::array<std::uint8_t, 4> pred_count{{0, 0, 0, 0}}; // 6-bit each
    std::uint32_t sum_beat = 0;
    std::uint32_t sum_pnn_mismatch = 0;
    std::uint32_t sum_ectopic_pair = 0;
    std::uint32_t sum_qrs_maf = 0;
    std::uint32_t sum_rbbb_like = 0;
    std::uint32_t sum_pre_qrs = 0;
    std::uint32_t sum_abnormal = 0;
    std::uint32_t sum_rhythm = 0;
    std::uint32_t sum_morphology = 0;
    std::uint32_t sum_rdm_valid = 0;
    std::uint32_t sum_rdm_code = 0;
    std::uint32_t sum_ram_code = 0;

    void reset() noexcept;
    FinalResult commit(const SnapshotTrace& snapshot, bool chunk_done,
                       std::uint64_t accepted_samples,
                       std::uint32_t snapshot_count) noexcept;
    std::array<std::int32_t, 4> current_membrane() const noexcept;
    std::array<std::uint8_t, 5> current_structural_gates() const noexcept;
};

class ExactModel {
public:
    void reset() noexcept;
    void begin_segment() noexcept;
    void process_sample(std::int16_t signed_12bit_sample);
    void end_segment_or_flush();
    const std::vector<SnapshotTrace>& get_snapshot_trace() const noexcept { return traces_; }
    const FinalResult& get_final_result() const noexcept { return final_result_; }
    std::uint64_t get_architectural_state_hash() const noexcept;
    std::uint64_t get_last_accepted_sample_state_hash() const noexcept {
        return last_accepted_sample_state_hash_;
    }

private:
    SnapshotFrontEnd frontend_;
    FinalMembrane final_;
    std::vector<SnapshotTrace> traces_;
    FinalResult final_result_;
    std::uint64_t accepted_samples_ = 0;
    std::uint64_t last_accepted_sample_state_hash_ = 0;
    std::uint32_t snapshot_count_ = 0;
    std::uint32_t segment_samples_ = 0;
    bool segment_active_ = false;
};

}  // namespace snn
