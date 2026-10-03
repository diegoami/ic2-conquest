# Tracked measurements of the experiments

The text outputs (trial tables, logs, logs of probes, timings, OCR dumps) of each experiment, copied from the git-ignored
`artifacts/run-exp-<name>/` so that a stopped session or a lost machine loses nothing, and `SAVES.sha256`, the SHA-256 of every save
and other binary of that experiment (the files themselves are in the GitHub release `run-exp-<name>`, never in git: CLAUDE.md rule 1).

Rule 6 of CLAUDE.md: new experiments write their text outputs straight to `runs/experiments/data/run-exp-<name>/`, commit and push
after each batch and at least every 30 minutes, and never delete or overwrite a measured file (a re-run writes new files beside
the old ones and the finding says which it cites). The experiments up to 2026-10-04 were copied here afterwards, unchanged, from
`artifacts/`.
