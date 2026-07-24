`timescale 1ns/1ps

module tb_locked;
    tb_snn_ecg_30min_chunk_dataset #(
        .MAX_SAMPLES(1800000),
        .MANIFEST_FILE("manifest.txt"),
        .RESULT_CSV("result.csv"),
        .DUT_SNAPSHOT_SAMPLES(60000),
        .DUT_SNAPSHOTS_PER_CHUNK(30),
        .DUT_POST_DONE_TICKS(37),
        .DUT_PROFILE_EN(1),
        .DUT_SAMPLE_GAP_CYCLES(0)
    ) tb();
endmodule
