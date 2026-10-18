# SAV export: a bound-original tax edit subset and binary alias evidence

2026-10-18. **[confirmed, partial] original source, executable instructions and public-input memory projections.** Research #37/conquest #99. Implementer **gpt-6.1-sol medium (OpenAI)**; independent Kimi review pending. This follows the [field policy](2026-10-17-sav-export-live-regions-and-safe-rejection-policy.md) and [bounded lineage controls](2026-10-18-sav-export-unknown-access-and-record-lineage-boundaries.md).

**Concrete progress:** the original tax command has a bounded **0..40** value domain and a measured core serialized projection. Its commit writes current nation `+44A`; refresh also writes/clamps viewport `+486/+488`. We measured the real instruction slices for all **16 × 41 = 656** tax assignments, four viewport cases and four original rename/conversion/whole-army commits. A strict reference tax projection accepts three public bound envelopes at rates 0 and 40, changing only the tax WORD; it rejects a foreign nation's tax, out-of-range rate and pending-offer state. This is a constructive changed-byte mapping, beyond identity copying or blanket UNKNOWN rejection.

**It remains a candidate exporter profile, not compatibility approval.** The measurements execute instruction slices, not complete GUI callbacks or Windows. Source composition identifies the exact remaining UI/provenance obligations below. No claim that those obligations were executed or that the twelve native owner JSON files can use this profile. No original/game/native run or SAV file write occurred. Research #37/conquest #99 stay open.

## Exact useful profile

Proposed profile `bound-original-current-human-tax-v1` takes an **authentic original envelope plus an explicitly bound tax edit**, not an arbitrary full native save. A trusted import/edit journal must bind the source hash and prove that the only native semantic change since import is the current human nation's tax. An unsupported native JSON cannot supply that proof by matching a few fields or claiming no missing fields.

Enforce all of the following:

1. Same pinned original format/version, structurally valid strategic envelope; no open battle, modal/turn-resolution work, new/removed/reordered records, changed army/fleet/city/map/queue/controller/calendar/economy/history state or unrepresented pending action. Fixed source envelope is retained in full. Source authenticity/loadability and the complete native baseline binding remain caller obligations; the research helper is not a production native importer.
2. Nation index equals the envelope's **current nation**, whose controller BYTE is **1**. Tax is an integer **0..40**, the original trackbar's explicit `Max=40` resource property. Sixteen-nation sweeps test address arithmetic; they do not authorize editing foreign nations.
3. Pending-offer source is **-1** for this minimal profile. Do not clear an offer to enter it. The original public start `run0-start-AUTO0720-seed12345.SAV`, turn 0720, fails this gate because its pending source is 11.
4. Use the bound original UI profile: width/height from `+47C/+47A`, viewport X/Y from `+488/+486`. The helper checks those inputs match the envelope, then requires the refresh clamp to leave the viewport unchanged. Chosen minimal positive width/height bounds are 271..1295 / 269..1005; these are conservative research-profile bounds, **not claimed original maximum dimensions**.
5. For the **original-command composition proof**, begin with a fresh original process/load and no selected map cell/army/fleet, no pending move, no unrelated queued event, and stable form geometry/scroll getter values. Fresh form initializer `00445958` sets its selection fields to -1; loader `004487C4` and `TPremierForm_StartTurn @0045AC5C` reset runtime army/fleet selectors. These fields are not all serialized, so they cannot be inferred from the SAV alone in an arbitrary reused process. The original validation protocol must establish them; the helper does not pretend to validate runtime state from bytes.
6. No simulation tick, order or other edit intervenes. Preserve **all other bytes**, including the 31 UNKNOWN nation bytes, authentic historical baselines, inactive/tombstone/text residue, record order, offers and RNG-related saved state. The algorithm uses original bytes, never a synthesized canonical template or DAT substitution.

On satisfying the source/native binding and UI obligations, the reference serialized transformation is:

```
output = exact copy of the bound source envelope
output[nation_offset + 1172*current_nation + 0x44A : +0x44C] = little-endian WORD(tax)
```

The reference implementation `tax_projection` additionally calculates and checks the identity clamp. The three public examples below are **byte-projection tests**, not attested native import/edit histories or approved original-compatible exports. The exporter can implement this finite profile and reject every other delta. **No existing exporter or native JSON conversion is implemented/enabled by this research packet.** Complete GUI composition and the independent native gate still precede compatibility claims.

## Original command and serialized side effects

Exact original source is retained in `source-command-consumers-v1.json` (36 functions / 1,800 exact numbered lines). Source SHA-256 remains `2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8`; EXE `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`; DAT provenance remains in the prior packet. The original source is encoded in JSON strings without stripping its trailing spaces.

- `TChangeTax_InitializeForm @00453E6C` reads saved tax `+44A` into dialog `+1F8`, reads tax base `+44C` for the income preview, and initializes UI controls. `TChangeTax_SetNewTax @0045409C` updates the dialog value from the slider. This does not recalculate tax base or treasury.
- `TChangeTax_OK @004540B8`, source 55665–55675, assigns the current nation's tax WORD, calls `TPremierForm_RefreshForms @0045BA6C`, sets the dialog result and posts its close request. Exact instruction interval **4540B8..4540DC** stops **before** refresh; one serialized WORD write was observed in every sweep case. No inference about the skipped callback follows solely from this slice.
- Refresh calls `TUnitMap_PaintForm @00445D38` and `TInformation_ShowNationStatus @0043BA7C`. Paint reads actual form/scroll state and assigns/clamps X/Y, with `s3=floor((width−15)/32)`, `s4=floor((height−45)/32)`: `X=max(0,min(scrollX,319−s3))`, `Y=max(0,min(scrollY,139−s4))`. Original interval **445D89..445E01**, including unmodified min/max callees, matches this model in identity, upper and lower clamp cases. Geometry getter results are explicit inputs; no GUI getter is stubbed and claimed tested.
- **Selection is a real dependency.** Paint can call `TUnitMap_SelectUnit @004466CC` when form `+21A >= 0`; that path can attack, embark or issue other gameplay effects using runtime selected army/fleet state. A tax-only envelope is therefore not claimed equivalent to an arbitrary live UI click. The profile demands the unselected/stable original-load protocol above.
- Information refresh writes strings in `[0049F00C,0049F994)` and display index `004A031C`. The retained save writer and supplemental loader show these are outside **all** serialized spans, including the optional tactical block. The proof output enumerates the entire strategic stream, news, order/offers/trailer/battle flag, plus all seven conditional tactical spans; it checks scratch exclusion against each. News begins at **0049F994**, not at the information scratch address. No tax-base update is hidden in this renderer.
- `FUN_0042313C` posts message `B021` through `PostMessageA`; it is an asynchronous close boundary, not a completed close/pump experiment. Generic form creation/virtual dispatch and queued close/event processing were not executed by the proof. Those remaining edges are obligations, not silently ignored writes.
- Ordinary save calls `TPremierForm_StoreFormPositions @0045BB1C`, which writes the saved geometry fields. The profile requires stable validated geometry; a different desktop/layout can legitimately yield different UI bytes. The serializer itself also captures main-window geometry. Do not equate a core tax projection with an exact GUI SaveAs file if those inputs differ.

`transition-projection-v3.json` is authoritative. Its snapshots compare the **entire strategic serialized stream**, rather than just edited fields, and collect each actual serialized write event. The 656 tax cases have one `+44A` WORD write each. Four viewport controls include explicit nonidentity clamps, demonstrating why the profile must test identity instead of assuming it. Three public sources each pass tax=0 and tax=40 in memory:

| Public bound source | Turn | Result |
|---|---:|---|
| `det-AUTO0721-clock.SAV` | 0721 | Tax-only changed offsets; source/output hashes recorded |
| `fleet-port-antium-0734.SAV` | 0734 | Same, existing fleet envelope retained |
| `fleet-split-antium-0734.SAV` | 0734 | Same, different fleet/count lineage retained |

No candidate file was written; scalar hashes describe in-memory projections only. Existing source saves were neither changed nor uploaded.

## What the binary audit actually found about UNKNOWN bytes

The prior decompiler lexical audit missed **three pointer anchors at nation+450**. `x86-cfg-alias-leads-v1.json` scans recursive x86 control flow from **1,884** known/supplemental/entry roots, decoding **74,750 instructions / 232,148 of 375,252 executable virtual bytes**, with zero decode failures or overlapping targets in that traversal. It records **812 indirect edges unresolved**, 408 nation operand leads and 411 nation-valued HIGHLOW relocations. This is instruction evidence with an explicit coverage boundary, not whole-program alias closure.

| Anchor instruction | Consumer in the original function |
|---|---|
| `00445B61: lea eax,[eax*4+00474AC0]` | `TUnitMap_PrintMapSquare` reads anchor `+36/+38`, i.e. nation `+486/+488` |
| `00445D96: lea edi,[eax*4+00474AC0]` | `TUnitMap_PaintForm` reads/writes anchor `+36/+38`, the same viewport fields |
| `004462C4: lea esi,[eax*4+00474AC0]` | `TUnitMap_AreaMapClicked` writes the viewport at those offsets |

These LEAs **form an address**; they do not read the UNKNOWN byte at +450. Decompiler constant folding explains why no literal +450 appeared in the old source inventory. The actual pointed-at viewport consumers are retained in full source. Their existence invalidates any inference from “no decompiler references” to “no pointers into this region.”

Save/load **do** consume all 31 bytes as part of the wholesale nation stream; “unconsumed” would therefore be false even if gameplay padding were eventually proved. No meaning/default is assigned to +450..46A/+46D/+491..493. No universal non-serialization consumer absence is proved: dynamic pointers, untraversed entries and 812 indirect edges remain outside the analysis. A second attempt seeding every relocated CODE address produced 266 decode failures and 2,514 overlapping targets because metadata/data addresses are not necessarily instructions. Its output is retained as a **rejected coverage experiment**; its apparent 353,893 covered bytes must not be presented as valid 94% executable coverage.

For the tax profile, opaque bytes remain bound to their original envelope and untouched across the known typed change. Full alias meaning is not replaced with a zero assumption. The useful narrow claim is the tax/viewport serialized projection under stated command-composition conditions, not arbitrary gameplay evolution with unknown inherited bytes.

## Inactive fields, text tails and new objects

The new rename evidence uses the **actual** original conversion path `00405B88 → 00403634 → 00405B54`, not merely generic `StrCopy`. The form resource has `MaxLength=23`; converter bound 255 is not protection for the army's 24-byte destination. Four names of length 0, 1, 10 and 23 produce prefix+NUL writes in the dialog copy. `TChangeArmyUnits_OK @00445378` then writes unchanged mobilization and copies the whole **656-byte** army. All other serialized bytes compare exact. The source root permits rename only for a single selected **regular, live** unit; no permission to rename arbitrary mercenary/inactive slots is inferred.

This proves how an existing bound unit can retain its own tail through the real conversion/parent commit. It does **not** complete the outer selected-unit GUI callback path, so rename is not enabled by the minimal tax profile. It also does not prove a whole-record tail is semantically significant. Explicit consumers distinguish the two requirements:

- `FUN_0044A66C` examines troop WORDs across all twenty slots to find the last live slot; inactive origin/quality/name is not used by that function. `FUN_0044A698` sums all twenty troop WORDs and returns 1 if the sum is zero; it relies on the inactive troop markers themselves, without reading inactive names/quality. Neither is an audit of every consumer.
- `FUN_0044A218` scans **live regular** units' visible names while generating an unused numbered name; names are therefore gameplay inputs, not merely display text. Its string conversion/parser consume the visible string, not a demonstrated trailing-tail semantic.
- New army constructor initializes only 96/656 bytes, new fleet construction 10/26; fleet completion still leaves destinations/moves without an initialization policy. `FUN_0044D9A8` selects launched fleets under owner/carrier/countdown/move predicates and passes their destination field address to the route helper. A new native fleet cannot omit live movement/destination values merely because its building record once ignored them.
- Whole-record/slot/serializer copies preserve residue for byte identity. They do **not**, by themselves, prove canonical zero tails would alter gameplay. Conversely, the few NUL-based consumers do not prove all other consumers ignore tails. A canonical semantic policy needs that complete consumer/dependency proof, or an original constructor trajectory with a proved pre-allocation envelope. Neither is supplied by this tax-only profile.

Historical `+434/+43C/+448/+44E` is retained byte-for-byte from the bound source. This profile never substitutes DAT history or deduces origin from current totals/title. A source campaign's genuine history may be retained without claiming its origin matches the shipped DAT. Native-only/new objects and owner JSON without authentic envelope/provenance remain outside this profile.

## Smallest remaining evidence, and the native gate

This packet does not end with a generic request for more research. The finite remaining obligations for the tax profile are:

1. **Trusted import/edit binding:** actual exporter accepts source hash plus tax-only delta, or a complete native baseline/delta attestation covering every other state component. Required API decision belongs to the exporter; generic normalized equality is inadequate. The twelve native owner JSON inputs lack this envelope/history in the current evidence and are not converted by this profile.
2. **Close/UI composition:** trace the fresh-process original tax dialog through `004540DC → 0045BA6C → 00445D38/0043BA7C`, the posted `0042313C` close/pump boundary and subsequent `0045BB1C/004484D0` save. Required runtime scalars are selected-cell form `+21A`, army/fleet selectors `004A0328/2A`, actual width/height and scrollbar values, stable geometry and absence of unrelated queued/modal work. Source already identifies the nonidentity viewport and selected-action branches. A GUI-free instruction-prefix test cannot supply these scalars or claim that complete trace.
3. **Independent native Windows validation:** once the exporter implements this exact profile, obtain three actual distinct representative candidates from the owner-coordinated flow, e.g. bound tax=0, tax=40 and a third accepted profile/count case. Hash and preserve original envelope, native source/delta, candidate, distinct save-copy and reopen evidence. Open, inspect ordinary state, order/end-turn, save new copy and reopen in the original Windows game. Different original geometry must be recorded, not zeroed or conflated with gameplay changes.

The owner reports **“No candidates that I know of.”** This is knowledge of availability, not a filesystem-absence claim. Private native input locations and coordinated Windows runtime remain **UNVERIFIED**; research is handling the concrete candidate-generation bridge, so no owner search for known nonexistent candidates is requested. No game run or native gate was attempted; **zero** Windows round trips. No original/private input upload, other-repo/build/T177/task25 write or future RNG-equivalence claim. This is a finite candidate profile for implementer evaluation and new original-instruction evidence, with the remaining GUI/native obligations explicit; changed-state export readiness remains false.
