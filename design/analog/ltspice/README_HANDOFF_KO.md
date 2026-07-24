# LTspice–XMODEL 팀 handoff

이 폴더는 LTspice 담당자가 회로를 수정하고 fixed XMODEL과 10초 patient 입력의
sample-by-sample code correlation을 이어갈 수 있도록 만든 경량 package다.
원 작업공간의 약 18.5 GB raw는 포함하지 않았다.

## 기준 버전

- LTspice final candidate: `ltspice_validation/schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc`
- XMODEL commit: `4756a5086023547328ef44fd5fd87da3c250dc39`
- MATLAB intent commit: `907f7e1f081a9d6a5703a32095d962143315a192` — source 전체는 용량 절감을 위해 미포함, 기존 비교표만 포함
- Original ASC/TXT/DOCX는 package root에 있으며 수정하지 말 것

## 포함한 것

- 원본 ASC, patient input, 설계 DOCX와 SHA256
- ±1.65 V XMODEL-aligned graphical ASC/netlist
- `XOPAMP_XMODEL` model/symbol
- AC/transient/stress `.cir` — stress PWL은 generator로 재생성
- LTspice 실행·raw parsing·ADC export scripts
- fixed XMODEL source subset와 correlation TB/script/parser
- 현재 audit, tables, plots, logs, 10,000-sample CSV 및 direct/S&H `.mem`

## 제외한 것

- 모든 LTspice `.raw` 약 18 GB
- `transient_export_50us.csv` 약 35.8 MB
- ±5 V `pre_alignment` snapshot
- Git cache와 76 MB MATLAB reference checkout
- 자동 재생성되는 77.7 MB stress `drive_*.txt`

제외 파일은 회로·입력·scripts로 재생성할 수 있다. 기존 실행 증거의 log와 정량 CSV는 포함했다.

## 필요한 환경

- Windows LTspice 26 계열
- PowerShell
- Python 3.10+와 `numpy`
- Fixed XMODEL 실행에는 Linux shell, Questa `vlib/vlog/vsim`, licensed XMODEL runtime

```powershell
python -m pip install -r ltspice_validation\requirements.txt
```

## LTspice 전체 재실행

```powershell
cd ltspice_validation
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1 `
  -Python C:\path\to\python.exe `
  -Ltspice C:\path\to\LTspice.exe `
  -SkipMatlab
```

또는 `PYTHON_EXE`, `LTSPICE_EXE` 환경변수를 설정한다. 실행하면 누락한
`drive_*.txt`와 모든 deck/raw/table이 다시 생성된다. ASCII raw는 약 14 GB 이상이므로
실행 전 disk 공간을 확인한다.

## Fixed XMODEL 실행

Linux/Questa/XMODEL 환경에서:

```bash
cd ltspice_validation
export XMODEL_HOME=/path/to/xmodel
export QUESTA_HOME=/path/to/questa
bash scripts/run_fixed_xmodel_correlation.sh
python scripts/compare_xmodel_ltspice.py
```

생성 기대 파일:

- `results/xmodel_aligned/xmodel_reference/adc_nominal.txt`
- `tables/xmodel_aligned_ltspice_xmodel_correlation.csv`
- `plots/xmodel_aligned_xmodel_waveform_comparison.svg`
- `plots/xmodel_aligned_xmodel_error.svg`

## Sample-by-sample exact 작업 순서

1. XMODEL과 LTspice 모두 `ECG+=patient`, `ECG-=0` 및 50 us input update인지 확인한다.
2. XMODEL 첫 falling edge와 LTspice direct aperture를 1.000 ms로 고정한다.
3. ADC limiter/floor/4095 scale/`code-2048`를 먼저 단독 endpoint test로 확인한다.
4. Primary gate는 `direct_adc_signed`와 fixed XMODEL signed code다. LTspice S/H stream은 별도 진단이다.
5. Sample count, timestamp, polarity, clipping, zero-lag error를 먼저 확인한다.
6. Best-lag는 진단값으로만 기록하고 데이터를 몰래 shift하지 않는다.
7. Exact mismatch가 남으면 stage-by-stage analog node와 XMODEL primitive 동작을 비교해 LTspice op-amp abstraction을 수정한다.
8. Exact 일치가 불가능한 XMODEL/LTspice solver 차이는 `CORRELATED`로 근거와 함께 남기고 임의 tolerance로 PASS 처리하지 않는다.
9. S/H acquisition/droop는 direct XMODEL gate가 완료된 뒤 별도 LTspice-only 결과로 유지한다.

## 현재 상태

- LTspice aligned runs: 35개 실행 완료, fatal/warning 0
- Direct/S&H vector: 생성 완료
- MATLAB nominal consistency: 실행 완료
- Fixed XMODEL code output: 기존 PC에 simulator가 없어 `PENDING_XMODEL_EXECUTION`

상세 변경점은 `ltspice_validation/audit/xmodel_alignment_audit.md`, 현재 결과는
`ltspice_validation/report/report_update_draft_ko.md`를 참고한다.
