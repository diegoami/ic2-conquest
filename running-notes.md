# PR #84 round-6 — R1 fix
## Plan
- [x] Add test_receiver_assertion_via_give_cities: calls production give_cities(), patches _give_cities_put with a wrapper that injects rogue byte BEFORE original, so assertion fires inside _give_cities_put
- [x] Wrapper injects only when snapshot is not None (simulates give_cities path)
- [x] Regression-detection control: calling wrapper with snapshot=None proves no raise
- [x] Update docstring to describe all four tests
- [x] All four tests pass; commit and push to origin/experiment/g4-followups
## Progress
- 2026-10-12 19:41 commit: a7c0906 — tests: add test_receiver_assertion_via_give_cities (round-6 R1)
- 2026-10-12 20:00 commit: <sha7> — round-7 R1: gate receiver injection; reach flag + receiver-tag assertion
## END
- 2026-10-12 19:41 stopped after: a7c0906 — summary: round-6 test added, all four pass, pushed to origin
- 2026-10-12 20:00 stopped after: <sha7> — round-7: receiver-only gate + reach flag; adversarial regression sim confirms detection
