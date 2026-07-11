#include "exact_model.hpp"

#include "fixed_width.hpp"
#include "locked_parameters.hpp"

#include <array>
#include <cstdint>

namespace snn {
namespace {

std::int32_t add32(std::int32_t a, std::int64_t b) noexcept {
    return static_cast<std::int32_t>(fw::signed_value<32>(
        fw::wrap_add<32>(fw::from_signed<32>(a), fw::from_signed<32>(b))));
}

std::uint8_t argmax_counts(const std::array<std::uint8_t,4>& values) noexcept {
    std::uint8_t best=0;
    for(std::uint8_t i=1;i<4;++i) if(values[i]>values[best]) best=i;
    return best;
}

std::uint8_t argmax_mem(const std::array<std::int32_t,4>& values) noexcept {
    std::uint8_t best=0;
    for(std::uint8_t i=1;i<4;++i) if(values[i]>values[best]) best=i;
    return best;
}

bool ge_u32(std::uint32_t value, std::int64_t threshold) noexcept {
    return static_cast<std::int64_t>(value)>=threshold;
}
bool lt_u8(std::uint8_t value, std::int64_t threshold) noexcept {
    return static_cast<std::int64_t>(value)<threshold;
}

}  // namespace

void FinalMembrane::reset() noexcept { *this=FinalMembrane{}; }

std::array<std::uint8_t,5> FinalMembrane::current_structural_gates() const noexcept {
    const bool aff=pred_count[3]>=params::STRICT_RW_FINAL_AFF_CNT && pred_count[1]>=params::STRICT_RW_FINAL_AFF_CHF_CNT && sum_morphology<=params::STRICT_RW_FINAL_AFF_MORPH_LE && sum_rhythm>=params::STRICT_RW_FINAL_AFF_RHYTHM_GE && sum_qrs_maf<=params::STRICT_RW_FINAL_AFF_QRS_LE;
    const bool nsr=pred_count[0]>=params::STRICT_RW_FINAL_NSR_CNT && pred_count[1]>=params::STRICT_RW_FINAL_NSR_CHF_CNT && sum_morphology<=params::STRICT_RW_FINAL_NSR_MORPH_LE && sum_abnormal<=params::STRICT_RW_FINAL_NSR_ABN_LE && sum_qrs_maf<=params::STRICT_RW_FINAL_NSR_QRS_LE && sum_ectopic_pair<=params::STRICT_RW_FINAL_NSR_ECT_LE;
    const bool high=pred_count[2]>=params::STRICT_RW_FINAL_ARR_NSR_ARR_CNT && sum_qrs_maf<=params::STRICT_RW_FINAL_ARR_NSR_QRS_HIGH_LE && sum_rbbb_like<=params::STRICT_RW_FINAL_ARR_NSR_RBBB_HIGH_LE;
    const bool low=pred_count[2]<=params::STRICT_RW_FINAL_ARR_NSR_ARR_LOW_LE && sum_qrs_maf<=params::STRICT_RW_FINAL_ARR_NSR_QRS_LOW_LE && sum_ectopic_pair<=params::STRICT_RW_FINAL_ARR_NSR_ECT_LOW_LE && sum_rhythm<=params::STRICT_RW_FINAL_ARR_NSR_RHYTHM_LOW_LE;
    const bool arr_nsr=pred_count[0]>=params::STRICT_RW_FINAL_ARR_NSR_NSR_CNT && sum_morphology>=params::STRICT_RW_FINAL_ARR_NSR_MORPH_GE && sum_pre_qrs>=params::STRICT_RW_FINAL_ARR_NSR_PRE_GE && (high||low);
    const bool arr_aff=pred_count[3]>=params::STRICT_RW_FINAL_ARR_AFF_AFF_CNT && pred_count[2]>=params::STRICT_RW_FINAL_ARR_AFF_ARR_CNT && sum_morphology>=params::STRICT_RW_FINAL_ARR_AFF_MORPH_GE && sum_ectopic_pair>=params::STRICT_RW_FINAL_ARR_AFF_ECT_GE && sum_qrs_maf<=params::STRICT_RW_FINAL_ARR_AFF_QRS_LE;
    const bool silent=pred_count[1]>=params::STRICT_RW_SILENT_AFF_CHF_CNT_GE && pred_count[0]<=params::STRICT_RW_SILENT_AFF_NSR_CNT_LE && pred_count[2]==params::STRICT_RW_SILENT_AFF_ARR_CNT_EQ && pred_count[3]==params::STRICT_RW_SILENT_AFF_AFF_CNT_EQ && sum_beat<=params::STRICT_RW_SILENT_AFF_BEAT_LE && sum_morphology<=params::STRICT_RW_SILENT_AFF_MORPH_LE && sum_rhythm<=params::STRICT_RW_SILENT_AFF_RHYTHM_LE && sum_abnormal<=params::STRICT_RW_SILENT_AFF_ABN_LE && sum_qrs_maf<=params::STRICT_RW_SILENT_AFF_QRS_LE && sum_ectopic_pair==params::STRICT_RW_SILENT_AFF_ECT_EQ && sum_ram_code==params::STRICT_RW_SILENT_AFF_RAM_EQ;
    return {{static_cast<std::uint8_t>(aff),static_cast<std::uint8_t>(nsr),static_cast<std::uint8_t>(arr_nsr),static_cast<std::uint8_t>(arr_aff),static_cast<std::uint8_t>(silent)}};
}

std::array<std::int32_t,4> FinalMembrane::current_membrane() const noexcept {
    const std::uint8_t base_pred=argmax_counts(pred_count);
    const bool base_nsr=base_pred==0, base_chf=base_pred==1, base_arr=base_pred==2, base_aff=base_pred==3;
    const std::int32_t nsr_minus_arr=static_cast<std::int32_t>(pred_count[0])-pred_count[2];
    const std::int32_t chf_minus_aff=static_cast<std::int32_t>(pred_count[1])-pred_count[3];
    const bool rdm_code_ge_aff_low=sum_rdm_valid!=0 && static_cast<std::uint64_t>(sum_rdm_code)>=static_cast<std::uint64_t>(sum_rdm_valid)*11U;
    const bool strong_nsr=base_nsr && (pred_count[0]>=params::STRICT_RW_BASE_STRONG_NSR_COUNT_GE ||
        (nsr_minus_arr>=params::STRICT_RW_BASE_STRONG_NSR_MARGIN_GE && sum_morphology<=params::STRICT_RW_BASE_STRONG_NSR_MORPH_LE && sum_qrs_maf<=params::STRICT_RW_BASE_STRONG_NSR_QRS_LE));
    const bool strong_chf=base_chf && (pred_count[1]>=params::STRICT_RW_BASE_STRONG_CHF_COUNT_GE || chf_minus_aff>=params::STRICT_RW_BASE_STRONG_CHF_MARGIN_GE);
    const bool aff_low=params::STRICT_RW_BASE_AFF_LOW_ENABLE!=0 && base_chf &&
        sum_abnormal<=params::STRICT_RW_BASE_AFF_LOW_ABN_LE && sum_morphology<=params::STRICT_RW_BASE_AFF_LOW_MORPH_LE &&
        sum_rbbb_like<=params::STRICT_RW_BASE_AFF_LOW_RBBB_LE && rdm_code_ge_aff_low && pred_count[1]>=params::STRICT_RW_BASE_AFF_LOW_CHF_COUNT_GE;
    const bool nsr_from_chf=base_chf && pred_count[0]>=params::STRICT_RW_BASE_NSR_FROM_CHF_NSR_COUNT_GE &&
        sum_abnormal<=params::STRICT_RW_BASE_NSR_FROM_CHF_ABN_LE && sum_qrs_maf<=params::STRICT_RW_BASE_NSR_FROM_CHF_QRS_LE &&
        sum_rbbb_like<=params::STRICT_RW_BASE_NSR_FROM_CHF_RBBB_LE && sum_morphology<=params::STRICT_RW_BASE_NSR_FROM_CHF_MORPH_LE;
    const bool chf_from_aff=base_aff && pred_count[1]>=params::STRICT_RW_BASE_CHF_FROM_AFF_CHF_COUNT_GE &&
        sum_morphology<=params::STRICT_RW_BASE_CHF_FROM_AFF_MORPH_LE && sum_qrs_maf<=params::STRICT_RW_BASE_CHF_FROM_AFF_QRS_LE &&
        sum_rbbb_like<=params::STRICT_RW_BASE_CHF_FROM_AFF_RBBB_LE;
    const bool aff=pred_count[2]<params::STRICT_RW_BASE_AFF_BLOCK_ARR_COUNT_GE && (base_chf||base_arr) && !strong_chf &&
        pred_count[3]>=params::STRICT_RW_BASE_AFF_COUNT_GE && chf_minus_aff<=params::STRICT_RW_BASE_AFF_CHF_MARGIN_LE &&
        sum_rhythm>=params::STRICT_RW_BASE_AFF_RHYTHM_GE && ge_u32(sum_ectopic_pair,params::STRICT_RW_BASE_AFF_ECP_GE) &&
        sum_ectopic_pair<=params::STRICT_RW_BASE_AFF_ECP_LE;
    const bool arr=!base_arr && !strong_nsr && pred_count[2]>=params::STRICT_RW_BASE_ARR_COUNT_GE &&
        pred_count[3]<=params::STRICT_RW_BASE_ARR_AFF_COUNT_LE && nsr_minus_arr<=params::STRICT_RW_BASE_ARR_NSR_MARGIN_LE &&
        sum_morphology>=params::STRICT_RW_BASE_ARR_MORPH_GE && sum_qrs_maf>=params::STRICT_RW_BASE_ARR_QRS_GE &&
        sum_rbbb_like>=params::STRICT_RW_BASE_ARR_RBBB_GE && sum_pre_qrs>=params::STRICT_RW_BASE_ARR_PRE_GE;
    const bool aff_rescue_source=(params::STRICT_RW_BASE_AFF_RESCUE_SOURCE_CHF!=0&&base_chf)||(params::STRICT_RW_BASE_AFF_RESCUE_SOURCE_ARR!=0&&base_arr);
    const bool aff_rescue=params::STRICT_RW_BASE_AFF_RESCUE_ENABLE!=0 && aff_rescue_source &&
        lt_u8(pred_count[2],params::STRICT_RW_BASE_AFF_RESCUE_ARR_COUNT_LT) && pred_count[3]>=params::STRICT_RW_BASE_AFF_RESCUE_COUNT_GE &&
        chf_minus_aff<=params::STRICT_RW_BASE_AFF_RESCUE_CHF_MARGIN_LE && sum_rhythm>=params::STRICT_RW_BASE_AFF_RESCUE_RHYTHM_GE &&
        sum_ectopic_pair>=params::STRICT_RW_BASE_AFF_RESCUE_ECT_GE;
    const bool arr_low=params::STRICT_RW_BASE_ARR_LOW_ENABLE!=0 && !base_arr && pred_count[2]>=params::STRICT_RW_BASE_ARR_LOW_COUNT_GE &&
        pred_count[3]<=params::STRICT_RW_BASE_ARR_LOW_AFF_COUNT_LE && sum_pre_qrs>=params::STRICT_RW_BASE_ARR_LOW_PRE_GE &&
        sum_qrs_maf>=params::STRICT_RW_BASE_ARR_LOW_QRS_GE && ge_u32(sum_rbbb_like,params::STRICT_RW_BASE_ARR_LOW_RBBB_GE) &&
        sum_morphology>=params::STRICT_RW_BASE_ARR_LOW_MORPH_GE && ge_u32(sum_abnormal,params::STRICT_RW_BASE_ARR_LOW_ABN_GE);

    std::array<std::int32_t,4> base={{pred_count[0],pred_count[1],pred_count[2],pred_count[3]}};
    if(nsr_from_chf){base[0]=add32(base[0],params::STRICT_RW_BASE_NSR_FROM_CHF_BOOST);base[1]=add32(base[1],-params::STRICT_RW_BASE_NSR_FROM_CHF_INHIBIT_CHF);}
    if(arr){base[0]=add32(base[0],-params::STRICT_RW_BASE_ARR_INHIBIT_NSR);base[1]=add32(base[1],-params::STRICT_RW_BASE_ARR_INHIBIT_CHF);base[2]=add32(base[2],params::STRICT_RW_BASE_ARR_BOOST);base[3]=add32(base[3],-params::STRICT_RW_BASE_ARR_INHIBIT_AFF);}
    if(arr_low){base[0]=add32(base[0],-params::STRICT_RW_BASE_ARR_LOW_INHIBIT_NSR);base[1]=add32(base[1],-params::STRICT_RW_BASE_ARR_LOW_INHIBIT_CHF);base[2]=add32(base[2],params::STRICT_RW_BASE_ARR_LOW_BOOST);base[3]=add32(base[3],-params::STRICT_RW_BASE_ARR_LOW_INHIBIT_AFF);}
    if(aff_low){base[1]=add32(base[1],-params::STRICT_RW_BASE_AFF_LOW_INHIBIT_CHF);base[3]=add32(base[3],params::STRICT_RW_BASE_AFF_LOW_BOOST);}
    if(chf_from_aff){base[1]=add32(base[1],params::STRICT_RW_BASE_CHF_FROM_AFF_BOOST);base[3]=add32(base[3],-params::STRICT_RW_BASE_CHF_FROM_AFF_INHIBIT_AFF);}
    if(aff){base[1]=add32(base[1],-params::STRICT_RW_BASE_AFF_INHIBIT_CHF);base[2]=add32(base[2],-params::STRICT_RW_BASE_AFF_INHIBIT_ARR);base[3]=add32(base[3],params::STRICT_RW_BASE_AFF_BOOST);}
    if(aff_rescue){base[1]=add32(base[1],-params::STRICT_RW_BASE_AFF_RESCUE_INHIBIT_CHF);base[2]=add32(base[2],-params::STRICT_RW_BASE_AFF_RESCUE_INHIBIT_ARR);base[3]=add32(base[3],params::STRICT_RW_BASE_AFF_RESCUE_BOOST);}

    const bool struct_aff=pred_count[3]>=params::STRICT_RW_FINAL_AFF_CNT && pred_count[1]>=params::STRICT_RW_FINAL_AFF_CHF_CNT &&
        sum_morphology<=params::STRICT_RW_FINAL_AFF_MORPH_LE && sum_rhythm>=params::STRICT_RW_FINAL_AFF_RHYTHM_GE && sum_qrs_maf<=params::STRICT_RW_FINAL_AFF_QRS_LE;
    const bool struct_nsr=pred_count[0]>=params::STRICT_RW_FINAL_NSR_CNT && pred_count[1]>=params::STRICT_RW_FINAL_NSR_CHF_CNT &&
        sum_morphology<=params::STRICT_RW_FINAL_NSR_MORPH_LE && sum_abnormal<=params::STRICT_RW_FINAL_NSR_ABN_LE &&
        sum_qrs_maf<=params::STRICT_RW_FINAL_NSR_QRS_LE && sum_ectopic_pair<=params::STRICT_RW_FINAL_NSR_ECT_LE;
    const bool arr_nsr_high=pred_count[2]>=params::STRICT_RW_FINAL_ARR_NSR_ARR_CNT && sum_qrs_maf<=params::STRICT_RW_FINAL_ARR_NSR_QRS_HIGH_LE && sum_rbbb_like<=params::STRICT_RW_FINAL_ARR_NSR_RBBB_HIGH_LE;
    const bool arr_nsr_low=pred_count[2]<=params::STRICT_RW_FINAL_ARR_NSR_ARR_LOW_LE && sum_qrs_maf<=params::STRICT_RW_FINAL_ARR_NSR_QRS_LOW_LE && sum_ectopic_pair<=params::STRICT_RW_FINAL_ARR_NSR_ECT_LOW_LE && sum_rhythm<=params::STRICT_RW_FINAL_ARR_NSR_RHYTHM_LOW_LE;
    const bool struct_arr_nsr=pred_count[0]>=params::STRICT_RW_FINAL_ARR_NSR_NSR_CNT && sum_morphology>=params::STRICT_RW_FINAL_ARR_NSR_MORPH_GE && sum_pre_qrs>=params::STRICT_RW_FINAL_ARR_NSR_PRE_GE && (arr_nsr_high||arr_nsr_low);
    const bool struct_arr_aff=pred_count[3]>=params::STRICT_RW_FINAL_ARR_AFF_AFF_CNT && pred_count[2]>=params::STRICT_RW_FINAL_ARR_AFF_ARR_CNT && sum_morphology>=params::STRICT_RW_FINAL_ARR_AFF_MORPH_GE && sum_ectopic_pair>=params::STRICT_RW_FINAL_ARR_AFF_ECT_GE && sum_qrs_maf<=params::STRICT_RW_FINAL_ARR_AFF_QRS_LE;
    const bool silent_aff=pred_count[1]>=params::STRICT_RW_SILENT_AFF_CHF_CNT_GE && pred_count[0]<=params::STRICT_RW_SILENT_AFF_NSR_CNT_LE &&
        pred_count[2]==params::STRICT_RW_SILENT_AFF_ARR_CNT_EQ && pred_count[3]==params::STRICT_RW_SILENT_AFF_AFF_CNT_EQ &&
        sum_beat<=params::STRICT_RW_SILENT_AFF_BEAT_LE && sum_morphology<=params::STRICT_RW_SILENT_AFF_MORPH_LE &&
        sum_rhythm<=params::STRICT_RW_SILENT_AFF_RHYTHM_LE && sum_abnormal<=params::STRICT_RW_SILENT_AFF_ABN_LE &&
        sum_qrs_maf<=params::STRICT_RW_SILENT_AFF_QRS_LE && sum_ectopic_pair==params::STRICT_RW_SILENT_AFF_ECT_EQ && sum_ram_code==params::STRICT_RW_SILENT_AFF_RAM_EQ;
    auto out=base;
    if(struct_nsr){out[0]=add32(out[0],params::STRICT_RW_FINAL_NSR_BOOST);out[1]=add32(out[1],-params::STRICT_RW_FINAL_NSR_INH_CHF);out[2]=add32(out[2],-params::STRICT_RW_FINAL_NSR_INH_ARR);}
    if(struct_aff){out[1]=add32(out[1],-params::STRICT_RW_FINAL_AFF_INH_CHF);out[2]=add32(out[2],-params::STRICT_RW_FINAL_AFF_INH_ARR);out[3]=add32(out[3],params::STRICT_RW_FINAL_AFF_BOOST);}
    if(struct_arr_nsr){out[0]=add32(out[0],-params::STRICT_RW_FINAL_ARR_NSR_INH_NSR);out[1]=add32(out[1],-params::STRICT_RW_FINAL_ARR_NSR_INH_CHF);out[2]=add32(out[2],params::STRICT_RW_FINAL_ARR_NSR_BOOST);out[3]=add32(out[3],-params::STRICT_RW_FINAL_ARR_NSR_INH_AFF);}
    if(struct_arr_aff){out[2]=add32(out[2],params::STRICT_RW_FINAL_ARR_AFF_BOOST);out[3]=add32(out[3],-params::STRICT_RW_FINAL_ARR_AFF_INH_AFF);}
    if(silent_aff){out[1]=add32(out[1],-params::STRICT_RW_SILENT_AFF_INH_CHF);out[3]=add32(out[3],params::STRICT_RW_SILENT_AFF_BOOST);}
    return out;
}

FinalResult FinalMembrane::commit(const SnapshotTrace& s, bool chunk_done,
                                  std::uint64_t accepted,
                                  std::uint32_t snapshots) noexcept {
    pred_count[s.snapshot_pred]=static_cast<std::uint8_t>(fw::wrap_add<6>(pred_count[s.snapshot_pred],1));
#define SUM(field,value) field=static_cast<std::uint32_t>(fw::wrap_add<32>(field,value))
    SUM(sum_beat,s.beat_count); SUM(sum_pnn_mismatch,s.pnn_mismatch_count);
    SUM(sum_ectopic_pair,s.ectopic_pair_count); SUM(sum_qrs_maf,s.qrs_maf_count);
    SUM(sum_rbbb_like,s.rbbb_delay_like_count); SUM(sum_pre_qrs,s.pre_qrs_bump_count);
    SUM(sum_abnormal,s.abnormal_evidence_count); SUM(sum_rhythm,s.rhythm_irregular_evidence_count);
    SUM(sum_morphology,s.morphology_evidence_count); SUM(sum_rdm_valid,s.rdm_valid_count);
    SUM(sum_rdm_code,s.rdm_code_sum); SUM(sum_ram_code,s.ram_code_sum);
#undef SUM
    FinalResult result; result.accepted_samples=accepted; result.snapshot_count=snapshots;
    result.final_mem=current_membrane(); result.final_pred=argmax_mem(result.final_mem);
    result.valid=chunk_done; result.decision_count=chunk_done?1U:0U;
    return result;
}

}  // namespace snn
