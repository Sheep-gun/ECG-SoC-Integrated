# 구성별 출처와 handoff

| 구성 | 고정 commit | 통합 위치 |
|---|---|---|
| MATLAB AFE–ADC | `907f7e1f081a9d6a5703a32095d962143315a192` | `design/analog/matlab/` |
| LTspice와 XMODEL | `4756a5086023547328ef44fd5fd87da3c250dc39` | `design/analog/ltspice/`, `design/analog/xmodel/` |
| Digital RTL | `c6b80de19cdcad5b7e43fe7835588b629d847f75` | `design/digital/` |

공개 authority는 로컬 checkout 경로가 아니라 `project_registry/upstream_commits.yaml`의 repository URL과 immutable commit이다. handoff 규약은 1 kSPS signed 12-bit ECG, `sample_valid`와 final class/membrane interface다.
