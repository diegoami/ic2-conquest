# PR #84 round-6 — R1 fix
## Plan
- [ ] Add test_receiver_assertion_via_give_cities: calls production give_cities(), patches _give_cities_put with a wrapper that injects rogue byte BEFORE original, so assertion fires inside _give_cities_put
- [ ] Wrapper injects only when snapshot is not None (simulates give_cities path)
- [ ] Regression-detection control: calling wrapper with snapshot=None proves no raise
- [ ] Update docstring to describe all four tests
- [ ] All four tests pass; commit and push to origin/experiment/g4-followups
## Progress
- 2026-10-12 19:41 commit: a7c0906 — tests: add test_receiver_assertion_via_give_cities (round-6 R1)
## END
- 2026-10-12 19:41 stopped after: a7c0906 — summary: test added, all four pass, pushed to origin
