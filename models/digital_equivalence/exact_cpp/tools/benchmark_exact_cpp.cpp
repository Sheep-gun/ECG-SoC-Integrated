#include "exact_model.hpp"

#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0601
#endif
#ifndef WINVER
#define WINVER 0x0601
#endif
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <powrprof.h>
#include <tlhelp32.h>
#include <cpuid.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr std::size_t kSamples=1800000;
constexpr int kWarmups=3,kRepetitions=10;
struct Case {std::string id,label,path;std::uint8_t pred=0;std::array<std::int32_t,4> mem{{0,0,0,0}};std::vector<std::int16_t> samples;};
struct Result {std::uint8_t pred=0;std::array<std::int32_t,4> mem{{0,0,0,0}};std::uint64_t accepted=0;std::uint32_t snapshots=0,decisions=0;};
struct Power {bool valid=false;ULONG max_mhz=0,current_mhz=0,mhz_limit=0;};
struct Measurement {double ns=0;std::uint64_t cycles=0;bool cycles_valid=false;Power before,after;Result result;};
struct ProcessorPowerEntry {ULONG number,max_mhz,current_mhz,mhz_limit,max_idle_state,current_idle_state;};

std::string trim(std::string v){const auto f=std::find_if_not(v.begin(),v.end(),[](unsigned char c){return std::isspace(c)!=0;});const auto l=std::find_if_not(v.rbegin(),v.rend(),[](unsigned char c){return std::isspace(c)!=0;}).base();return f>=l?std::string{}:std::string(f,l);}
std::vector<std::string> split(const std::string& line){std::vector<std::string> out;std::string x;bool q=false;for(char c:line){if(c=='"')q=!q;else if(c==','&&!q){out.push_back(x);x.clear();}else x.push_back(c);}out.push_back(x);return out;}
std::string path_join(std::string root,std::string rel){std::replace(rel.begin(),rel.end(),'/', '\\');if(!root.empty()&&root.back()!='\\'&&root.back()!='/')root.push_back('\\');return root+rel;}

std::vector<Case> load_cases(const std::string& csv,const std::string& root){std::ifstream in(csv,std::ios::binary);if(!in)throw std::runtime_error("cannot open cases");std::string line;if(!std::getline(in,line))throw std::runtime_error("empty cases");const auto h=split(trim(line));std::map<std::string,std::size_t> c;for(std::size_t i=0;i<h.size();++i)c[h[i]]=i;std::vector<Case> out;while(std::getline(in,line)){if(trim(line).empty())continue;const auto f=split(trim(line));Case x;x.id=f[c["case_id"]];x.label=f[c["class_label"]];x.path=path_join(root,f[c["mem_path"]]);x.pred=static_cast<std::uint8_t>(std::stoul(f[c["expected_final_pred"]]));x.mem={{static_cast<std::int32_t>(std::stol(f[c["expected_final_mem_NSR"]])),static_cast<std::int32_t>(std::stol(f[c["expected_final_mem_CHF"]])),static_cast<std::int32_t>(std::stol(f[c["expected_final_mem_ARR"]])),static_cast<std::int32_t>(std::stol(f[c["expected_final_mem_AFF"]]))}};out.push_back(std::move(x));}if(out.size()!=36)throw std::runtime_error("expected 36 cases");return out;}

std::int16_t sample(std::string line,std::uint64_t n){const auto h=line.find('#');if(h!=std::string::npos)line.erase(h);const auto s=line.find("//");if(s!=std::string::npos)line.erase(s);line=trim(line);if(line.empty())return 4096;if(line.size()!=3)throw std::runtime_error("invalid width line "+std::to_string(n));std::size_t used=0;long v=0;try{v=std::stol(line,&used,16);}catch(...){throw std::runtime_error("invalid hex line "+std::to_string(n));}if(used!=3||v<0||v>0xfff)throw std::runtime_error("invalid sample");if(v>=0x800)v-=0x1000;return static_cast<std::int16_t>(v);}
std::vector<std::int16_t> parse_file(const std::string& path){std::ifstream in(path,std::ios::binary);if(!in)throw std::runtime_error("cannot open "+path);std::vector<std::int16_t> out;out.reserve(kSamples);std::string line;std::uint64_t n=0;while(std::getline(in,line)){const auto v=sample(line,++n);if(v==4096)continue;if(out.size()>=kSamples)throw std::runtime_error("too many samples");out.push_back(v);}if(out.size()!=kSamples)throw std::runtime_error("sample count");return out;}

Result kernel(const std::vector<std::int16_t>& samples){snn::ExactModel model;model.reset();for(auto v:samples)model.process_sample(v);const auto& r=model.get_final_result();return {r.final_pred,r.final_mem,r.accepted_samples,r.snapshot_count,r.decision_count};}
void write_json(const std::string& path,const Result& r){std::ofstream o(path,std::ios::binary|std::ios::trunc);if(!o)throw std::runtime_error("cannot write output");o<<"{\n  \"final_pred\": "<<static_cast<unsigned>(r.pred)<<",\n  \"final_mem_NSR\": "<<r.mem[0]<<",\n  \"final_mem_CHF\": "<<r.mem[1]<<",\n  \"final_mem_ARR\": "<<r.mem[2]<<",\n  \"final_mem_AFF\": "<<r.mem[3]<<",\n  \"accepted_samples\": "<<r.accepted<<",\n  \"snapshot_count\": "<<r.snapshots<<",\n  \"decision_count\": "<<r.decisions<<"\n}\n";o.flush();if(!o)throw std::runtime_error("output write");}
Result end_to_end(const Case& c,const std::string& output){auto samples=parse_file(c.path);auto r=kernel(samples);write_json(output,r);return r;}
bool exact(const Case& c,const Result& r){return r.pred==c.pred&&r.mem==c.mem&&r.accepted==kSamples&&r.snapshots==30&&r.decisions==1;}

std::uint32_t logical_count(){SYSTEM_INFO info{};GetSystemInfo(&info);return info.dwNumberOfProcessors;}
std::uint32_t physical_count(){unsigned eax=0,ebx=0,ecx=0,edx=0;if(__get_cpuid(0x80000008U,&eax,&ebx,&ecx,&edx)==0)return 0;return (ecx&0xffU)+1U;}
std::uint32_t thread_count(){const DWORD pid=GetCurrentProcessId();HANDLE h=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);if(h==INVALID_HANDLE_VALUE)return 0;THREADENTRY32 e{};e.dwSize=sizeof(e);std::uint32_t n=0;if(Thread32First(h,&e))do{if(e.th32OwnerProcessID==pid)++n;}while(Thread32Next(h,&e));CloseHandle(h);return n;}
Power power(std::uint32_t cpu){const auto n=logical_count();std::vector<ProcessorPowerEntry> p(n);if(CallNtPowerInformation(ProcessorInformation,nullptr,0,p.data(),static_cast<ULONG>(p.size()*sizeof(p[0])))!=0||cpu>=p.size())return {};return {true,p[cpu].max_mhz,p[cpu].current_mhz,p[cpu].mhz_limit};}
using QueryThreadCycleTimeFn=BOOL (WINAPI*)(HANDLE,PULONG64);
QueryThreadCycleTimeFn cycle_fn(){static const auto fn=reinterpret_cast<QueryThreadCycleTimeFn>(GetProcAddress(GetModuleHandleA("kernel32.dll"),"QueryThreadCycleTime"));return fn;}
BOOL query_cycles(ULONG64* value){const auto fn=cycle_fn();return fn?fn(GetCurrentThread(),value):FALSE;}
template<class F>Measurement measure(F&& f,std::uint32_t cpu){LARGE_INTEGER hz{},a{},b{};QueryPerformanceFrequency(&hz);ULONG64 ca=0,cb=0;Measurement m;m.before=power(cpu);const BOOL oka=query_cycles(&ca);QueryPerformanceCounter(&a);m.result=f();QueryPerformanceCounter(&b);const BOOL okb=query_cycles(&cb);m.after=power(cpu);m.ns=static_cast<double>(b.QuadPart-a.QuadPart)*1e9/static_cast<double>(hz.QuadPart);m.cycles_valid=oka&&okb&&cb>=ca;m.cycles=m.cycles_valid?static_cast<std::uint64_t>(cb-ca):0;return m;}

void row(std::ofstream& o,const Case& c,const char* mode,int rep,const Measurement& m,std::uint32_t cpu,std::uint64_t mask){const double ms=m.ns/1e6,sps=static_cast<double>(kSamples)*1e9/m.ns,cps=m.cycles_valid?static_cast<double>(m.cycles)/kSamples:0,effective=m.cycles_valid?static_cast<double>(m.cycles)/(m.ns/1e3):0;o<<c.id<<','<<c.label<<','<<mode<<','<<rep<<','<<kWarmups<<','<<kRepetitions<<",0,"<<cpu<<",0x"<<std::hex<<mask<<std::dec<<",0,1,"<<kSamples<<','<<std::fixed<<std::setprecision(3)<<m.ns<<','<<std::setprecision(9)<<ms<<','<<m.cycles<<','<<std::setprecision(6)<<cps<<','<<std::setprecision(3)<<sps<<','<<effective<<','<<(m.before.valid?std::to_string(m.before.current_mhz):"")<<','<<(m.after.valid?std::to_string(m.after.current_mhz):"")<<','<<(m.before.valid?std::to_string(m.before.max_mhz):"")<<','<<(m.before.valid?std::to_string(m.before.mhz_limit):"")<<','<<static_cast<unsigned>(m.result.pred)<<','<<m.result.mem[0]<<','<<m.result.mem[1]<<','<<m.result.mem[2]<<','<<m.result.mem[3]<<','<<m.result.accepted<<','<<m.result.snapshots<<','<<m.result.decisions<<','<<(exact(c,m.result)?1:0)<<'\n';}

void environment(const std::string& path,std::uint32_t cpu,std::uint64_t mask,DWORD_PTR previous){LARGE_INTEGER hz{};QueryPerformanceFrequency(&hz);const auto p=power(cpu);std::ofstream o(path,std::ios::binary|std::ios::trunc);if(!o)throw std::runtime_error("environment output");o<<"{\n  \"physical_cores\": "<<physical_count()<<",\n  \"logical_processors\": "<<logical_count()<<",\n  \"process_threads_observed\": "<<thread_count()<<",\n  \"processor_group\": 0,\n  \"affinity_cpu\": "<<cpu<<",\n  \"affinity_mask\": \"0x"<<std::hex<<mask<<std::dec<<"\",\n  \"previous_thread_affinity_mask\": \"0x"<<std::hex<<static_cast<std::uint64_t>(previous)<<std::dec<<"\",\n  \"qpc_frequency_hz\": "<<hz.QuadPart<<",\n  \"query_thread_cycle_time_available\": "<<(cycle_fn()?"true":"false")<<",\n  \"processor_power_information_available\": "<<(p.valid?"true":"false")<<",\n  \"reported_max_mhz\": "<<p.max_mhz<<",\n  \"reported_current_mhz_before_benchmark\": "<<p.current_mhz<<",\n  \"reported_mhz_limit\": "<<p.mhz_limit<<",\n  \"warmups_per_case_per_mode\": 3,\n  \"measured_repetitions_per_case_per_mode\": 10,\n  \"trace_enabled\": false,\n  \"assertions_enabled\": false,\n  \"march_native_enabled\": true,\n  \"single_process\": true,\n  \"single_thread_algorithm\": true\n}\n";}

struct Args{std::string cases,root,raw,env,out;std::uint32_t cpu=2;};
Args parse(int argc,char**argv){
    Args a;
    for(int i=1;i<argc;++i){
        if(i+1>=argc){throw std::invalid_argument("missing value");}
        std::string k=argv[i],v=argv[++i];
        if(k=="--cases")a.cases=v;
        else if(k=="--data-root")a.root=v;
        else if(k=="--raw")a.raw=v;
        else if(k=="--environment")a.env=v;
        else if(k=="--e2e-output")a.out=v;
        else if(k=="--affinity-cpu")a.cpu=static_cast<std::uint32_t>(std::stoul(v));
        else throw std::invalid_argument("unknown option");
    }
    if(a.cases.empty()||a.root.empty()||a.raw.empty()||a.env.empty()||a.out.empty()){
        throw std::invalid_argument("required option");
    }
    return a;
}
}

int main(int argc,char**argv)try{const auto a=parse(argc,argv);if(a.cpu>=logical_count()||a.cpu>=64)throw std::runtime_error("affinity CPU");const std::uint64_t mask=std::uint64_t{1}<<a.cpu;if(!SetProcessAffinityMask(GetCurrentProcess(),static_cast<DWORD_PTR>(mask)))throw std::runtime_error("process affinity");const DWORD_PTR previous=SetThreadAffinityMask(GetCurrentThread(),static_cast<DWORD_PTR>(mask));if(!previous)throw std::runtime_error("thread affinity");auto cases=load_cases(a.cases,a.root);for(auto&c:cases)c.samples=parse_file(c.path);for(const auto&c:cases)if(!exact(c,kernel(c.samples)))throw std::runtime_error("pre-timing mismatch "+c.id);environment(a.env,a.cpu,mask,previous);std::ofstream raw(a.raw,std::ios::binary|std::ios::trunc);if(!raw)throw std::runtime_error("raw output");raw<<"case_id,class_label,mode,repetition,warmups,measured_repetitions,affinity_group,affinity_cpu,affinity_mask,trace_enabled,march_native_enabled,samples,latency_ns,latency_ms,thread_cycles,cycles_per_sample,samples_per_s,effective_clock_mhz,current_mhz_before,current_mhz_after,max_mhz,mhz_limit,final_pred,final_mem_NSR,final_mem_CHF,final_mem_ARR,final_mem_AFF,accepted_samples,snapshots,decisions,output_exact\n";for(const auto&c:cases){for(int i=0;i<kWarmups;++i)if(!exact(c,kernel(c.samples)))throw std::runtime_error("kernel warmup");for(int i=0;i<kRepetitions;++i){const auto m=measure([&](){return kernel(c.samples);},a.cpu);if(!exact(c,m.result))throw std::runtime_error("kernel mismatch");row(raw,c,"kernel",i+1,m,a.cpu,mask);}for(int i=0;i<kWarmups;++i)if(!exact(c,end_to_end(c,a.out)))throw std::runtime_error("e2e warmup");for(int i=0;i<kRepetitions;++i){const auto m=measure([&](){return end_to_end(c,a.out);},a.cpu);if(!exact(c,m.result))throw std::runtime_error("e2e mismatch");row(raw,c,"end_to_end",i+1,m,a.cpu,mask);}raw.flush();if(!raw)throw std::runtime_error("raw write");}std::cout<<"benchmark_complete cases=36 modes=2 repetitions=10 affinity_cpu="<<a.cpu<<"\n";return 0;}catch(const std::exception&e){std::cerr<<"exact_cpp_benchmark: "<<e.what()<<'\n';return 2;}
