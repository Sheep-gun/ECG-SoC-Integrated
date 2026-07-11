#include "model_types.hpp"

#include <cstdlib>
#include <iostream>

namespace {
int failures = 0;
void check(bool ok, const char* name) {
    if (!ok) { ++failures; std::cerr << "FAIL " << name << '\n'; }
}
}

int main() {
    snn::EcgEventEncoderAdaptive event;
    event.tick(true, false, 0);
    event.tick(true, false, 5);
    check(!event.strong_event, "event threshold equal is quiet");
    event.tick(true, false, 11);
    check(event.strong_event && event.up_event, "event threshold plus one");
    event.tick(true, false, 6);
    check(!event.strong_event && event.down_event, "negative slope at event threshold");

    snn::QrsLifDetector qrs;
    qrs.tick(true, true);
    check(qrs.qrs_mem == 8 && !qrs.beat_spike, "qrs first integration");
    qrs.tick(true, true);
    check(qrs.beat_spike && qrs.refractory_cnt == 280, "qrs threshold crossing");
    qrs.tick(true, true);
    check(!qrs.beat_spike && qrs.qrs_mem == 0 && qrs.refractory_cnt == 279,
          "qrs refractory suppresses event");

    snn::PnnRhythmPredictor pnn;
    pnn.tick(false, true, true);
    for (int i = 0; i < 300; ++i) pnn.tick(false, true, false);
    pnn.tick(false, true, true);
    check(pnn.evaluating && pnn.rr_interval == 301, "pnn captures old-state age");
    for (int i = 0; i < 46; ++i) pnn.tick(false, false, false);
    check(pnn.evaluating && !pnn.predictor_valid, "pnn scan holds on idle");
    for (int i = 0; i < 46; ++i) pnn.tick(false, true, false);
    check(!pnn.evaluating && pnn.predictor_valid, "pnn scan advances on rhythm tick");

    snn::RdmVariabilityNeuron rdm;
    rdm.tick(false, true, 500);
    check(!rdm.rr_diff_valid_spike, "rdm first RR primes state");
    rdm.tick(false, true, 650);
    check(rdm.rr_diff_valid_spike && rdm.rdm_level_code == 15 &&
          rdm.rdm_level_spike == 0x7fff, "rdm threshold equality ladder");

    snn::EctopicPairNeuron ect;
    ect.tick(false, true, 500);
    ect.tick(false, true, 300);
    check(ect.early_rr_spike && !ect.ectopic_pair_spike, "ectopic early");
    ect.tick(false, true, 800);
    check(ect.late_rr_spike && ect.ectopic_pair_spike, "ectopic alternating pair");

    snn::DscrSpikeCounter dscr;
    dscr.tick(false, true, 0);
    dscr.tick(false, true, 2047);
    check(dscr.valid_slope_spike && !dscr.sign_flip_spike, "dscr positive slope");
    dscr.tick(false, true, -2048);
    check(dscr.valid_slope_spike && dscr.sign_flip_spike, "dscr sign flip");

    snn::RamPeakAccumulator ram;
    ram.tick(false, true, true, false, 1024);
    ram.tick(false, true, true, true, 2047);
    for (int i = 0; i < 79; ++i) ram.tick(false, true, false, false, 0);
    check(!ram.ram_amp_spike, "ram post hold before expiry");
    ram.tick(false, true, false, false, 0);
    check(ram.ram_amp_spike && ram.ram_amp_code == 32, "ram post hold emission");

    snn::QrsMafNeuron maf;
    for (int i = 0; i < 5; ++i) maf.tick(false, true, 512, true, i == 2, false);
    maf.tick(false, true, 512, true, false, true);
    for (int i = 0; i < 99; ++i) maf.tick(false, true, 0, false, false, false);
    check(maf.qrs_maf_valid_spike && maf.pre_qrs_bump_spike,
          "qrs maf final sample and pre-beat evidence");

    snn::RbbbQrsDelayBank rbbb;
    rbbb.tick(false, true, false, false, false, 5, false, false, false, 0, 0);
    check(rbbb.qrs_onset_spike, "rbbb onset threshold equality");
    for (int i = 0; i < 160; ++i)
        rbbb.tick(false, true, false, false, false, 5, false, false, false, 0, 0);
    for (int i = 0; i < 15; ++i)
        rbbb.tick(false, true, false, false, false, 0, false, false, false, 0, 0);
    check(rbbb.qrs_valid_spike && rbbb.wide_qrs_spike && rbbb.terminal_delay_spike &&
          rbbb.rbbb_like_beat_spike, "rbbb gap termination and evidence");

    if (failures != 0) return EXIT_FAILURE;
    std::cout << "feature_blocks: pass\n";
    return EXIT_SUCCESS;
}
