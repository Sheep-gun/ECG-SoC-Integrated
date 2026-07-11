#include "exact_model.hpp"
#include "model_types.hpp"

#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {
struct Row { std::string scenario,category,rtl_reference,expected,actual; bool pass; };
std::vector<Row> rows;
template <typename T> std::string s(T value) { std::ostringstream o; o<<value; return o.str(); }
void record(const char* scenario,const char* category,const char* rtl,const std::string& expected,const std::string& actual) {
    rows.push_back({scenario,category,rtl,expected,actual,expected==actual});
}
}

int main(int argc,char** argv) {
    snn::EcgEventEncoderAdaptive event;
    event.tick(true,false,0); event.tick(true,false,4);
    record("event_threshold_minus_one","threshold","ecg_event_encoder_adaptive:strong_event","0",s(event.strong_event));
    event.tick(true,false,9);
    record("event_threshold_equal","threshold","ecg_event_encoder_adaptive:strong_event","0",s(event.strong_event));
    event.tick(true,false,15);
    record("event_threshold_plus_one","threshold","ecg_event_encoder_adaptive:strong_event/up_event","1/1",s(event.strong_event)+"/"+s(event.up_event));
    event.tick(true,false,9);
    record("negative_slope_plus_one","signed_slope","ecg_event_encoder_adaptive:strong_event/down_event","1/1",s(event.strong_event)+"/"+s(event.down_event));

    snn::QrsLifDetector qrs; qrs.tick(true,true); qrs.tick(true,true);
    record("qrs_threshold_crossing","threshold","qrs_lif_detector:beat_spike/refractory_cnt","1/280",s(qrs.beat_spike)+"/"+s(qrs.refractory_cnt));
    qrs.refractory_cnt=1; qrs.qrs_mem=7; qrs.tick(true,true);
    record("refractory_expiry_old_state","old_new_order","qrs_lif_detector:qrs_mem/refractory_cnt/beat_spike","0/0/0",s(qrs.qrs_mem)+"/"+s(qrs.refractory_cnt)+"/"+s(qrs.beat_spike));

    snn::PnnRhythmPredictor pnn; pnn.tick(false,true,true);
    for(int i=0;i<300;++i) pnn.tick(false,true,false);
    pnn.tick(false,true,true);
    const auto held=pnn.eval_idx; for(int i=0;i<46;++i)pnn.tick(false,false,false);
    record("pnn_idle_scan_hold","cadence","pnn_rhythm_predictor:evaluating/eval_idx","1/0",s(pnn.evaluating)+"/"+s(static_cast<unsigned>(pnn.eval_idx)));
    for(int i=0;i<46;++i)pnn.tick(false,true,false);
    record("pnn_rhythm_scan_complete","cadence","pnn_rhythm_predictor:predictor_valid/evaluating","1/0",s(pnn.predictor_valid)+"/"+s(pnn.evaluating));
    (void)held;

    snn::RdmVariabilityNeuron rdm; rdm.tick(false,true,500); rdm.tick(false,true,650);
    record("rdm_threshold_ladder_equal","threshold","rdm_variability_neuron:level_code/level_spike","15/32767",s(static_cast<unsigned>(rdm.rdm_level_code))+"/"+s(rdm.rdm_level_spike));
    snn::EctopicPairNeuron ect; ect.tick(false,true,500); ect.tick(false,true,300); ect.tick(false,true,800);
    record("ectopic_early_late_pair","pair_transition","ectopic_pair_neuron:late_rr_spike/ectopic_pair_spike","1/1",s(ect.late_rr_spike)+"/"+s(ect.ectopic_pair_spike));
    snn::DscrSpikeCounter dscr; dscr.tick(false,true,0); dscr.tick(false,true,2047); dscr.tick(false,true,-2048);
    record("dscr_positive_to_negative_flip","signed_slope","dscr_spike_counter:valid_slope/sign_flip","1/1",s(dscr.valid_slope_spike)+"/"+s(dscr.sign_flip_spike));

    snn::C24ScoreNeurons score; score.reset(); score.beat_seg_count=0xffff;
    snn::ScoreInputs input; input.beat_spike=true; score.tick(false,input);
    record("segment_counter_rollover","wrap","class_score_neurons:beat_seg_count[15:0]","0",s(score.beat_seg_count));
    score.reset(); input=snn::ScoreInputs{}; input.pnn_match_spike=true; input.pnn_mismatch_spike=true; score.tick(false,input);
    record("simultaneous_pnn_events","simultaneous","class_score_neurons:pnn_match_seg/pnn_mis_seg","1/1",s(score.pnn_match_seg_count)+"/"+s(score.pnn_mis_seg_count));
    score.reset(); score.c24_readout_busy_ticks=1; const auto before=score.c24_mem;
    input=snn::ScoreInputs{}; input.rdm_valid_spike=true; score.tick(false,input);
    record("readout_busy_event_capture","flush","class_score_neurons:c24_event_group_pending","0",s(score.c24_mem!=before));

    snn::ExactModel one; one.reset(); for(int i=0;i<60000;++i)one.process_sample(0);
#if EXACT_CPP_TRACE
    record("snapshot_last_sample","boundary","snn_ecg_30min_final_top:accepted/window_count","60000/1",s(one.get_snapshot_trace().back().accepted_samples)+"/"+s(one.get_snapshot_trace().size()));
    record("snapshot_flush_visible_updates","flush","snn_ecg_30min_final_top:POST_DONE_TICKS=37 pre-NBA commit","1",s(one.get_snapshot_trace().size()==1));
#else
    record("snapshot_last_sample","boundary","snn_ecg_30min_final_top:accepted/window_count","60000/1",s(one.get_final_result().accepted_samples)+"/"+s(one.get_final_result().snapshot_count));
    record("snapshot_flush_visible_updates","flush","snn_ecg_30min_final_top:POST_DONE_TICKS=37 pre-NBA commit","1",s(one.get_final_result().snapshot_count==1));
#endif

    snn::FinalMembrane fm; fm.reset(); fm.pred_count={{0,1,1,1}}; snn::SnapshotTrace tied; tied.snapshot_pred=0;
    const auto tied_result=fm.commit(tied,true,0,30);
    record("wta_equal_first_wins","tie_break","final_membrane_layer:strict-greater WTA","0",s(static_cast<unsigned>(tied_result.final_pred)));

    snn::ExactModel full; full.reset(); for(int i=0;i<1800000;++i)full.process_sample(0);
    const auto& fr=full.get_final_result();
    record("final_snapshot_last_sample","boundary","snn_ecg_30min_final_top:final_valid","1800000/30/1",s(fr.accepted_samples)+"/"+s(fr.snapshot_count)+"/"+s(fr.decision_count));

    if(argc==3 && std::string(argv[1])=="--csv") {
        std::ofstream out(argv[2],std::ios::binary); if(!out)return 2;
        out<<"scenario,category,rtl_reference,expected,actual,exact_match\n";
        for(const auto& r:rows)out<<r.scenario<<','<<r.category<<','<<r.rtl_reference<<','<<r.expected<<','<<r.actual<<','<<(r.pass?1:0)<<'\n';
    }
    std::size_t passed=0;for(const auto& r:rows){if(r.pass)++passed;else std::cerr<<"FAIL "<<r.scenario<<" expected="<<r.expected<<" actual="<<r.actual<<'\n';}
    std::cout<<"adversarial_sequences: "<<passed<<'/'<<rows.size()<<" passed\n";
    return passed==rows.size()?EXIT_SUCCESS:EXIT_FAILURE;
}
