#include "Vsnn_ecg_30min_final_top.h"
#include "verilated.h"

#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

double sc_time_stamp() {
    return 0.0;
}

namespace {

using Clock = std::chrono::steady_clock;

struct Result {
    uint32_t final_pred;
    int32_t mem_nsr;
    int32_t mem_chf;
    int32_t mem_arr;
    int32_t mem_aff;
    uint64_t total_cycles;
    uint64_t run_cycles;
    uint64_t input_wait_cycles;
    uint64_t accepted_samples;
    uint64_t windows;
    uint64_t decisions;
};

std::vector<int16_t> load_mem(const std::string& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        throw std::runtime_error("cannot open input: " + path);
    }
    std::vector<int16_t> samples;
    samples.reserve(1800000);
    std::string line;
    while (std::getline(input, line)) {
        if (line.size() < 3) {
            continue;
        }
        unsigned value = static_cast<unsigned>(std::stoul(line.substr(0, 3), nullptr, 16));
        samples.push_back(static_cast<int16_t>(value >= 0x800U ? static_cast<int>(value) - 0x1000 : value));
    }
    if (samples.size() != 1800000U) {
        throw std::runtime_error("expected 1800000 samples, got " + std::to_string(samples.size()));
    }
    return samples;
}

void cycle(Vsnn_ecg_30min_final_top& top) {
    top.clk = 0;
    top.eval();
    top.clk = 1;
    top.eval();
}

Result infer(const std::vector<int16_t>& samples) {
    VerilatedContext context;
    context.traceEverOn(false);
    Vsnn_ecg_30min_final_top top(&context);
    top.clk = 0;
    top.rst = 1;
    top.start = 0;
    top.sample_valid = 0;
    top.adc_data = 0;
    for (int i = 0; i < 5; ++i) {
        cycle(top);
    }
    top.rst = 0;
    cycle(top);
    top.start = 1;
    cycle(top);
    top.start = 0;

    size_t index = 0;
    unsigned gap_count = 0;
    constexpr uint64_t timeout = 8000000ULL;
    uint64_t host_cycles = 0;
    bool seen_final = false;
    Result result{};

    while (host_cycles < timeout) {
        top.clk = 0;
        top.eval();
        if (top.sample_ready && gap_count == 0U && index < samples.size()) {
            top.sample_valid = 1;
            top.adc_data = static_cast<uint16_t>(samples[index]) & 0x0fffU;
            ++index;
            gap_count = 2U;
        } else {
            top.sample_valid = 0;
            top.adc_data = 0;
            if (gap_count > 0U) {
                --gap_count;
            }
        }
        top.clk = 1;
        top.eval();
        ++host_cycles;
        if (top.final_valid) {
            result.final_pred = top.final_pred_class;
            result.mem_nsr = static_cast<int32_t>(top.final_mem_nsr);
            result.mem_chf = static_cast<int32_t>(top.final_mem_chf);
            result.mem_arr = static_cast<int32_t>(top.final_mem_arr);
            result.mem_aff = static_cast<int32_t>(top.final_mem_aff);
            result.total_cycles = top.prof_total_cycle_counter;
            result.run_cycles = top.prof_run_cycle_counter;
            result.input_wait_cycles = top.prof_input_wait_cycle_counter;
            result.accepted_samples = top.prof_accepted_sample_counter;
            result.windows = top.prof_window_counter;
            result.decisions = top.prof_decision_counter;
            seen_final = true;
            break;
        }
    }
    top.final();
    if (!seen_final) {
        throw std::runtime_error("simulation timeout after " + std::to_string(host_cycles) + " cycles");
    }
    if (index != samples.size()) {
        throw std::runtime_error("final result before all samples accepted");
    }
    return result;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2 || argc > 4) {
            std::cerr << "usage: cpp_baseline INPUT.mem [WARMUP=0] [REPEATS=1]\n";
            return 2;
        }
        const int warmups = argc >= 3 ? std::stoi(argv[2]) : 0;
        const int repeats = argc >= 4 ? std::stoi(argv[3]) : 1;
        const auto samples = load_mem(argv[1]);
        for (int i = 0; i < warmups; ++i) {
            (void)infer(samples);
        }
        for (int repeat = 0; repeat < repeats; ++repeat) {
            const auto begin = Clock::now();
            const Result result = infer(samples);
            const auto end = Clock::now();
            const auto elapsed_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - begin).count();
            std::cout
                << "CPP_RESULT"
                << " repeat_id=" << repeat
                << " sample_count=" << samples.size()
                << " elapsed_ns=" << elapsed_ns
                << " final_pred=" << result.final_pred
                << " final_mem_NSR=" << result.mem_nsr
                << " final_mem_CHF=" << result.mem_chf
                << " final_mem_ARR=" << result.mem_arr
                << " final_mem_AFF=" << result.mem_aff
                << " prof_total_cycles=" << result.total_cycles
                << " prof_run_cycles=" << result.run_cycles
                << " prof_input_wait_cycles=" << result.input_wait_cycles
                << " accepted_samples=" << result.accepted_samples
                << " windows=" << result.windows
                << " decisions=" << result.decisions
                << "\n";
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "CPP_BASELINE_ERROR " << error.what() << "\n";
        return 1;
    }
}
