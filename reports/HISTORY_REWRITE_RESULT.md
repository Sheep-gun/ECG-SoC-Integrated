# History rewrite result

## Result

- Tool: `git-filter-repo 2.47.0`
- Rewrite completed locally: yes
- Force push performed: no
- Branch: `main`
- Pre-maintenance public HEAD: `32d2fbd582040f7de7ed54e4ecf5a8a4efd19268`
- Rewritten public-baseline equivalent: `f52c4c2fb3a73bd6d223b3f2cbd805918d6d5db3`
- Post-rewrite content commit preceding final audit: `a64919be207f7131202a735bdc2def93d198ab56`
- Rewritten preliminary audit commit: `d6a10f7cf55cbc922792171f79134861f5e02497`
- Actual final HEAD: report with `git rev-parse HEAD` after the final audit commit
- Restored remote: `origin` → `https://github.com/Sheep-gun/ECG-SoC-Integrated.git`

## Exact rewrite

The rewrite used `--invert-paths` for only these prefixes:

```text
components/afe_xmodel/algorithm/person_data/nsrdb/1.0.0/
components/afe_xmodel/algorithm/person_data/chfdb/1.0.0/
components/afe_xmodel/algorithm/person_data/mitdb/1.0.0/
components/afe_xmodel/algorithm/person_data/afdb/1.0.0/
```

`git rev-list --objects --all` contains zero matching raw-data paths after rewrite. `git count-objects -vH` reports one 44.11 MiB pack and no loose/garbage objects.

## Size reduction

| Metric | Before | After |
|---|---:|---:|
| Working-tree bytes excluding `.git` | 2,307,174,104 | 140,346,925 |
| `.git` bytes | 1,535,086,190 | 48,243,693 |
| Repository total bytes | 3,842,260,294 | 188,590,618 |
| Reachable/object storage (`git count-objects`) | 1.42 GiB loose | 45.83 MiB pack |
| Tracked files ≥10 MiB | 56 | 0 |
| Tracked files ≥50 MiB | 15 | 0 |
| Largest tracked/reachable blob | 53,996,544-byte CHFDB `.dat` | 7,514,904-byte project-derived MATLAB CSV |

The working tree decreased by 2,166,827,179 bytes (about 93.92%), and local repository total decreased by 3,653,669,676 bytes (about 95.09%).

## Provenance and retained evidence

The curated artifact manifest contains 913 retained component files (MATLAB 136, XMODEL 520, digital 257). Each retained integrated Git blob is compared directly with the corresponding fixed upstream commit blob. The 981 omitted upstream paths comprise 977 fixed-version PhysioNet distribution paths plus four submission/temporary paths; retained+excluded paths cover all upstream tracked paths.

Locked `.mem` inputs, strict split/lock metadata, classification/evaluation CSV/JSON, AFE-to-RTL comparisons, board replay evidence, source, RTL/IP/Vivado/Vitis evidence, figures and manuscript remain.

## Backup

- Bundle: `<LOCAL_BACKUP_BUNDLE>`
- SHA256: `6601AA18474939D0C659AFAE6219E7E7371287DCEA7ACF12171D169FBB929D1C`
- `git bundle verify`: complete-history PASS

Machine-readable after lists are `largest_current_files_after.csv` and `largest_git_blobs_after.csv`.
