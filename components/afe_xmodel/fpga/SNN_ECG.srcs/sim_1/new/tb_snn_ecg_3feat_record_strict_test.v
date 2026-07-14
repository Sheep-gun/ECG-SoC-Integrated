`timescale 1ns / 1ps

module tb_snn_ecg_3feat_record_strict_test;
    tb_snn_ecg_3feat_dataset #(
        .MAX_SAMPLES(180000),
        .MANIFEST_FILE("<LOCAL_DIGITAL_REPOSITORY>/person_data_record_split_strict_varlen/test/dataset_manifest_test_varlen.txt"),
        .WRITE_CASE_CSV(1),
        .RESULT_CSV("<LOCAL_DIGITAL_REPOSITORY>/results/test/rtl_test_varlen_case_results.csv"),
        .WRITE_SUBWINDOW_CSV(0),
        .SUBWINDOW_CSV("<LOCAL_DIGITAL_REPOSITORY>/results/test/rtl_test_varlen_subwindow_features.csv"),
        .MANIFEST_HAS_SAMPLE_COUNT(1)
    ) u_tb();
endmodule
