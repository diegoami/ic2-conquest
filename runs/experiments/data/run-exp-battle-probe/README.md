# run-exp-battle-probe: data folder notes (added in the battles PR A, the B0 review's notes R2 and R3)

- `b0-resume-comparison-20261004.json`, `b0-series-comparison-20261004.json`, `b0-series-comparison-lab2-20261004.json` are **historical**: they
  were made by an earlier ad-hoc command (their schemas, `closest_original`, `differing_vs_orig_same_offset(i+5)`, `"lab1_a v lab1_t0"`, are not
  the ones the committed `b0_probe.py` writes) before the commands `report`, `resumecmp` and `compare` existed. They are kept as measured.
  The committed commands regenerate the same facts: `gate-summary-20261004-085012.json` (series and post-battle byte comparison),
  `resume-comparison-resume05_gate2_a_r{1,2}-20261004-085925.json` (resume v original and v a second resume).
- `compare-gate2_a-gate2_s2a-20261004-092047.json`: seed 1 v seed 2, `BATTLE01` to `BATTLE15` (the first file differs in 29 bytes), the byte
  comparison behind the finding's "differ from BATTLE01 (29 bytes)".
- `b0-lab-pra_check-*` / `lab1_pra_check_*`: one lab seed-1 trial re-run after the driver changes of PR A (neutral click point, `Game.open`,
  proven End turn loop, `computer_general_on`): its post-battle save is byte-identical to the earlier ones (`415797f3a927`).
