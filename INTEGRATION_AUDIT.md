# Integration audit

This file is finalized after all component imports, evidence extraction, and
integrity checks. The integration uses Git-object exports of three fixed commits;
it never copies an upstream working tree or `.git` directory.

The parent digital repository locally excludes `/ECG-SoC-Integrated/` through
`.git/info/exclude`. This is a local-only safety entry and is not committed to
the parent repository.
