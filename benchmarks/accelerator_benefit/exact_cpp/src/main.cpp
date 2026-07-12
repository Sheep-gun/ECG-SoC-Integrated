#include "exact_model.hpp"
#include "locked_parameters.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

struct Args {
    std::string input;
    std::string format = "signed12_hex";
    std::string output;
    std::string trace_output;
    std::string sample_hash_output;
    std::uint64_t expected_samples = 1800000;
    bool allow_incomplete = false;
    bool stop_after_expected = false;
};

Args parse_args(int argc, char** argv) {
    Args args;
    for (int i=1;i<argc;++i) {
        const std::string key=argv[i];
        if (i+1>=argc) throw std::invalid_argument("missing value for "+key);
        const std::string value=argv[++i];
        if(key=="--input") args.input=value;
        else if(key=="--format") args.format=value;
        else if(key=="--output") args.output=value;
        else if(key=="--trace-output") args.trace_output=value;
        else if(key=="--sample-hash-output") args.sample_hash_output=value;
        else if(key=="--expected-samples") args.expected_samples=std::stoull(value);
        else if(key=="--allow-incomplete") args.allow_incomplete=(value=="1"||value=="true");
        else if(key=="--stop-after-expected") args.stop_after_expected=(value=="1"||value=="true");
        else throw std::invalid_argument("unknown option: "+key);
    }
    if(args.input.empty()||args.output.empty()) throw std::invalid_argument("--input and --output are required");
    if(args.format!="signed12_hex"&&args.format!="decimal_signed") throw std::invalid_argument("format must be signed12_hex or decimal_signed");
    return args;
}

std::string trim(std::string value) {
    const auto first=std::find_if_not(value.begin(),value.end(),[](unsigned char c){return std::isspace(c)!=0;});
    const auto last=std::find_if_not(value.rbegin(),value.rend(),[](unsigned char c){return std::isspace(c)!=0;}).base();
    return first>=last?std::string{}:std::string(first,last);
}

std::int16_t parse_sample(std::string line, const std::string& format, std::uint64_t line_no) {
    const auto hash=line.find('#'); if(hash!=std::string::npos) line.erase(hash);
    const auto slash=line.find("//"); if(slash!=std::string::npos) line.erase(slash);
    line=trim(line);
    if(line.empty()) return 4096; // sentinel outside signed-12 range for blank/comment
    std::size_t used=0;
    long value=0;
    try {
        if(format=="signed12_hex") {
            if(line.size()!=3) throw std::invalid_argument("hex sample must contain exactly three digits");
            value=std::stol(line,&used,16);
            if(used!=line.size()||value<0||value>0xfff) throw std::invalid_argument("invalid 12-bit hex");
            if(value>=0x800) value-=0x1000;
        } else {
            value=std::stol(line,&used,10);
            if(used!=line.size()||value< -2048||value>2047) throw std::invalid_argument("decimal sample outside signed 12-bit range");
        }
    } catch(const std::exception& e) {
        throw std::runtime_error("line "+std::to_string(line_no)+": "+e.what());
    }
    return static_cast<std::int16_t>(value);
}

void write_result(const std::string& path, const snn::FinalResult& r) {
    std::ofstream out(path,std::ios::binary);
    if(!out) throw std::runtime_error("cannot open output: "+path);
    out << "{\n"
        << "  \"final_pred\": " << static_cast<unsigned>(r.final_pred) << ",\n"
        << "  \"final_mem_NSR\": " << r.final_mem[0] << ",\n"
        << "  \"final_mem_CHF\": " << r.final_mem[1] << ",\n"
        << "  \"final_mem_ARR\": " << r.final_mem[2] << ",\n"
        << "  \"final_mem_AFF\": " << r.final_mem[3] << ",\n"
        << "  \"accepted_samples\": " << r.accepted_samples << ",\n"
        << "  \"snapshot_count\": " << r.snapshot_count << ",\n"
        << "  \"decision_count\": " << r.decision_count << ",\n"
        << "  \"model_id\": \"" << snn::params::model_id << "\",\n"
        << "  \"parameter_hash\": \"" << snn::params::parameter_payload_sha256 << "\",\n"
        << "  \"build_id\": \"exact_cpp_c6b80de_v1\"\n"
        << "}\n";
}

void write_trace(const std::string& path, const std::vector<snn::SnapshotTrace>& rows) {
    if(path.empty()) return;
    std::ofstream out(path,std::ios::binary);
    if(!out) throw std::runtime_error("cannot open trace output: "+path);
    out << "snapshot_index,accepted_samples,snapshot_pred,class_mem_NSR,class_mem_CHF,class_mem_ARR,class_mem_AFF,beat_count,pnn_match_count,pnn_mismatch_count,dscr_flip_count,dscr_slope_count,ram_code_sum,ram_code_count,rdm_valid_count,rdm_code_sum,ectopic_pair_count,qrs_maf_count,qrs_width_abn_count,qrs_complex_abn_count,qrs_energy_abn_count,rbbb_delay_like_count,rbbb_delay_applied_count,pre_qrs_bump_count,abnormal_evidence_count,rhythm_irregular_evidence_count,morphology_evidence_count,final_mem_NSR,final_mem_CHF,final_mem_ARR,final_mem_AFF,structural_gates,state_hash\n";
    for(const auto& r:rows) {
        out<<r.snapshot_index<<','<<r.accepted_samples<<','<<static_cast<unsigned>(r.snapshot_pred);
        for(auto v:r.snapshot_scores) out<<','<<v;
        out<<','<<r.beat_count<<','<<r.pnn_match_count<<','<<r.pnn_mismatch_count
           <<','<<r.dscr_flip_count<<','<<r.dscr_slope_count<<','<<r.ram_code_sum<<','<<r.ram_code_count
           <<','<<r.rdm_valid_count<<','<<r.rdm_code_sum<<','<<r.ectopic_pair_count<<','<<r.qrs_maf_count
           <<','<<r.qrs_width_abn_count<<','<<r.qrs_complex_abn_count<<','<<r.qrs_energy_abn_count
           <<','<<r.rbbb_delay_like_count<<','<<r.rbbb_delay_applied_count<<','<<r.pre_qrs_bump_count
           <<','<<r.abnormal_evidence_count<<','<<r.rhythm_irregular_evidence_count<<','<<r.morphology_evidence_count;
        for(auto v:r.final_mem_after) out<<','<<v;
        out<<",\""; for(std::size_t i=0;i<r.structural_gates.size();++i){if(i)out<<',';out<<static_cast<unsigned>(r.structural_gates[i]);} out<<'"';
        out<<','<<std::hex<<std::setw(16)<<std::setfill('0')<<r.state_hash<<std::dec<<'\n';
    }
}

}  // namespace

int main(int argc,char** argv) try {
    const Args args=parse_args(argc,argv);
#if !EXACT_CPP_TRACE
    if(!args.trace_output.empty()||!args.sample_hash_output.empty()||args.allow_incomplete||args.stop_after_expected)
        throw std::invalid_argument("verification trace/prefix options require EXACT_CPP_TRACE=ON");
#endif
    std::ifstream input(args.input,std::ios::binary);
    if(!input) throw std::runtime_error("cannot open input: "+args.input);
    snn::ExactModel model; model.reset();
    std::ofstream sample_hash_out;
    if(!args.sample_hash_output.empty()) {
        sample_hash_out.open(args.sample_hash_output,std::ios::binary);
        if(!sample_hash_out) throw std::runtime_error("cannot open sample hash output: "+args.sample_hash_output);
        sample_hash_out << "accepted_sample,state_hash\n";
    }
    std::string line; std::uint64_t line_no=0, samples=0;
    while(std::getline(input,line)) {
        if(args.stop_after_expected && samples==args.expected_samples) break;
        ++line_no;
        const std::int16_t sample=parse_sample(line,args.format,line_no);
        if(sample==4096) continue;
        if(samples>=args.expected_samples) throw std::runtime_error("input contains more than expected samples");
        model.process_sample(sample); ++samples;
        if(sample_hash_out) {
            sample_hash_out<<samples<<','<<std::hex<<std::setw(16)<<std::setfill('0')
                           <<model.get_last_accepted_sample_state_hash()<<std::dec<<'\n';
        }
    }
    if(samples!=args.expected_samples) throw std::runtime_error("unexpected sample count: "+std::to_string(samples));
    const auto& result=model.get_final_result();
    if(!result.valid && !args.allow_incomplete) throw std::runtime_error("input ended without a final decision");
    write_result(args.output,result); write_trace(args.trace_output,model.get_snapshot_trace());
    return 0;
} catch(const std::exception& e) {
    std::cerr<<"exact_cpp_ecg: "<<e.what()<<'\n';
    return 2;
}
