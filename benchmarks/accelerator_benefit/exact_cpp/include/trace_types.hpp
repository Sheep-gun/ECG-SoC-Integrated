#pragma once

#include <array>
#include <cstdint>

namespace snn {

struct FinalResult {
    std::uint8_t final_pred = 0;
    std::array<std::int32_t, 4> final_mem{{0, 0, 0, 0}};
    std::uint64_t accepted_samples = 0;
    std::uint32_t snapshot_count = 0;
    std::uint32_t decision_count = 0;
    bool valid = false;
};

struct SnapshotTrace {
    std::uint32_t snapshot_index = 0;
    std::uint64_t accepted_samples = 0;
    std::uint8_t snapshot_pred = 0;
    std::array<std::int64_t, 4> snapshot_scores{{0, 0, 0, 0}};
    std::uint32_t beat_count = 0;
    std::uint32_t pnn_match_count = 0;
    std::uint32_t pnn_mismatch_count = 0;
    std::uint32_t dscr_flip_count = 0;
    std::uint32_t dscr_slope_count = 0;
    std::uint32_t ram_code_sum = 0;
    std::uint32_t ram_code_count = 0;
    std::uint32_t rdm_valid_count = 0;
    std::uint32_t rdm_code_sum = 0;
    std::uint32_t ectopic_pair_count = 0;
    std::uint32_t qrs_maf_count = 0;
    std::uint32_t qrs_width_abn_count = 0;
    std::uint32_t qrs_complex_abn_count = 0;
    std::uint32_t qrs_energy_abn_count = 0;
    std::uint32_t rbbb_delay_like_count = 0;
    std::uint32_t rbbb_delay_applied_count = 0;
    std::uint32_t pre_qrs_bump_count = 0;
    std::uint32_t abnormal_evidence_count = 0;
    std::uint32_t rhythm_irregular_evidence_count = 0;
    std::uint32_t morphology_evidence_count = 0;
    std::array<std::int32_t, 4> final_mem_after{{0, 0, 0, 0}};
    std::array<std::uint8_t, 5> structural_gates{{0, 0, 0, 0, 0}};
    std::uint64_t state_hash = 0;
};

}  // namespace snn
