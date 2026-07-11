# Publish rewritten history safely

The local rewrite is not publication. Do not run these commands until the final local checker results and final HEAD reported by Codex have been reviewed.

## Publication command

```powershell
git push --force-with-lease origin main
```

Use an explicit lease tied to the verified public baseline, not plain `--force`:

```powershell
git push --force-with-lease=refs/heads/main:32d2fbd582040f7de7ed54e4ecf5a8a4efd19268 origin main
```

This command refuses the update if another party changed public `main` after the audited baseline.

## Remote verification

```powershell
git ls-remote --heads origin main
git fetch origin main
git rev-parse main
git rev-parse origin/main
git log --oneline --decorate -5 main
git rev-list --objects origin/main | Select-String 'components/afe_xmodel/algorithm/person_data/(nsrdb|chfdb|mitdb|afdb)/1.0.0/'
```

The last command must produce no output. A fresh clone should then run both Python checkers.

## Existing-clone warning

Every rewritten commit has a new SHA. Existing clones must not merge the old and rewritten histories. Safest recovery is a fresh clone. If preserving a clone is essential, first back up local work, fetch, and explicitly reset/rebase onto the rewritten `origin/main` only after understanding the consequences. The pre-rewrite full bundle remains at `C:\Users\YangGeon\SNN ECG Classifier\ECG-SoC-Integrated-before-slimming.bundle` with SHA256 `6601AA18474939D0C659AFAE6219E7E7371287DCEA7ACF12171D169FBB929D1C`.
