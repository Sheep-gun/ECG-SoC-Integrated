#!/usr/bin/env python3
# ARR 플립 진단: raw .mem-ARR vs AFE-ARR 출력의 기울기(delta) 통계 비교.
# 분류기 event encoder는 |delta|>8 을 strong_event로 씀 → 기울기 무뎌지면 검출 변함.
import os
BASE=os.path.join(os.path.dirname(__file__),"..")
def sgn(v): return v if v<2048 else v-4096
# raw .mem (signed)
raw=[]
for i,l in enumerate(open(os.path.join(BASE,"data","mem_ARR.mem"))):
    if i>=10000: break
    l=l.strip()
    if l: raw.append(sgn(int(l,16)))
# AFE 출력 (multiclass adc_ARR.txt, code-2048 = signed)
afe={}
p=os.path.join(BASE,"sim_out","multiclass","adc_ARR.txt")
for l in open(p):
    if l.startswith("#"): continue
    a=l.split()
    if len(a)>=2: afe[int(a[0])]=int(a[1])-2048
def stats(seq, name):
    d=[abs(seq[k+1]-seq[k]) for k in range(len(seq)-1)]
    mx=max(d); strong=sum(1 for x in d if x>8)
    print(f"{name:10} max|delta|={mx:4d}  strong(|delta|>8)={strong:5d}  샘플={len(seq)}")
# 유효구간 2000~9900
raw_v=raw[2000:9900]
afe_v=[afe[i] for i in range(2000,9900) if i in afe]
print("=== ARR 기울기(delta) 비교: 유효구간 ===")
stats(raw_v, "raw .mem")
stats(afe_v, "AFE 출력")
print("\nAFE의 max|delta|·strong 이벤트가 raw보다 작으면 → AFE 대역제한이 QRS 기울기를 무디게 함(=ARR→AFF 플립 원인)")
