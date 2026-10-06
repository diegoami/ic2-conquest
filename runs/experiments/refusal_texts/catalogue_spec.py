"""The hand-read part of the catalogue: for each message-box call site (keyed by its call line in all_app_functions.txt) its id, kind, test order, condition (with
cited lines: `L<line> «<text of that line>»`, checked against the tracked code extract), effect, tag and play evidence. NO LITERAL IS TYPED HERE: the literal of a row is
read from the call site by draft_tables.py and re-read by claims_audit.py. For a message built at run time ('expr' sites) `tmpl` lists its pieces: ('var', description) or
('lit', line) = the string literal on that line of the extract.
Field meanings of the records are from docs/sav-layout-notes.md and research docs/reports/decompiled-unit-map-orders-and-record-fields.md (army +4 owner, +8 covered cell (-1 aboard),
+10 supplies, +12 purse, slot k at +16+32k with troops at +4k...; fleet +8 owner, +10 launch countdown (0xFFFF launched), +12 moves, +18 ships, +22 carried army (-1 none);
city +18 owner, +26 fortification; nation +0x26 relations (0 peace 1 trade 2 alliance 3 war, negative = cooldown), +0x2E4 recruitment slots, +0x442 mobilisation, +0x490 human)."""
def C(line, text): return 'L%d «%s»' % (line, text)

ROWS = []
def row(line, id, kind, grp, order, cond, effect, tag='[derived]', plays=(), tmpl=None, fn_note=''):
    ROWS.append(dict(line=line, id=id, kind=kind, grp=grp, order=order, cond=cond, effect=effect, tag=tag, plays=list(plays), tmpl=tmpl))

# ---------------------------------------------------------------- unit map: army orders
row(47042, 'R01', 'refusal', 'army order: Split army (UA04)', '1 of 1',
    'an own army is selected (%s) and its second unit slot is empty (%s; 0x47c220 = army +0x34 = slot 1 troops, 16 + 32 + 4): the army has one unit'
    % (C(47039, '(&DAT_0047c1f0)[sVar1 * 0x148] == DAT_004a0320'), C(47041, '(&DAT_0047c220)[sVar1 * 0x148] == 0')),
    'dropped: the Split army dialog does not open; nothing changes. (With 2 or more units the dialog opens; if no free tile is next to the army or 198 armies exist, FUN_00449f08 returns -1 and nothing happens, no box: %s)' % C(48725, '(-1 < (short)local_12) && (DAT_004a0324 < 0xc6)'),
    plays=['UA04'])
row(46978, 'R02', 'refusal', 'army order: Join armies (UA05)', '1 of 3',
    'the army has a partner (the last own army one tile away, FUN_00449d64 %s; no partner = no box) and one of the two is aboard a fleet: %s'
    % (C(48612, 'if ((sVar4 != param_1) && ((&DAT_0047c1f0)[param_1 * 0x148] == *psVar2)) {'), C(46976, '(&DAT_0047c1f4)[(short)uStack_10 * 0x148] == -1) ||')),
    'dropped: nothing merges', plays=['A01b'])
row(47011, 'R03', 'refusal', 'army order: Join armies (UA05)', '2 of 3',
    'not aboard, and the two armies together hold 21 or more units (the sum of FUN_0044a66c, the index of the last occupied slot + 1, fails %s)' % C(46984, '(int)(short)iVar2 + (int)(short)iVar3 < 0x15'),
    'dropped: nothing merges; shown BEFORE the troop test, so when both limits are exceeded this line appears', plays=['UA05a', 'UA05c'])
row(47006, 'R04', 'refusal', 'army order: Join armies (UA05)', '3 of 3',
    'at most 20 units, and the two armies together hold 100,001 or more troops (FUN_0044a698 sums the 20 slots; %s fails)' % C(46987, 'if (iVar2 + iVar3 < 0x186a1) {'),
    'dropped: nothing merges; 100,000 itself is allowed', plays=['UA05b'])
row(47102, 'R05', 'refusal', 'army order: Disband army', '1 of 1 (the prompt P01 follows when it passes)',
    'no own city within one tile of the army (FUN_004494e4 returns -1): %s' % C(47101, 'if (sVar2 == -1) {'),
    'dropped: the army is kept', plays=['S01'])
row(46595, 'R06', 'refusal', 'army order: embark (click an own fleet with an army selected)', 'alternative of R07 and of the attack prompts (a different click target)',
    'the selected army has 1 or more moves and the fleet is one tile away (bVar4, %s), the fleet carries no army (%s) and the fleet\'s ships are fewer than troops / 500 (%s)'
    % (C(46514, '(short)(&DAT_0047c1f2)[DAT_004a0328 * 0x148] < 1'), C(46592, '(&DAT_0049c282)[*(short *)(param_1 + 0x224) * 0xd] == -1'), C(46594, 'if ((int)(short)(&DAT_0049c27e)[*(short *)(param_1 + 0x224) * 0xd] < iVar6 / 500) {')),
    'dropped: nobody boards; the click leaves the fleet selected. The call passes type 3 (Confirmation) with an OK-only button set, so the box is titled Confirm', plays=['E01'])
row(46637, 'R07', 'refusal', 'fleet order: attack a fleet', 'alternative of R06 and of the attack prompts (a different click target)',
    'an own fleet with moves is one tile from an enemy fleet (%s) that is next to a city of its owner (FUN_004494e4 >= 0, else-branch of %s)'
    % (C(46611, 'else if (((DAT_004a032a < 0) || ((short)(&DAT_0049c278)[DAT_004a032a * 0xd] < 1)) ||'), C(46621, 'if (sVar5 < 0) {')),
    'dropped: no attack, no war declared')
# ---------------------------------------------------------------- unit map: mercenaries
row(46914, 'R08', 'refusal', 'army order: Recruit mercenaries (button)', '1 of 5',
    'the army is selected and a mercenary offer is one tile away (FUN_00449d08; none = no box) and its 20th slot is occupied: not (%s)' % C(46884, '*(short *)(&DAT_0047c460 + sVar1 * 0x290) < 1'),
    'dropped: the dialog does not open', plays=['M03'])
row(46910, 'R09', 'refusal', 'army order: Recruit mercenaries (button)', '2 of 5',
    'fewer than 20 units and the army already holds 100,001 or more troops: not (%s)' % C(46885, 'if (iVar2 < 0x186a1) {'),
    'dropped: the dialog does not open', plays=['M02'])
row(46888, 'R10', 'refusal', 'army order: Recruit mercenaries (button)', '3 of 5',
    'the offer\'s city owner is at war with the current nation: %s' % C(46887, '[(short)(&DAT_004795a2)[(short)local_14 * 0x11] * 0x24a + (int)DAT_004a0320] == 3) {'),
    'dropped: the dialog does not open', plays=['M04'])
row(46894, 'R11', 'refusal', 'army order: Recruit mercenaries (button)', '4 of 5',
    'supplies x 10000 / troops is below 15: %s' % C(46893, '< 0xf) {'),
    'dropped: the dialog does not open', plays=['M01'])
row(46904, 'R12', 'refusal', 'army order: Recruit mercenaries (button)', '5 of 5',
    'the army is aboard a fleet whose ships are fewer than troops / 500: the pass test is %s' % C(46899, '(iVar2 / 500 <= (int)(short)(&DAT_0049c27e)[(short)param_1[0x89] * 0xd])) {'),
    'dropped: the dialog does not open')
# ---------------------------------------------------------------- fleet orders
row(47179, 'R13', 'refusal', 'fleet order: Repair fleet', '1 of 2',
    'no own city within one tile of the fleet: %s' % C(47178, 'if (sVar2 == -1) {'),
    'dropped: the Repair fleet dialog does not open', plays=['F03b'])
row(47187, 'R14', 'refusal', 'fleet order: Repair fleet', '2 of 2',
    'near a city but the fleet carries an army: the pass test is %s' % C(47182, 'else if ((short)(&DAT_0049c282)[sVar1 * 0xd] < 0) {'),
    'dropped: the dialog does not open', plays=['F06'])
row(47260, 'R15', 'refusal', 'fleet order: Join fleets (UF05)', '1 of 2',
    'a partner fleet exists (same owner, launched, one tile away: FUN_00449dd8 %s) and the ships add up to 101 or more: the pass test is %s'
    % (C(48643, 'if (((sVar4 != param_1) && ((&DAT_0049c274)[param_1 * 0xd] == *psVar2)) &&'), C(47234, 'if ((short)(&DAT_0049c27e)[sVar1 * 0xd] + iVar2 < 0x65) {')),
    'dropped: nothing merges; shown BEFORE the army test', plays=['UF05b', 'UF05c'])
row(47237, 'R16', 'refusal', 'fleet order: Join fleets (UF05)', '2 of 2',
    'at most 100 ships together, and the partner (%s) or this fleet (%s) carries an army'
    % (C(47235, 'if (((ushort)(&DAT_0049c282)[(short)local_10 * 0xd] < 0x8000) ||'), C(47236, '(iVar2 = sVar1 * 0xd, -1 < (short)(&DAT_0049c282)[sVar1 * 0xd])) {')),
    'dropped: nothing merges', plays=['UF05'])
row(47293, 'R17', 'refusal', 'fleet order: Split fleet', '1 of 3',
    'the fleet has fewer than 20 ships: %s' % C(47292, 'if ((short)(&DAT_0049c27e)[iVar2 * 0xd] < 0x14) {'),
    'dropped: the Split fleet dialog does not open', plays=['F01'])
row(47309, 'R18', 'refusal', 'fleet order: Split fleet', '2 of 3',
    '20 or more ships and the fleet carries an army: the else of %s' % C(47296, 'else if ((short)(&DAT_0049c282)[iVar2 * 0xd] < 0) {'),
    'dropped: the dialog does not open', plays=['F02'])
row(47300, 'R19', 'refusal', 'fleet order: Split fleet', '3 of 3',
    '20 or more ships, no army aboard, and no free fleet slot or free sea tile (the callee leaves the new fleet index at -1): %s' % C(47299, 'if (sStack_8 == -1) {'),
    'dropped: nothing is created')
row(47341, 'R20', 'refusal', 'fleet order: Scuttle fleet', '2 of 2',
    'no army aboard (%s) and no own city within one tile: %s' % (C(47336, 'if ((short)(&DAT_0049c282)[iVar3 * 0xd] < 0) {'), C(47340, 'if (sVar2 == -1) {')),
    'dropped: the fleet is kept (when a city is near, the prompt P02 follows)', plays=['F04b'])
row(47362, 'R21', 'refusal', 'fleet order: Scuttle fleet', '1 of 2',
    'the fleet carries an army: the else of %s' % C(47336, 'if ((short)(&DAT_0049c282)[iVar3 * 0xd] < 0) {'),
    'dropped: the fleet is kept; shown BEFORE the city test', plays=['F05'])
# ---------------------------------------------------------------- city
row(47401, 'R22', 'refusal', 'city order: Fortify city', '1 of 3',
    'an own city is selected and an enemy army is next to it (FUN_004497cc returns 1): the else of %s' % C(47386, "if ((char)uVar2 == '\\0') {"),
    'dropped: the Fortify dialog does not open', plays=['C03'])
row(47388, 'R23', 'refusal', 'city order: Fortify city', '2 of 3',
    'not under siege and the fortification word equals 100: %s' % C(47387, 'if ((&DAT_004795aa)[sVar1 * 0x11] == 100) {'),
    'dropped: the dialog does not open', plays=['C01'])
row(47396, 'R24', 'refusal', 'city order: Fortify city', '3 of 3',
    'not under siege and the fortification word is 101 or more (a pending order is stored as 100 x points + fortification, e.g. 372): the else of %s' % C(47391, 'else if ((short)(&DAT_004795aa)[sVar1 * 0x11] < 0x65) {'),
    'dropped: the dialog does not open', plays=['C02'])
# ---------------------------------------------------------------- mercenary hire dialog
row(43637, 'R25', 'refusal', 'mercenary dialog: Recruit unit', '1 of 3',
    'the army\'s purse is smaller than the hire price: %s' % C(43633, 'if ((short)(&DAT_0047c1f8)[sVar4 * 0x148] <'),
    'dropped: the unit is not hired; the dialog stays open', plays=['MM01'])
row(43691, 'R26', 'refusal', 'mercenary dialog: Recruit unit', '2 of 3',
    'the army\'s troops plus the unit\'s troops would be 100,001 or more: the pass test is %s' % C(43644, '0x186a1) {'),
    'dropped: the unit is not hired', plays=['MM02'])
row(43652, 'R27', 'refusal', 'mercenary dialog: Recruit unit', '3 of 3',
    'the army is aboard a fleet (fleet index >= 0) whose ships are fewer than (troops + the unit) / 500: %s' % C(43648, 'if ((int)(short)(&DAT_0049c27e)[sVar4 * 0xd] <'),
    'dropped: the unit is not hired (the code returns)')
# ---------------------------------------------------------------- army to army transfer dialog
for (sfx, lines, c20, ctr, cfl) in (('Army1Transfer', (44155, 44159, 44164), C(44125, '*(short *)(param_1 + 0x750) < 1'), C(44128, 'if (iVar7 + iVar6 < 0x186a1) {'), C(44133, 'if (iVar6 < (iVar7 + *(short *)(param_1 + 0x260 + sVar9 * 0x20)) / 500) {')),
                                    ('Army2Transfer', (44236, 44240, 44245), C(44206, '*(short *)(param_1 + 0x4c0) < 1'), C(44209, 'if (iVar7 + iVar6 < 0x186a1) {'), C(44214, 'if (iVar6 < (iVar7 + *(short *)(param_1 + 0x4f0 + sVar9 * 0x20)) / 500) {'))):
    base = 'R28' if sfx == 'Army1Transfer' else 'R31'
    n = int(base[1:])
    row(lines[0], 'R%02d' % n, 'refusal', 'army to army dialog: Transfer (%s)' % sfx, '1 of 3 (per selected unit, last slot first; the boxes follow the loop)',
        'a selected unit meets a target army whose 20th slot is occupied: not (%s)' % c20,
        'clamped per unit: that unit stays; units that pass are still moved; the box is shown once after the loop')
    row(lines[1], 'R%02d' % (n + 1), 'refusal', 'army to army dialog: Transfer (%s)' % sfx, '2 of 3 (shown only when no unit hit the 20-unit test: else-if)',
        'the target\'s troops plus the unit\'s would be 100,001 or more: the pass test is %s' % ctr,
        'clamped per unit: that unit stays; the others are still moved')
    row(lines[2], 'R%02d' % (n + 2), 'refusal', 'army to army dialog: Transfer (%s)' % sfx, '3 of 3 (a separate box, after the two above)',
        'the target army is aboard a fleet whose ships are fewer than (troops + the unit) / 500: the pass test is %s' % cfl,
        'clamped per unit: that unit stays (the code jumps over the move)')
row(44326, 'R34', 'refusal', 'army to army dialog: Disband (Army1Disband)', 'after the prompt P06, once per order',
    'a regular unit (label 0, %s) is selected and no own city is next to the first army of the dialog (%s; +0x770 is set in TArmyToArmy_InitializeForm from that army\'s tile: %s)' % (C(44312, '(*(short *)(param_1 + 0x25c + sVar6 * 0x20) == 0)) {'), C(44311, 'if ((*(short *)(param_1 + 0x770) == -1) &&'), C(43793, 'uVar1 = FUN_004494e4((undefined *)')),
    'clamped: mercenary units of the selection are removed; regular units are kept; one box after the loop', plays=['TD01'])
row(44412, 'R35', 'refusal', 'army to army dialog: Disband (Army2Disband)', 'after the prompt P07, once per order',
    'a regular unit (label 0, %s) is selected and no own city is next to the FIRST army of the dialog (%s: the same word +0x770 as for the first list, set in TArmyToArmy_InitializeForm at %s)' % (C(44398, '(*(short *)(param_1 + 0x4ec + sVar6 * 0x20) == 0)) {'), C(44397, 'if ((*(short *)(param_1 + 0x770) == -1) &&'), C(43793, 'uVar1 = FUN_004494e4((undefined *)')),
    'clamped: mercenary units of the selection are removed; regular units are kept; one box after the loop', plays=['TD02'])
# ---------------------------------------------------------------- change units
row(45513, 'R36', 'refusal', 'Change units: Rename unit (D05)', '1 of 2',
    'two or more units are selected: the else of %s' % C(45487, 'if (iVar2 < 2) {'),
    'dropped: no Rename dialog', plays=['D05a'])
row(45507, 'R37', 'refusal', 'Change units: Rename unit (D05)', '2 of 2',
    'exactly one unit is selected and its label is not 0 (a mercenary): the else of %s' % C(45502, 'if (*(short *)(param_1 + 0x1ea + unaff_BP * 0x20) == 0) {'),
    'dropped: no Rename dialog', plays=['D05b'])
row(45577, 'R38', 'refusal', 'Change units: Split unit (D06)', '1 of 4',
    'two or more units are selected: the else of %s' % C(45539, 'if (iVar3 < 2) {'),
    'dropped', plays=['CU03'])
row(45572, 'R39', 'refusal', 'Change units: Split unit (D06)', '2 of 4',
    'one unit selected and its label is not 0 (mercenary): the else of %s' % C(45556, 'if (*psVar1 == 0) {'),
    'dropped', plays=['CU02'])
row(45568, 'R40', 'refusal', 'Change units: Split unit (D06)', '3 of 4',
    'a regular unit and the army\'s 20th slot is occupied: the else of %s' % C(45557, 'if (*(short *)(param_1 + 0x44e) < 1) {'),
    'dropped', plays=['CU01'])
row(45559, 'R41', 'refusal', 'Change units: Split unit (D06)', '4 of 4',
    'a regular unit, fewer than 20 units, and the unit\'s troops are below two fifths of its type\'s size limit: %s' % C(45558, 'if ((int)psVar1[2] < ((short)(&DAT_00478fca)[psVar1[1] * 0x14] * 2) / 5) {'),
    'dropped: no Split unit dialog', plays=['D06'])
row(45642, 'R42', 'refusal', 'Change units: Join units', '1 of 3',
    'two or more units are selected and one of them has a non-zero label (mercenary): %s sets the flag' % C(45634, 'bVar5 = true;'),
    'dropped', plays=['CU04'])
row(45678, 'R43', 'refusal', 'Change units: Join units', '2 of 3',
    'all selected units regular but not all of one type: %s clears the flag' % C(45629, 'if (sVar10 != psVar1[1]) {'),
    'dropped', plays=['CU05'])
row(45647, 'R44', 'refusal', 'Change units: Join units', '3 of 3',
    'all regular, one type, and the total troops exceed the type\'s size limit: %s' % C(45646, 'if ((short)(&DAT_00478fca)[sVar10 * 0x14] < iStack_18) {'),
    'dropped', plays=['CU06'])
row(45756, 'R45', 'refusal', 'Change units: Disband', 'after the prompt P08, once per order',
    'a selected unit is regular (%s) and no own city is next to the army (%s; +0x1d6 is set in TChangeArmyUnits_InitializeForm from the army\'s tile: %s)' % (C(45744, '(*(short *)(param_1 + 0x1ea + sVar5 * 0x20) == 0)) {'), C(45743, 'if ((*(short *)(param_1 + 0x1d6) == -1) &&'), C(45408, 'uVar2 = FUN_004494e4((undefined *)CONCAT22((short)((uint)(sVar1 * 0x52) >> 0x10),DAT_004a0320),')),
    'clamped: mercenary units of the selection are removed; regular units are kept; one box after the loop', plays=['CU07', 'CU08'])
# ---------------------------------------------------------------- recruitment
row(56033, 'R46', 'refusal', 'Recruit unit (dialog Army recruits)', '1 of 3',
    'the 40th recruitment slot is occupied (nation +0x420 = slot 39 troops): not (%s)' % C(55949, 'if (*(short *)(&DAT_00474a90 + DAT_004a0320 * 0x494) < 1) {'),
    'dropped: nothing is queued, no money taken', plays=['RC01'])
row(55952, 'R47', 'refusal', 'Recruit unit (dialog Army recruits)', '2 of 3',
    'the mobilisation rate (nation +0x442) is 100: %s' % C(55950, 'if ((&DAT_00474ab2)[DAT_004a0320 * 0x24a] == 100) {'),
    'dropped: nothing is queued', plays=['RC02'])
row(56026, 'R48', 'refusal', 'Recruit unit (dialog Army recruits)', '3 of 3',
    'the chosen city is not "All cities", its fortification is 74 or less and it is not the capital: the else of %s' % C(55957, '((sVar8 < 0) || (0x4a < (short)(&DAT_004795aa)[sVar8 * 0x11])) ||'),
    'dropped: nothing is queued (the list offers only qualifying cities, so this fires when the fortification fell after the list was filled)')
row(56092, 'R49', 'refusal', 'Recruit unit (dialog Army recruits): Mobilize', '1 of 1',
    'a selected unit is ready (state above 15, %s) and FUN_0044a4e0 found neither an army to join nor room for a new army (FUN_00449f08 needs a free tile and fewer than 198 armies, %s)'
    % (C(56076, 'if (0xf < (short)(&DAT_00474954)[DAT_004a0320 * 0x24a + iVar5 * 4]) {'), C(48725, '(-1 < (short)local_12) && (DAT_004a0326 < 0xc6)'.replace('004a0326', '004a0324'))),
    'clamped per unit: units that found a place are mobilised; the box is shown once after the loop')
# ---------------------------------------------------------------- relations
row(55177, 'R50', 'refusal', 'International relations: peace', '1 of 1',
    'the other nation is computer-controlled (%s) and is at war with the current nation (%s)' % (C(55170, "if (((&DAT_00474b00)[iVar1 * 0x494] == '\\0') &&"), C(55171, '((&DAT_00474696)[DAT_004a0320 * 0x24a + iVar1] == 3)) {')),
    'dropped: the callee reports failure (`*param_3 = 0`), so the new value is not applied; in play the box appears at the click on the radio, before OK, and the radio keeps its old value',
    plays=['RL01'], tmpl=[('var', 'nation name'), ('lit', 55174)])
row(55237, 'R51', 'refusal', 'International relations: trade', '1 of 3',
    'three nations are already marked for trade in the form: %s' % C(55235, 'if (sVar4 == 3) {'),
    'dropped: the callee reports failure (`*param_3 = 0`): the new value is not applied (the box appears at the radio click)', plays=['RL02'])
row(55248, 'R52', 'refusal', 'International relations: trade', '2 of 3',
    'the relation with the target is negative (a cooldown): %s' % C(55242, 'if ((short)(&DAT_00474696)[DAT_004a0320 * 0x24a + iVar3] < 0) {'),
    'dropped: the callee reports failure (`*param_3 = 0`): the new value is not applied (the box appears at the radio click)', plays=['RL03'], tmpl=[('var', 'nation name'), ('lit', 55245)])
row(55257, 'R53', 'refusal', 'International relations: trade', '3 of 3',
    'not negative, and either the target already has three trade partners (%s) or the relation is 2 or 3 (%s)' % (C(55229, 'if ((sVar2 == 3) && ((DAT_0049f00a != 1 || (param_2 != DAT_0049f008)))) {'), C(55250, 'else if (bVar1 || 1 < (short)(&DAT_00474696)[DAT_004a0320 * 0x24a + (int)param_2]) {')),
    'dropped: the callee reports failure (`*param_3 = 0`): the new value is not applied (the box appears at the radio click)', plays=['RL04'], tmpl=[('lit', 55252), ('var', 'nation name'), ('lit', 55254)])
row(55321, 'R54', 'refusal', 'International relations: alliance', '1 of 1',
    'the target is computer-controlled (%s) and one of: a pending war or a pending alliance with a nation at war (%s), the current nation is at war with anyone (%s), or the relation is negative (%s)'
    % (C(55310, "if ((&DAT_00474b00)[local_6 * 0x494] == '\\0') {"), C(55300, 'if (*(short *)(param_1 + 900 + sVar3 * 2) == 3) {'), C(55313, "if (((char)uVar2 == '\\0') &&"), C(55314, '(-1 < (short)(&DAT_00474696)[DAT_004a0320 * 0x24a + (int)local_6])) goto LAB_004531cd;')),
    'dropped: the callee reports failure (`*param_3 = 0`): the new value is not applied (the box appears at the radio click)', plays=['RL05'], tmpl=[('var', 'nation name'), ('lit', 55318)])
# ---------------------------------------------------------------- build fleet
row(58528, 'R55', 'refusal', 'Build fleet (Strategy menu or toolbar)', '1 of 3 (when no own fleet is under construction)',
    'no own city is a free coastal city (FUN_004496e0 returns -1, %s) and no own fleet is under construction (%s)' % (C(58526, 'if (sVar3 == -1) {'), C(58527, "if (cStack_5 == '\\0') {")),
    'dropped: the dialog does not open', plays=['BF01'])
row(58532, 'R56', 'refusal', 'Build fleet (Strategy menu or toolbar)', '2 of 3',
    'no free coastal city and at least one own fleet is under construction: the else of %s' % C(58527, "if (cStack_5 == '\\0') {"),
    'dropped: the dialog does not open (the notices N02 are shown first for each fleet under construction)')
row(58537, 'R57', 'refusal', 'Build fleet (Strategy menu or toolbar)', '3 of 3',
    'a free coastal city exists and the fleet table is full (the fleet count is 99): %s' % C(58536, 'else if (DAT_004a0326 == 99) {'),
    'dropped: the dialog does not open')
# ---------------------------------------------------------------- prompts (Yes / No / Cancel)
PR = []
def prompt(line, id, grp, cond, effect, plays=(), tmpl=None):
    ROWS.append(dict(line=line, id=id, kind='prompt', grp=grp, order='-', cond=cond, effect=effect, tag='[derived]', plays=list(plays), tmpl=tmpl))
prompt(47106, 'P01', 'army order: Disband army', 'the army is near an own city (the else of the test of R05)', 'Yes (result 6) disbands the army and returns its money and supplies to the nearest city: %s; No or Cancel: nothing' % C(47108, 'if (iVar4 == 6) {'), plays=['S02'])
prompt(47345, 'P02', 'fleet order: Scuttle fleet', 'no army aboard and an own city is next to the fleet', 'Yes (6) deletes the fleet and returns money and supplies to the city; No or Cancel: nothing', plays=['F04'])
prompt(46541, 'P03', 'unit map: attack a city', 'an own army with moves is next to a city of another nation that is not already at war with the current nation', 'Yes (6) sets the relation to 3 (war) and starts the attack; No or Cancel: nothing happens')
prompt(46566, 'P04', 'unit map: attack an army', 'an own army with moves is next to an army of another nation that is not at war', 'Yes (6) declares war and attacks; No or Cancel: nothing')
prompt(46623, 'P05', 'unit map: attack a fleet', 'an own fleet with moves is next to an enemy fleet not docked at its city (see R07) and not at war', 'Yes (6) declares war and attacks; No or Cancel: nothing')
prompt(44300, 'P06', 'army to army dialog: Disband (Army1Disband)', 'one or more units selected', 'Yes (6) removes the units, subject to R34; text built from the count', plays=['TD01'],
       tmpl=[('lit', 44287), ('var', 'number of selected units'), ('lit', 44292), ('lit', 44295), ('lit', 44297)])
prompt(44386, 'P07', 'army to army dialog: Disband (Army2Disband)', 'one or more units selected', 'Yes (6) removes the units, subject to R35; text built from the count', plays=['TD02'],
       tmpl=[('lit', 44373), ('var', 'number of selected units'), ('lit', 44378), ('lit', 44381), ('lit', 44383)])
prompt(45732, 'P08', 'Change units: Disband', 'one or more units selected', 'Yes (6) removes the units, subject to R45; text built from the count', plays=['CU07', 'CU08'],
       tmpl=[('lit', 45719), ('var', 'number of selected units'), ('lit', 45724), ('lit', 45727), ('lit', 45729)])
prompt(56146, 'P09', 'Army recruits: Disband (queued units)', 'one or more queued units selected', 'Yes (6) deletes them, no refund; text built from the count',
       tmpl=[('lit', 56133), ('var', 'number of selected units'), ('lit', 56138), ('lit', 56141), ('lit', 56143)])
prompt(58018, 'P10', 'Game: New game', 'the New game command', 'Yes (6) starts the new-game form')
prompt(58150, 'P11', 'Game: quit', 'closing the main window', 'Yes (6) quits')
prompt(58398, 'P12', 'Game: lead a different nation', 'the New nation command', 'Yes (6) hands the seat to another nation')
prompt(58425, 'P13', 'Game: abdicate', 'the Abdicate command', 'Yes (6) abdicates (see findings/2026-10-05-end-of-game-screens.md)')
# ---------------------------------------------------------------- notices (an OK box that is not a refusal)
def notice(line, id, grp, cond, effect, tmpl):
    ROWS.append(dict(line=line, id=id, kind='notice', grp=grp, order='-', cond=cond, effect=effect, tag='[derived]', plays=[], tmpl=tmpl))
notice(56327, 'N01', 'Build fleet dialog: OK', 'a fleet size above 0 was ordered', 'the order is accepted and the notice reports the city', [('lit', 56322), ('var', 'city name'), ('lit', 56324)])
notice(58517, 'N02', 'Build fleet command', 'one box per own fleet still under construction, before the refusals R55-R57', 'information only', [('lit', 58504), ('var', 'ships'), ('lit', 58508), ('var', 'weeks'), ('lit', 58512), ('var', 'city name'), ('lit', 58514)])
notice(58228, 'N03', 'start of a turn: a computer nation\'s offer', 'a nation that proposed trade or an alliance last turn has not got it', 'information only; the offer lapses at the next turn start; the word after `wants to` is the first literal (trade) or the second (form an alliance)', [('var', 'nation name'), ('lit', 58221), ('lit', 58215), ('lit', 58218), ('lit', 58223), ('var', 'nation name'), ('lit', 58225)])
# ---------------------------------------------------------------- excluded
ROWS.append(dict(line=37891, id='X01', kind='excluded', grp='battle screen: Surrender', order='-', cond='the Surrender command of the tactical battle', effect='excluded by the task: battles are paused', tag='[derived]', plays=[], tmpl=None))

# plays that evidence rows made in loops above (the left Transfer button is Army1Transfer: it moves units from the first list to the second, TArmyToArmy_MoveUnit(param_1, param_1 + 0x24c, param_1 + 0x4dc, ...) at L44138;
# the right button is Army2Transfer, from the second list to the first, L44219). The box text is the same literal for both functions: the play shows the line, the button shows the function.
for _id, _p in {'R28': ['T01'], 'R29': ['T02'], 'R30': ['TR3b'], 'R31': ['T01r'], 'R32': ['T02r']}.items():
    next(r for r in ROWS if r['id'] == _id)['plays'] = _p
