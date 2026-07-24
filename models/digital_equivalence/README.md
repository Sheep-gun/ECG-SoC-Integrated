# Python 및 Exact C++ 등가모델

최종 디지털 분류기의 Python 정수 등가모델과 Exact C++ 등가모델을 보존한다. 원본은 upstream 저장소 `Sheep-gun/SNN-ECG-4-Class-Classifier`의 benchmark 완료 커밋 `09e4d840827ad20856f5e23be4743ddd01565e30`에서 복구했다. 이 benchmark가 대상으로 한 고정 RTL은 커밋 `c6b80de19cdcad5b7e43fe7835588b629d847f75`이다.

## 보존 범위

- `tools/locked_integer_inference.py`: RTL과 동일한 정수 연산 및 최종 판정 Python 모델
- `tools/snapshot_c24_rtl_exact.py`: Snapshot 처리의 cycle-explicit Python 모델
- `tools/run_python_benchmark.py`, `tools/check_python_equivalence.py`: Python 실행 및 정합 검사
- `exact_cpp/`: Exact C++ 소스, 단위시험, 정합 결과와 검증 도구
- `reference/`: 잠금 기준 파라미터

통합 저장소에서는 디지털 소스를 `design/digital/`에서 찾도록 경로만 조정했다. 모델 연산, 가중치, 임계값, 파이프라인 의미와 고정 RTL은 변경하지 않았다.

## 실행 범위와 데이터

Python 모델은 NumPy가 필요하다. Exact C++은 C++17과 CMake로 빌드할 수 있다.

```powershell
cmake -S models/digital_equivalence/exact_cpp -B <BUILD_DIR>
cmake --build <BUILD_DIR> --config Release
ctest --test-dir <BUILD_DIR> -C Release --output-on-failure
```

36개 30분 입력은 고정 PhysioNet 원본과 보존된 AFE 규칙에서 재생성한다.
먼저 `tools/data/generate_locked_digital_36case.py`를 실행하면 저장소 밖의
`../generated_rtl_fpga_test_inputs_36case`에 잠금 `.mem`과 SHA-256 manifest가 생성된다. 이어 다음
명령으로 Python 예측 클래스와 네 Final Membrane을 36개 모두 재검증한다.

```powershell
python models/digital_equivalence/tools/check_python_equivalence.py --workers 4
```

재생성된 36개 입력은 실제 XMODEL dump가 아니라 과거 FPGA/XSim 검증 입력의
재현본이며, 실제 full-30분 XMODEL 출력 4개와 구분한다.

Vivado 기반 보조 검증 도구를 실행할 때는 `VIVADO_BIN`을 Vivado `bin` 디렉터리로 지정한다. 별도 C++ toolchain 경로가 필요하면 `EXACT_CPP_TOOLCHAIN_BIN`을 사용한다.
