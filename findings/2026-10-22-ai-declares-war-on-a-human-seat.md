# An AI nation declares war on the human seat: seen once, after 14 turns of meeting the code's conditions; the human gets a news line only, no box

2026-10-22. **[confirmed]** for the event and what the human sees (one staged play, Wine); the 1-in-10 rate is **not**
measured. Run `run-exp-manual-gaps`, item B11. The rule (`docs/rules-digest.md` §7, research
`decompiled-ai-offers-to-human-seats.md` §1a) had no observation of an AI declaring war on a human seat.

## Answer

- **Code:** an AI seat declares war on a nation `k` only if it is at war with nobody, its mobilisation is ≤ 40 and the
  season is not Winter, `k` is a neighbour (mask `+0x46`), `0 ≤ rel[k][me] < 3`, `k` is not protected by an ally, and
  `8·P(me)/P(k) > 10` (the best such ratio is the target), with `P = wealth/20000 × unity/100`; then `Random(10) == 0`.
- **Staging** (`MG_B11_staged_carthage_celtiberia_-18.SAV`, from `run0-start-AUTO0720-seed12345.SAV`, one edit): Carthage's
  only war (Celtiberia) set to −18 (peace with the cooldown), so Carthage is at war with nobody and Celtiberia is no target.
  Carthage's other neighbours are excluded by the code (Numidia its ally; Ptolemaic −10); Rome (relation 0, no allies) is its
  only possible target. Unchanged start values: Carthage mobilisation 15, P 1,733; Rome P 1,058 (8 × ratio = 13.1).
- **Play** (seed build `354d8265…`, seed 12345; End turn only, Rome gave no orders):

  | Turn (autosave) | Season | Carthage → Rome | Carthage P / mob | Rome P | Note |
  |---|---|---:|---|---:|---|
  | 0720 (start) | Spring | 0 | 1,733 / 15 | 1,058 | conditions met |
  | 0721 .. 0733 | Spring, Summer, Autumn | 0 | 1,733 → 1,865 / 15 → 9 | 1,058 → 634 | 13 more turns with the conditions met and no declaration (Gaul, at war with Rome, took Roman cities meanwhile: Rome 25 → 16 cities) |
  | **0734** (`MG_B11_seed12345_AUTO0734.SAV`) | Autumn | **3** (both ways) | 1,865 / 13 | 634 | news **"CARTHAGE DECLARES WAR ON ROME."** under *Week 3 Autumn 270BC* |

  - The declaration happened in Carthage's seat after Rome ended turn 0733 (Week 3 Autumn), the 14th AI turn with the
    conditions met; 0.9^13 ≈ 25 %, so the wait is unremarkable for a 1-in-10 draw.
  - **What the human sees:** no message box at all. At the start of turn 0734 the Information panel's news list shows the line
    in capitals, like the human's own declarations (`MG_B11_seed12345_after_declaration_screen.png`). The only boxes of the
    run were End turn ? ("An army of yours needs supplies.") and turn-start trade offers.
  - Between `AUTO0733` and `AUTO0734` Rome's and Carthage's relation words changed 0 → 3 and nothing else of Carthage's
    relations changed (no ally drawn in: Rome has none) (`B11-0733-0734-diff.txt`; the other relation changes belong to
    Seleucid's conquest of Galatia the same turn).
  - Carthage's mobilisation rose 9 → 13 at the declaration turn.

## Addendum (2026-10-22, from research's intake, PR diegoami/imperial-conquest-2-research#59)

**Carthage's was not the first AI war on Rome in this run.** Illyria declared war first, between turns 0721 and 0722,
through an alliance. Rome–Illyria went from trade (1) to war (3) on both sides, and Gaul–Illyria from −8 to alliance (2),
checked in `MG_B11_seed12345_AUTO0721.SAV` → `MG_B11_seed12345_AUTO0722.SAV`. Research's news read is
"Illyria forms an alliance with Gaul." then "ILLYRIA DECLARES WAR ON ROME.". This is the AI alliance rule plus the
relation setter's one-step cascade: allying with Gaul, which is at war with Rome, puts Illyria at war with Rome.

So a human can be dragged into war in two ways: by an AI's own war rule (Carthage, above) or by an AI allying with one
of the human's enemies (Illyria). In both cases the human sees only news lines.

## What this does not establish

- One seed, one declaration: the 1-in-10 chance and the target choice by best ratio are consistent, not measured.
- The staging removed Carthage's natural war; in the unedited start Carthage is at war with Celtiberia and cannot declare.
- Whether Carthage's armies then attack Rome was not followed (the run stops at the declaration).

## Evidence

- `runs/experiments/data/run-exp-manual-gaps/`: `b11-war.jsonl` (per turn: both relation words, Carthage's wars, P and
  mobilisation of both, the boxes' OCR), `B11-0733-0734-diff.txt`, `staged-edits.jsonl`, `shots.csv`.
- Saves (Drive `IC2/artifacts/run-exp-manual-gaps/saves/`): `MG_B11_staged_carthage_celtiberia_-18.SAV` (`faf919b2a829…`),
  autosaves `MG_B11_seed12345_AUTO0721.SAV` .. `MG_B11_seed12345_AUTO0734.SAV` (hashes in `SAVES.sha256`).
