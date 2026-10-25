# Manual army and fleet funding can drive the national treasury into debt

**Status:** conquest draft for Main #1456 (v0.8.1), measured under Wine; awaiting
Research promotion. Conquest task #206. **[confirmed, partial]** for the
nineteen original UI cases below; **[derived]** for the general code rule.
No native Windows acceptance or remake fix is claimed.

## Answer

The original permits manual treasury funding at **−100, 0 and +50**. With a
purse of 100 and a +100 request, the original's real money control is visible
and enabled; army **and fleet** purses become 200 and treasury becomes
**−200, −100 and −50**, respectively. This is UI-reachable behavior measured
in parsed before/after saves, not inferred solely from a missing handler gate.

Keep the distinction between accounts:

- Treasury funding uses the signed purse-cap step without checking the
  treasury balance. The 1,000 purse cap remains; an over-cap positive arrow
  sends excess back to the treasury.
- An **army supplied by a fleet** uses that fleet's purse and limits the step
  to its balance. Provider 50 funds only 50; provider 0 funds nothing. Reverse
  transfer limits the receiving fleet to 1,000.
- A **fleet target** uses the national treasury for money even when a different
  fleet is selected as the supply provider. In the measured control, provider
  fleet 5 keeps 50 while treasury −100 becomes −200 and target fleet 2 becomes 200.
  Do not infer army-provider money semantics from the selected supply provider
  when the target is a fleet.

## Method and private provenance

Retained unmodified `Imperial Conquest 2.exe`, verified against the existing
original identity pin, with unchanged original DAT. Linux; Wine 10.0
(Ubuntu 10.0~repack-12ubuntu1), isolated win32 prefix, Xvfb 1280×1024. Full EXE/DAT
identities, original files, screenshots, full fingerprints, states and hashes
are **private**, under ignored `artifacts/run-exp-manual-funding1456/`.
No original file or private hash is a Git/public-release payload.

Source fixture `fleet-split-antium-0734.SAV`, **turn 0734**. The only staged
fields are national treasury, target purse and adjacent fleet purse, checked
by a byte allowlist. Positions, map, ownership, units, moves and supplies are
unchanged. The actual original opens each staged fixture; File > Save as
records a before save, the real visible/enabled +100/−100 money arrow is
clicked, the dialog closes with OK and File > Save as records the after save.
No direct handler calls, EXE patches, writes to running memory, End turn,
battle, new campaign or native Windows interaction.

Each result file names its immutable save pair, for example
`treasury-v2_army-debt-negative_before.SAV` →
`treasury-v2_army-debt-negative_after.SAV` (turn 0734), and
`controls-v3_fleet-fleet-provider_before.SAV` →
`controls-v3_fleet-fleet-provider_after.SAV` (turn 0734).

`audit-v1.json` independently reparses **all 19 saved pairs**. All match the
predeclared predictions; all actual money controls were enabled and visible;
all account totals are conserved. All parsed strategic state apart from the
tested balances and camera view is unchanged, including turn and battle flag.
This does not claim byte-for-byte identity of unparsed save/UI fields.

## Small case table: prediction versus measured original

All 19 observations equal `all-cases-plan-v1.json` predictions fixed before the
control batch. Each request is one real money-arrow click. “Other fleet” is
fleet 2 for an army target, fleet 5 for a fleet target; it matters as a money
provider only for army/fleet-provider rows. Last column is the current native
helper result when different, as `[treasury, target purse, other fleet]`.

| Case | Request | Original treasury | Original target purse | Other fleet purse | Native helper projection |
|---|---:|---:|---:|---:|---|
| army-debt-negative | +100 | -100 → -200 | 100 → 200 | 50 → 50 | -100, 100, 50 |
| army-debt-zero | +100 | 0 → -100 | 100 → 200 | 50 → 50 | 0, 100, 50 |
| army-debt-low-positive | +100 | 50 → -50 | 100 → 200 | 50 → 50 | 0, 150, 50 |
| army-at-cap | +100 | -100 → -100 | 1000 → 1000 | 50 → 50 | matches |
| army-over-cap | +100 | -100 → 0 | 1100 → 1000 | 50 → 50 | matches |
| army-reverse | −100 | -100 → 0 | 100 → 0 | 50 → 50 | matches |
| army-reverse-limited | −100 | -100 → -50 | 50 → 0 | 50 → 50 | matches |
| army-fleet-limited | +100 | -100 → -100 | 100 → 150 | 50 → 0 | matches |
| army-fleet-empty | +100 | -100 → -100 | 100 → 100 | 0 → 0 | matches |
| army-fleet-over-cap | +100 | -100 → -100 | 1100 → 1000 | 50 → 150 | matches |
| army-fleet-reverse | −100 | -100 → -100 | 100 → 0 | 50 → 150 | matches |
| army-fleet-reverse-cap | −100 | -100 → -100 | 100 → 50 | 950 → 1000 | matches |
| fleet-debt-negative | +100 | -100 → -200 | 100 → 200 | 50 → 50 | -100, 100, 50 |
| fleet-debt-zero | +100 | 0 → -100 | 100 → 200 | 50 → 50 | 0, 100, 50 |
| fleet-debt-low-positive | +100 | 50 → -50 | 100 → 200 | 50 → 50 | 0, 150, 50 |
| fleet-at-cap | +100 | -100 → -100 | 1000 → 1000 | 50 → 50 | matches |
| fleet-over-cap | +100 | -100 → 0 | 1100 → 1000 | 50 → 50 | matches |
| fleet-reverse | −100 | -100 → 0 | 100 → 0 | 50 → 50 | matches |
| fleet-fleet-provider | +100 | -100 → -200 | 100 → 200 | 50 → 50 | -100, 150, 0 |

## Code and caller/UI gates

References are to the pinned `all_app_functions.txt` (existing decompile pin
`2018c205…`), exact starts/ends in `source-audit-v2.json`:

- `TUnitMap_SupplyArmy @00446F50`, lines 46829–46855, and
  `TUnitMap_SupplyFleet @004477FC`, lines 47126–47158: selected owned target
  and qualifying nearby provider; neither checks treasury sign/balance.
- `TAFSupply_InitializeForm @0043EDC0`, lines 42278–42332: selects target,
  initializes providers and spinners. No treasury gate.
- `TAFSupply_CityOrFleet @0043EFAC`, lines 42337–42564: own city or fleet shows
  the money controls; foreign city hides them. It changes visibility via
  `00412C08`, not a balance-based enabled flag. `ChangeProvider @0043FB10`,
  lines 42828–42887, refreshes this visibility and numbers.
- `TAFSupply_ChangeMoney @0044005C`, lines 43091–43174: positive-arrow army
  step `min(request,1000−army_purse)`; treasury branch subtracts it without a
  source-balance test (43118–43135). Fleet-provider army branch adds
  `min(step,fleet_purse)` (43129–43132). Reverse army step limits to the army
  purse and, for a fleet receiver, `1000−fleet_purse` (43154–43169).
- The **fleet-target** branch (43107–43115, 43145–43151) always uses national
  treasury, independently of the selected supply provider. This distinction
  is measured in the final table row, not just decompiled.
- `TAFSupply_OK @00440234`, lines 43179–43185, closes the form. Money arrows
  already update balances; OK does not introduce a later treasury check.

## Current remake comparison

Source pin `a5cfebedbb419870985c5f86e3987f238dd587f4`. Retained native build
pin `b593c6e28939c1c7154f9a41d0436a8f14f352dc` has byte-identical
`TreasuryPurseTransfer.cs`, `TransferMoneyCommandHandler.cs` and faithful
ruleset, verified by authoritative Git blob identities in `source-audit-v2`.
Faithful purse cap is 1,000 in both. No source overlays or replacement logic.

`Native.cs` calls the actual upstream helper with the current handler's
source-verified treasury/via dispatch. **12/19 match; seven differ**: the six
army/fleet treasury funding cases and the fleet-target/via-fleet case. This is
an actual helper comparison plus a dispatch projection, **not** native UI,
full command integration or installed-desktop-build validation.

`native-v2.json` is authoritative: the current command routes a via-fleet
request through purse/purse for either target kind. `native-v1.json` chose
treasury for every fleet target (original routing), so it did not compare that
current via dispatch. V1 is retained with its narrower scope disclosed.
No remake UI routing bug is claimed without checking the actual caller.

## Precise faithful correction recommended for #1456

1. Give **manual treasury-to-army and treasury-to-fleet** transfers their own
   source semantics: use signed `min(request,cap−purse)` without limiting to
   the treasury's balance or zero. Move the treasury by the exact opposite
   applied amount. Preserve the cap and signed over-cap pullback.
2. Keep the **army/fleet-provider** purse balance limit, reverse-direction
   donor limit and receiving-purse cap. Do not remove the common source clamp
   for every account merely to fix the treasury case.
3. For the faithful original **Supply fleet** money action, use treasury even
   when a fleet supplies the provisions. Check the remake caller before
   treating generic CLI `via` support as a UI defect; a deliberately extended
   CLI purse/purse operation can remain separate from original dialog parity.
4. Replace the obsolete remarks that call treasury debt unknown or say manual
   transfers cannot drive treasury negative. Add regressions for these measured
   cases at the appropriate treasury/provider dispatch boundary.
5. **Preserve T207's automatic-funding treasury reserve**, the separate
   owner-selected QoL policy. This research does not change presets, automatic
   decisions, existing UI fixes, release scope or version tags.

## Evidence and limits

Public case scalars, predeclared predictions, audit and source references:
`runs/experiments/data/run-exp-manual-funding1456/`. Reproducible probes:
`runs/experiments/manual-funding1456/`; running notes:
`RUN-NOTES-manual-funding1456.md`. Measurements are exclusive/versioned;
no saves or outputs overwritten or deleted. Pilot-v1 failed before clicking
because the runner called a nonexistent hover method; its files/failure are
retained. Source-audit-v1's approximate ranges are superseded by mechanically
located exact ranges in v2, with both kept.

One Roman fixture and turn; monetary fields are synthetic, not naturally
played debt. Negative fleet/army purses, integer overflow, foreign-city money
visibility in live play and every possible provider configuration were not
measured here. Broader signed rules are decompiled predictions unless already
covered by earlier research. Wine observations remain candidates for native
Windows confirmation; no further owner save or Windows access was needed for
this bounded task.
