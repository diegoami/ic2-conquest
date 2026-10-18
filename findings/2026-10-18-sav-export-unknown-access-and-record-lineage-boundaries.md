# SAV export: bounded unknown-byte access and record-lineage rejection boundaries

2026-10-18. **[confirmed, partial] source and original-x86 helper evidence; independent review pending.** Research [#37](https://github.com/diegoami/imperial-conquest-2-research/issues/37), conquest [#99](https://github.com/diegoami/ic2-conquest/issues/99). Implementer: **gpt-6.1-sol medium (OpenAI)**, owner-selected agent; owner-selected independent reviewer **Kimi K3, `kimi-code-plan-global/k3`**.

**Result:** four exercised helper paths do not read or write the 31 unresolved bytes in any nation, even with nonzero patterned contents. This strengthens **bounded path conservation**, without proving the bytes are padding or safe across gameplay. Two new unit-deletion controls show exactly how historic slot bytes survive removal and move with the last live unit. Equal visible text plus an equal rename still leaves different binary tails. Consequently a normalized native object list/text value cannot reconstruct authentic record lineage. **Changed-state export remains unsupported unless its complete operation/dependency and lineage proof is supplied.** No new default is authorized.

This extends the [partially promoted safety report](2026-10-17-sav-export-live-regions-and-safe-rejection-policy.md); it does not supersede its field matrix or native Windows gate. Research #37/conquest #99 remain open. No owner inputs, candidate exports, game/Wine/native runs or new SAV files were accessed/generated. Task #25, T177 and build work are untouched.

## Evidence and scope

The [immutable evidence index](../runs/experiments/data/run-exp-sav-export37-closure/README.md) selects authoritative outputs and retains rejected/earlier measurements. Input pins remain the prior report's source/EXE/DAT hashes. Controls load only already-public `run0-start-AUTO0720-seed12345.SAV`, turn 0720, SHA-256 `050bc354f1cbbe374b6a627f06054f2043b9f91a268f6fbfbc18ed1e7e65574c`; its data supplies the synthetic emulator environment, not a newly observed game result. Unmodified helper instructions execute under Unicorn 2.1.4, without stubs or host game execution.

`source-alias-leads-v2.json` searches all sixteen complete nation address ranges `[00474670,00478FB0)`, any symbol spelling or literal, and functions containing the byte/WORD/DWORD strides `494/24A/125`. It records **156 functions / 680 absolute lexical references**, **zero additional functions** versus the older broader 247-function inventory, zero starting addresses in the unknown regions, and zero matching relative-offset constants within selected functions. This adds a reproducible negative lexical check, **not semantic closure**. It does not resolve access width, derived pointers, scaled/dynamic offsets, transitive callees or out-of-selection relative constants. A read starting before an unknown byte could overlap it. Generic `StrCopy` demonstrates why caller-specific pointer analysis still matters.

The initial `source-alias-leads-v1.json` accidentally includes 224 bytes after the nation table. Its 17 apparent added functions concern that adjacent range and are **not nation evidence**. It is retained as a rejected draft. The empty `source-added-functions-v1.txt` derives from corrected v2, which has no additions. No additional function claim relies on it.

## Bounded access controls

`x86-path-controls-v2.json` records six passing controls. For the first four, all **31 × 16 = 496** unknown bytes (`450..46A`, `46D`, `491..493`) contain nonzero patterned synthetic values. Memory hooks cover the **entire accessed interval**, so an instruction starting outside a byte can still be caught when it overlaps. Hooks record guest instruction PC, read/write event type, address, size and intersected unknown addresses. All four paths report no guest read/write event there and preserve every canary exactly.

| Exercised path | Additional measured result | Exact limitation |
|---|---|---|
| `0044B8F4`, city-list helper, public start city 90 from nation 0 to 1 | All sixteen `434/43C/448` baseline tuples remain exact | Caller has not updated owner/count/economy; this is not a completed city transfer |
| `00449F08`, successful army constructor at public start city 85 | New army index is returned; no unknown-byte access | One constructor path/location/controller profile; not every caller or turn |
| `0044AC3C`, remove last of two live unit slots | Old last slot clears troops; origin/type/quality/name tail persist | Two contiguous live slots in a synthetic army; not every list topology |
| `0044AC3C`, remove first of two live unit slots | All 32 bytes of the last slot move to slot 0; old last clears troops only | Same bounded topology; no general normalized-list reconstruction proof |

A sixth control routes original `StrCopy @00405B00` **deliberately** through synthetic pointers into unknown bytes. Its log contains both guest reads (`16`) and writes (`17`) at the expected unknown addresses, proving the hooks can detect indirect accesses. A host-side NUL setup also changes a canary; the positive result rests on the recorded guest read/write events, **not** merely the final `all_canaries_preserved=false`. This deliberate pointer route is instrumentation validation, not evidence of a reachable original gameplay caller.

This proof is narrower than “unknown bytes never change.” It authorizes no changed-state campaign export: other constructors, orders, turn processing, UI actions, loaders and modal/tactical paths are not covered by these four negative controls. The prior 224 public all-zero records remain observations, never default semantics.

## Unit and text lineage

Exact source is retained in `source-controls-and-history-v1.txt`: `0044AC3C` at pinned source lines **49430–49462**, with slot count helper `0044A66C`; `0044A80C` updates the resulting map marker. The deletion helper copies eight DWORDs from the last slot and clears only its troop WORD. Our two controls use different origin/type/quality values and different trailing text in each slot. Both exact post-buffer assertions pass. The now-inactive last slot retains 30 of its 32 bytes; its visible name and trailing bytes are not reset. Removing the first unit moves the surviving unit's entire own buffer, rather than preserving the removed destination slot's old tail.

The fifth control applies the same original `StrCopy` rename, `old` → `Hi`, to two 24-byte buffers with the same visible initial name and different historic tails. Both write `Hi\0`, retain **21** prior trailing bytes and remain unequal. The source and control support this exact conclusion: **a normalized visible string and rename alone do not determine the original bytes**. They do not establish that every tail byte affects behavior, or that canonical padding is always unsafe. Neither semantic irrelevance of all inactive/text bytes nor a complete safe canonical new-record policy is proved.

For original byte identity, record identity/order, the full source slot buffer and the actual operation history must remain bound together. After removal, the last unit's residue follows that unit into its new slot; the vacated last slot follows the original troop-clear behavior. Copying unrelated destination/template residue or zeroing inactive slots fails that identity contract. A new native army or fleet still needs the complete field/residue policy missing from the prior constructor packet (army 560/656 bytes retained, fleet construction 16/26 retained); these new deletion controls do not fill that gap.

## Historical/profile lineage and exact rejection contract

The prior pinned DAT loader (`original-news_log_decomp.txt`, `004481A0`) copies initial `430→434`, `438→43C`, `446→448`. The full pinned dump does not contain that loader or `004487C4`; use the retained supplemental sources, not an invented full-dump citation. `THumanFalls_InitializeForm`, **56436–56448**, reads these saved historical values under “270 BC”; the SAV loader reads the full nation block without deriving them anew. The new list-helper control preserves the three baselines while changing city-list bytes; it does not prove applicability of any DAT profile to a native campaign.

The exact current support boundary is:

| Input/request | Supported decision in this packet |
|---|---|
| Complete authentic envelope; complete relevant original state unchanged | Prior validated identity path only; normalized field equality is insufficient |
| Changed gameplay state; unknown regions merely copied from its own template | **Reject `UNKNOWN_DEPENDENCY_UNPROVED`**: same lineage does not establish conservation over the requested changed operation |
| A state changed only by one measured helper | Bounded helper conservation evidence only; **no complete export approval** until all related fields, caller effects, framing, history and other gates are proved |
| Native new army/fleet, omitted inactive bytes, or normalized text with lost original tails | **Reject `RECORD_LINEAGE_OR_RESIDUE_POLICY_MISSING`** for an identity-preserving path; a separately proved canonical semantic policy could be investigated later |
| Deletion/reordering from a native list without original slot identities/whole-buffer mapping | **Reject `SLOT_LINEAGE_MISSING`**; matching visible surviving units does not recover historic source/destination buffers |
| Missing authentic start history; matching current totals, names or “270 BC” scenario title | **Reject `HISTORICAL_PROFILE_APPLICABILITY_UNPROVED`**; current coincidence is not origin provenance |
| Source/EXE/DAT hashes known but original campaign origin/mutation history absent | Binary pins identify research inputs, **not native save provenance**; same history rejection |
| Candidate paths/private inputs/coordinated Windows runtime unverified | Do not attempt original round trips; preserve originals and obtain owner coordination first |

The rejection names are proposed diagnostic vocabulary for the supported-state contract, **not implemented exporter error codes**. A source-bound native campaign with independently attested classical origin may eventually use the pinned start baselines; an arbitrary faithful-looking or imported campaign cannot. No profile is inferred from its title, current city count, all-zero unknown bytes or a public reader's unmapped-field list.

Required next evidence remains operation-complete dependency/alias analysis or mapped meanings for all 31 bytes, a justified complete new-record/inactive/text policy, authentic historical/profile lineage, then applicable candidate exports and the coordinated independent **three-output native Windows gate**. Candidate/private/runtime availability remains **UNVERIFIED**, not absent. This packet performs **zero** Windows round trips and makes no compatibility, future behavior or RNG-equivalence claim.
