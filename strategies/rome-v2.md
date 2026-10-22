---
id: rome-v2
nation: Rome
author: player (diegoami), 2026-10-22
status: proposed          # proposed -> accepted -> in-trial -> validated | refuted | revised
start: new game, Rome human, default DAT (270 BC Spring week 1)
parent: rome-v1 (run 0, runs/0/debrief.md)
---

# Rome v2: recruit without limit, in debt if needed; never lose the armies

## Player's intent (in the player's words, not edited by the bot)

Everything in `strategies/rome-v1.md` ("Player's intent") still applies. Added 2026-10-22, after run 0:

I Do not worry too much about losing a few town, as long as you do not lose your armies.  Recruit like there is no tomorrow from the beginning, raise taxes, go into debt, evn massivley so. A second army is not a bad idea because recruiting takes a lot of time and then either they declare war on you or you on them.

*The player's answers to the bot's questions (2026-10-22):* keep a margin of **1,000 talents above the debt line**; tax **25 %**.

## Principles (checkable rules the bot must follow)

rome-v1's P1–P7 stay, with run 0's corrections (P1 uses the real melee matrix, DAT `0x1F7A6`). New or changed:

| # | Principle | How the bot checks it from the save |
|---|---|---|
| P1′ | Attack a field army only at matchup strength ≥ k × the defender's, **k = 5** (run 0 calibration; k = 3 only if the battle destroys the enemy's last army). Compute the ratio after any joins | every attack order logs both strengths and the ratio |
| P8 | **The armies come first, the towns second**: never trade an army for a town. A town may be left to the enemy if holding it would risk an army | every turn: no army is left where an enemy army of more than 1/k of its strength can reach it next turn, unless it is the planned battle |
| P9 | **Recruit like there is no tomorrow from turn 1**: every recruiting city queues units every turn while money and mobilisation allow | the queue is never below what the treasury and mobilisation allow; the reason for every unused recruiting turn is logged |
| P10 | **Spend into debt down to the debt line + 1,000**: the line is −(wealth div 500) talents, below which the game deposes the human leader | before every spending order: treasury after the order ≥ −(wealth div 500) + 1,000, with wealth read from the current save |
| P11 | **Tax 25 %** | the nation's tax field is 25 from turn 1 |
| P12 | **A second army** from early on, so that a war (theirs or ours) never finds Rome with one army | from the first mobilisations: two field armies; the second guards the south (Carthage declared war on Rome in Summer in run 0 and in the B11 staging) |

---

## Bot validation (written by the bot before the run)

Numbers from `saves/run0-start-AUTO0720-seed12345.SAV` (turn 0720) and run 0's `AUTO0744.SAV`, rules from `docs/rules-digest.md` (corrected 2026-10-22) and `findings/`.

| # | Supported by | What it means in numbers | Gap or risk |
|---|---|---|---|
| P10 | The deposition test (`findings/2026-10-12-g4-followups.md`, code `FUN_00452034`): at the start of each human turn, the leader is deposed if the treasury is below the debt line −(wealth div 500), or if unity < 400 | Start: wealth 2,577,000 → line −5,154 → **floor −4,154**. After run 0's conquests wealth was 3,051,000 → floor −5,102. Spendable at the start: 2,200 + 4,154 ≈ **6,350 talents** | Upkeep is billed with no balance check (`docs/rules-digest.md` §3), so a quarter's bill can push the treasury past the floor by itself: the margin must cover the next quarter's net bill. A lost city lowers wealth (pop × 3,000) and so raises the line |
| P9 | Recruit cost (DAT unit table): LI 15,000 for 150, HI 6,000 for 600, archers 3,500 for 68, LC 7,000 for 525, HC 2,500 for 360. Each order raises mobilisation by 1 + troops × 1,000 div wealth (cap 100, then refused) | Mobilisation starts at 30: a full LI battalion adds 6, HI 3, archers 2. **About 70 points of room** ≈ 11 full LI battalions or 23 HI | **Mobilisation is the real cap, not money**: 100 % refuses every order. High mobilisation also cuts every city's supply production (× (1 − mob/200), halved at 100) and population growth, and drains unity. It decays by only 3 a quarter |
| P11 | Unity per quarter: + 25 − tax/2 − mob/5 (capped 300..990); loyalty −Random(tax) div 8 with a 1-in-3 chance per city per quarter | At 25 % and mobilisation 100: −20 a quarter; from 821 that is about 21 quarters to the 400 line. Each capture +9, each loss −15 | Income at 25 %: tax ≈ 616 + tribute 632 − cities 175 − wealth 128 + trade ≈ **+950 a quarter before upkeep**, against ≈ +700 at 10 %. Captured cities (loyalty 41–55 in run 0) slide further |
| P12 | Run 0: Carthage declared war between 0727 and 0728 and landed 28,800 troops by sea on 0737 | A second army of about 20,000 (HI + archers) mobilised at Rome by 0726 | Every army needs supplies: two armies in Winter need about twice the city stock (rules-digest §2) |

**Proposed for the run (bot):** HI and archers for the field armies (they beat Gaul's LI: matrix HI→LI 60, archers ×3 in sieges), LI as cheap mass where the money runs short (150 talents per 15,000); recruit at Rome, Luceria and Arretium (fortified to 75 on turn 1 as in run 0).
