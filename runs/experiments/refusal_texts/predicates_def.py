#!/usr/bin/env python3
"""The refusal, prompt and notice conditions as structured predicates, read from the code extract on their own (issue #58).

This file is the hand reading of code_extract_refusals.v2.txt (first column = line of all_app_functions.txt): for every row of the
finding's catalogue, the tests on the path to its message box (function, test line, the outcome taken, and the comparison of each
atom: variable, operator, constant, the atom's value when the box shows), the effect (what the order does instead of acting, and the
line that would have acted), and for the prompts the answer test and what each answer does. It was written from the code, not from
the catalogue's prose; predicate_audit.py checks every entry against the code (each test, outcome and path; each atom's operator
and constant; flags, gotos and short-circuits; effects; answers), then compares the catalogue with it.

Run: python3 predicates_def.py [--out FILE]   writes predicates-vN.json (the next free version, exclusive create) under
runs/experiments/data/run-exp-refusal-audit58/. Standard library only.

Vocabulary.
 guard: {line, fn, out, role, deciding, reached, kind, combine, atoms, flag, means, cite}
   line      the test's `if` line (a continuation line is mapped to it); for kind 'dataflow' the line cited
   out       True = the then-branch is taken on the way to the box, False = the else-branch (the box needs the test FALSE)
   role      'context' (the order needs it at all: its other branch has no box, the order silently does nothing),
             'target'  (which tile was clicked: SelectUnit dispatches on it), 'answer' (a prompt's answer, see that prompt's row),
             'decisive' (part of the refusal's condition), 'structure' (an if-statement before the box that it falls through)
   deciding  the test that sends this row's box apart from the order's success (the row's own test)
   reached   the line whose path the guard is on (default: the box's call line); a flag's set line, a callee's line
   kind      'if' (an enclosing test), 'sc' (a short-circuit operand of the condition that holds the box call), 'goto' (an if whose
             then-branch jumps over the box, or to a flag's set label), 'pre' (an if-statement before the box in its block),
             'dataflow' (a value computed elsewhere: only its citation is checked)
   combine   how the atoms make `out`: 'and' / 'or' (None = a single atom)
   atoms     [{code, var, op, const, value, check, rel, tokens}]: code is a substring of the condition (whitespace normalised);
             op the operator as written; const the constant as a number (None when both sides vary); value = the atom's truth
             value when the box shows; check = the phrase test the audit applies to the catalogue ('number', 'concept:<name>',
             'rel' or None); rel = (lhs words, operator, rhs words) for 'rel'; tokens = regexes that the cell must contain
   flag      {name, set, value}: the guard tests a flag; `set` is the line that sets it, `value` what it is set to
 effect: {kind, action, reports_failure, loop, flag_set, note}
   kind 'drop'  (the box branch does nothing else; `action` = the lines that carry the order out, on another branch)
        'clamp' (the box follows a per-unit loop: units that pass are acted on in the loop, `action`; the failing ones set `flag_set`)
        'notice_after_action' (the order is carried out before the box: `action`), 'info' (the box reports, nothing else)
 answers (prompts): {test, yes, op, yes_kind, yes_actions, other_actions, after}
   test the line comparing the box's result; yes = 6 (mrYes); op '==' (act on Yes) or '!=' (leave unless Yes); yes_kind 'then' or
   'after_return'; yes_actions / other_actions / after = [{line, what, concept}] (after = runs whatever the answer)
"""
import argparse, json, os, sys, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
DATA = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-refusal-audit58')
EXTRACT = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-refusal-texts', 'code_extract_refusals.v2.txt')


def A(code, var, op=None, const=None, value=True, check=None, rel=None, tokens=None, line=None):
    return {'code': code, 'var': var, 'op': op, 'const': const, 'value': value, 'check': check, 'rel': rel, 'tokens': tokens or [], 'line': line}


def G(line, out, role='decisive', deciding=False, reached=None, fn=None, kind='if', combine=None, atoms=(), flag=None, means='', cite=None):
    return {'line': line, 'out': out, 'role': role, 'deciding': deciding, 'reached': reached, 'fn': fn, 'kind': kind,
            'combine': combine, 'atoms': list(atoms), 'flag': flag, 'means': means, 'cite': cite or [line]}


def C(line, means='', role='context', **kw):
    return G(line, kw.pop('out', True), role=role, means=means, **kw)


def F(name, set_line, value='true', via=None):
    return {'name': name, 'set': set_line, 'value': value, 'via': via}


def E(kind, action=(), reports_failure=None, loop=None, flag_set=None, note=''):
    return {'kind': kind, 'action': list(action), 'reports_failure': reports_failure, 'loop': loop, 'flag_set': flag_set, 'note': note}


def R(id_, table, fn, call, guards, effect=None, answers=None, alts=None, note=''):
    return {'id': id_, 'table': table, 'function': fn, 'call': call, 'paths': alts if alts else [guards], 'effect': effect,
            'answers': answers, 'note': note}


def ANS(test, op, yes_kind, yes_actions, other_actions=(), after=()):
    return {'test': test, 'yes': 6, 'op': op, 'yes_kind': yes_kind, 'yes_actions': list(yes_actions), 'other_actions': list(other_actions), 'after': list(after)}


def act(line, what, concept=None):
    return {'line': line, 'what': what, 'concept': concept}


# ------------------------------------------------------------------------------------------------ shared atoms
NO_CITY = 'concept:no_own_city'
HAS_ARMY = 'concept:fleet_has_army'
NUMBER = 'number'

ROWS = []
add = ROWS.append

# ======================================================================== TUnitMap (the map's order buttons)
add(R('R01', 'catalogue', 'TUnitMap_SplitArmy', 47042, [
    C(47039, 'an own army is selected', atoms=[A('(&DAT_0047c1f0)[sVar1 * 0x148] == DAT_004a0320', 'army.owner == current nation', '==')]),
    G(47041, True, deciding=True, atoms=[A('(&DAT_0047c220)[sVar1 * 0x148] == 0', 'army slot 1 troops (army +0x34)', '==', 0, True, 'concept:slot1_empty')],
      means='the second unit slot is empty: the army has one unit')],
    E('drop', [47046, 47048], note='with 2+ units FUN_00449f08 makes the new army and the Split army dialog opens')))

add(R('R02', 'catalogue', 'TUnitMap_JoinArmies', 46978, [
    C(46972, 'an own army is selected'),
    C(46975, 'a partner exists: the last own army one tile away (FUN_00449d64); none = nothing happens'),
    G(46976, True, deciding=True, combine='or', atoms=[
        A('(&DAT_0047c1f4)[(short)uStack_10 * 0x148] == -1', 'partner covered cell (army +8; -1 = aboard)', '==', -1, True, 'concept:aboard'),
        A('(&DAT_0047c1f4)[sVar1 * 0x148] == -1', 'army covered cell (army +8)', '==', -1, True, 'concept:aboard')],
      means='either army is aboard a fleet', cite=[46976, 46977])],
    E('drop', [46989, 46996])))

add(R('R03', 'catalogue', 'TUnitMap_JoinArmies', 47011, [
    C(46972, 'an own army is selected'), C(46975, 'a partner exists'),
    G(46976, False, combine='or', atoms=[
        A('(&DAT_0047c1f4)[(short)uStack_10 * 0x148] == -1', 'partner aboard', '==', -1, False, 'concept:aboard'),
        A('(&DAT_0047c1f4)[sVar1 * 0x148] == -1', 'army aboard', '==', -1, False, 'concept:aboard')], means='neither is aboard', cite=[46976, 46977]),
    G(46984, False, deciding=True, atoms=[A('(int)(short)iVar2 + (int)(short)iVar3 < 0x15', 'units(army) + units(partner) (FUN_0044a66c: last occupied slot + 1)', '<', 21, False, NUMBER)])],
    E('drop', [46989, 46996])))

add(R('R04', 'catalogue', 'TUnitMap_JoinArmies', 47006, [
    C(46972, 'an own army is selected'), C(46975, 'a partner exists'),
    G(46976, False, combine='or', atoms=[
        A('(&DAT_0047c1f4)[(short)uStack_10 * 0x148] == -1', 'partner aboard', '==', -1, False, 'concept:aboard'),
        A('(&DAT_0047c1f4)[sVar1 * 0x148] == -1', 'army aboard', '==', -1, False, 'concept:aboard')], cite=[46976, 46977]),
    G(46984, True, atoms=[A('(int)(short)iVar2 + (int)(short)iVar3 < 0x15', 'units together', '<', 21, True, NUMBER)]),
    G(46987, False, deciding=True, atoms=[A('iVar2 + iVar3 < 0x186a1', 'troops(army) + troops(partner) (FUN_0044a698)', '<', 100001, False, NUMBER)])],
    E('drop', [46989, 46996])))

add(R('R05', 'catalogue', 'TUnitMap_DisbandArmy', 47102, [
    C(47096, 'an own army is selected'),
    G(47101, True, deciding=True, atoms=[A('sVar2 == -1', 'own city within one tile of the army (FUN_004494e4; -1 = none)', '==', -1, True, NO_CITY)])],
    E('drop', [47106], note='with a city near, the prompt P01 is the next step')))

BVAR4_DEF = G(46514, False, reached=46520, combine='or', atoms=[
    A('DAT_004a0328 < 0', 'an army is selected for a move', '<', 0, False),
    A('(short)(&DAT_0047c1f2)[DAT_004a0328 * 0x148] < 1', 'that army\'s moves (army +6)', '<', 1, False, 'concept:no_moves'),
    A('!bVar4', 'FUN_004492a0: the clicked tile is one tile from the army', None, None, False)],
    means='bVar4 = an army is selected, has 1 or more moves and is one tile from the clicked tile', cite=[46514, 46516])

add(R('R06', 'catalogue', 'TUnitMap_SelectUnit', 46595, [
    BVAR4_DEF,
    C(46532, 'the clicked tile is not a city', role='target', out=False),
    C(46555, 'nor an army', role='target', out=False),
    C(46582, 'it is a fleet', role='target'),
    G(46590, True, atoms=[A('uVar2 == DAT_004a0320', 'fleet owner == current nation', '==')], means='an own fleet'),
    G(46592, True, combine='and', atoms=[
        A('bVar4', 'the selected army can board (see 46514)', None, None, True),
        A('(&DAT_0049c282)[*(short *)(param_1 + 0x224) * 0xd] == -1', 'fleet carried army (fleet +0x16; -1 = none)', '==', -1, True, 'concept:fleet_no_army')]),
    G(46594, True, deciding=True, atoms=[A('(int)(short)(&DAT_0049c27e)[*(short *)(param_1 + 0x224) * 0xd] < iVar6 / 500', 'fleet ships (fleet +0x12) vs army troops / 500', '<', None, True, 'rel', rel=['ships', '<', 'troops / 500'], tokens=[r'500'])])],
    E('drop', [46601], note='the click leaves the fleet selected (L46591) and the army unselected (L46608), as on the boarding path')))

add(R('R07', 'catalogue', 'TUnitMap_SelectUnit', 46637, [
    C(46532, 'not a city', role='target', out=False), C(46555, 'not an army', role='target', out=False), C(46582, 'a fleet', role='target'),
    G(46590, False, atoms=[A('uVar2 == DAT_004a0320', 'fleet owner == current nation', '==', None, False)], means='the clicked fleet is not own'),
    G(46611, False, combine='or', atoms=[
        A('DAT_004a032a < 0', 'an own fleet is selected', '<', 0, False),
        A('(short)(&DAT_0049c278)[DAT_004a032a * 0xd] < 1', 'selected fleet moves (fleet +0xc)', '<', 1, False, 'concept:no_moves'),
        A('!bVar4', 'FUN_004492a0: one tile apart', None, None, False)],
      means='an own fleet with moves is selected one tile away', cite=[46611, 46613]),
    G(46621, False, deciding=True, atoms=[A('sVar5 < 0', 'a city of the clicked fleet\'s owner within one tile (FUN_004494e4)', '<', 0, False, 'concept:no_owner_city')])],
    E('drop', [46627, 46629])))

# ---------------------------------------------------------------------- Recruit mercenaries (map button)
MERC_CTX = [C(46878, 'an own army is selected (or the army aboard the selected fleet)'),
            C(46882, 'a mercenary offer is one tile away (FUN_00449d08); none = nothing happens')]
SLOT19 = lambda v: A('*(short *)(&DAT_0047c460 + sVar1 * 0x290) < 1', 'army slot 19 troops (army +0x274)', '<', 1, v, 'concept:slot19_free')
add(R('R08', 'catalogue', 'TUnitMap_RecruitMercenaries', 46914, MERC_CTX + [
    G(46884, False, deciding=True, atoms=[SLOT19(False)])], E('drop', [46900])))
add(R('R09', 'catalogue', 'TUnitMap_RecruitMercenaries', 46910, MERC_CTX + [
    G(46884, True, atoms=[SLOT19(True)]),
    G(46885, False, deciding=True, atoms=[A('iVar2 < 0x186a1', 'army troops (FUN_0044a698)', '<', 100001, False, NUMBER)])], E('drop', [46900])))
WAR_OFFER = lambda v: A('[(short)(&DAT_004795a2)[(short)local_14 * 0x11] * 0x24a + (int)DAT_004a0320] == 3', 'relation of the offer city\'s owner to the current nation (3 = war)', '==', 3, v, 'concept:war')
add(R('R10', 'catalogue', 'TUnitMap_RecruitMercenaries', 46888, MERC_CTX + [
    G(46884, True, atoms=[SLOT19(True)]), G(46885, True, atoms=[A('iVar2 < 0x186a1', 'army troops', '<', 100001, True, NUMBER)]),
    G(46886, True, deciding=True, atoms=[WAR_OFFER(True)], cite=[46886, 46887])], E('drop', [46900])))
SUPPLY = lambda v: A('((short)(&DAT_0047c1f6)[sVar1 * 0x148] * 10000) / iVar2 < 0xf', 'army supplies (army +0xa) x 10000 / troops', '<', 15, v, NUMBER)
add(R('R11', 'catalogue', 'TUnitMap_RecruitMercenaries', 46894, MERC_CTX + [
    G(46884, True, atoms=[SLOT19(True)]), G(46885, True, atoms=[A('iVar2 < 0x186a1', 'army troops', '<', 100001, True, NUMBER)]),
    G(46886, False, atoms=[WAR_OFFER(False)], cite=[46886, 46887]),
    G(46893, True, deciding=True, atoms=[SUPPLY(True)])], E('drop', [46900])))
add(R('R12', 'catalogue', 'TUnitMap_RecruitMercenaries', 46904, MERC_CTX + [
    G(46884, True, atoms=[SLOT19(True)]), G(46885, True, atoms=[A('iVar2 < 0x186a1', 'army troops', '<', 100001, True, NUMBER)]),
    G(46886, False, atoms=[WAR_OFFER(False)], cite=[46886, 46887]), G(46893, False, atoms=[SUPPLY(False)]),
    G(46898, False, deciding=True, combine='or', atoms=[
        A('(short)param_1[0x89] < 0', 'a fleet is selected (the army is aboard it)', '<', 0, False, 'concept:not_aboard_fleet'),
        A('iVar2 / 500 <= (int)(short)(&DAT_0049c27e)[(short)param_1[0x89] * 0xd]', 'troops / 500 vs the fleet\'s ships', '<=', None, False, 'rel', rel=['ships', '<', 'troops / 500'], tokens=[r'500'])],
      cite=[46898, 46899])], E('drop', [46900])))

# ---------------------------------------------------------------------- fleets
OWN_FLEET = lambda ln: C(ln, 'an own fleet is selected')
add(R('R13', 'catalogue', 'TUnitMap_RepairFlt', 47179, [
    OWN_FLEET(47174),
    G(47178, True, deciding=True, atoms=[A('sVar2 == -1', 'own city within one tile of the fleet (FUN_004494e4)', '==', -1, True, NO_CITY)])], E('drop', [47183])))
add(R('R14', 'catalogue', 'TUnitMap_RepairFlt', 47187, [
    OWN_FLEET(47174),
    G(47178, False, atoms=[A('sVar2 == -1', 'own city near', '==', -1, False, NO_CITY)]),
    G(47182, False, deciding=True, atoms=[A('(short)(&DAT_0049c282)[sVar1 * 0xd] < 0', 'fleet carried army (fleet +0x16)', '<', 0, False, 'concept:fleet_no_army')])], E('drop', [47183])))
add(R('R15', 'catalogue', 'TUnitMap_JoinFleets', 47260, [
    OWN_FLEET(47229), C(47232, 'a partner fleet exists: same owner, launched, one tile away (FUN_00449dd8); none = nothing happens'),
    G(47234, False, deciding=True, atoms=[A('(short)(&DAT_0049c27e)[sVar1 * 0xd] + iVar2 < 0x65', 'ships(fleet) + ships(partner)', '<', 101, False, NUMBER)])], E('drop', [47242, 47249])))
add(R('R16', 'catalogue', 'TUnitMap_JoinFleets', 47237, [
    OWN_FLEET(47229), C(47232, 'a partner fleet exists'),
    G(47234, True, atoms=[A('(short)(&DAT_0049c27e)[sVar1 * 0xd] + iVar2 < 0x65', 'ships together', '<', 101, True, NUMBER)]),
    G(47235, True, deciding=True, combine='or', atoms=[
        A('(ushort)(&DAT_0049c282)[(short)local_10 * 0xd] < 0x8000', 'partner carried army read unsigned (< 0x8000 = an index >= 0)', '<', 0x8000, True, HAS_ARMY),
        A('-1 < (short)(&DAT_0049c282)[sVar1 * 0xd]', 'this fleet\'s carried army', '<', -1, True, HAS_ARMY)],
      cite=[47235, 47236])], E('drop', [47242, 47249])))
SHIPS20 = lambda v: A('(short)(&DAT_0049c27e)[iVar2 * 0xd] < 0x14', 'fleet ships', '<', 20, v, NUMBER)
FLEET_ARMY_SPLIT = lambda v: A('(short)(&DAT_0049c282)[iVar2 * 0xd] < 0', 'fleet carried army', '<', 0, v, 'concept:fleet_no_army')
add(R('R17', 'catalogue', 'TUnitMap_SplitFleet', 47293, [OWN_FLEET(47289), G(47292, True, deciding=True, atoms=[SHIPS20(True)])], E('drop', [47297, 47304])))
add(R('R18', 'catalogue', 'TUnitMap_SplitFleet', 47309, [OWN_FLEET(47289), G(47292, False, atoms=[SHIPS20(False)]),
    G(47296, False, deciding=True, atoms=[FLEET_ARMY_SPLIT(False)])], E('drop', [47297, 47304])))
add(R('R19', 'catalogue', 'TUnitMap_SplitFleet', 47300, [OWN_FLEET(47289), G(47292, False, atoms=[SHIPS20(False)]),
    G(47296, True, atoms=[FLEET_ARMY_SPLIT(True)]),
    G(47297, None, kind='dataflow', means='func_0x00447c04 writes the new fleet index into sStack_8, -1 when it cannot make one'),
    G(47299, True, deciding=True, atoms=[A('sStack_8 == -1', 'the new fleet index', '==', -1, True, 'concept:no_new_fleet')])], E('drop', [47304])))
FLEET_ARMY_SCUT = lambda v: A('(short)(&DAT_0049c282)[iVar3 * 0xd] < 0', 'fleet carried army', '<', 0, v, 'concept:fleet_no_army')
add(R('R20', 'catalogue', 'TUnitMap_ScuttleFleet', 47341, [OWN_FLEET(47334), G(47336, True, atoms=[FLEET_ARMY_SCUT(True)]),
    G(47340, True, deciding=True, atoms=[A('sVar2 == -1', 'own city within one tile of the fleet', '==', -1, True, NO_CITY)])], E('drop', [47345])))
add(R('R21', 'catalogue', 'TUnitMap_ScuttleFleet', 47362, [OWN_FLEET(47334), G(47336, False, deciding=True, atoms=[FLEET_ARMY_SCUT(False)])], E('drop', [47345])))

# ---------------------------------------------------------------------- Fortify
OWN_CITY = C(47384, 'an own city is selected')
SIEGE = lambda v: A("(char)uVar2 == '\\0'", 'FUN_004497cc: an army at war with the city\'s owner is next to it (returns 1)', '==', 0, v, 'concept:not_besieged')
add(R('R22', 'catalogue', 'TUnitMap_Fortify', 47401, [OWN_CITY, G(47386, False, deciding=True, atoms=[SIEGE(False)])], E('drop', [47392])))
add(R('R23', 'catalogue', 'TUnitMap_Fortify', 47388, [OWN_CITY, G(47386, True, atoms=[SIEGE(True)]),
    G(47387, True, deciding=True, atoms=[A('(&DAT_004795aa)[sVar1 * 0x11] == 100', 'city fortification word (city +0x1a)', '==', 100, True, NUMBER)])], E('drop', [47392])))
add(R('R24', 'catalogue', 'TUnitMap_Fortify', 47396, [OWN_CITY, G(47386, True, atoms=[SIEGE(True)]),
    G(47387, False, atoms=[A('(&DAT_004795aa)[sVar1 * 0x11] == 100', 'fortification word', '==', 100, False, NUMBER)]),
    G(47391, False, deciding=True, atoms=[A('(short)(&DAT_004795aa)[sVar1 * 0x11] < 0x65', 'fortification word', '<', 101, False, NUMBER)])], E('drop', [47392])))

# ======================================================================== TRecruitMercs (the hire dialog)
MERC_ROW = C(43630, 'an offer row is chosen in the dialog')
add(R('R25', 'catalogue', 'TRecruitMercs_RecruitMercUnit', 43637, [MERC_ROW,
    G(43633, True, deciding=True, atoms=[A('(short)(&DAT_0047c1f8)[sVar4 * 0x148] <', 'army money (army +0xc) vs the hire price', '<', None, True, 'rel', rel=['purse', '<', 'price'])], cite=[43633])],
    E('drop', [43662])))
TROOPS_MM = lambda v: A('0x186a1', 'army troops + the unit\'s troops', '<', 100001, v, NUMBER)
add(R('R26', 'catalogue', 'TRecruitMercs_RecruitMercUnit', 43691, [MERC_ROW,
    G(43633, False, atoms=[A('(short)(&DAT_0047c1f8)[sVar4 * 0x148] <', 'purse vs price', '<', None, False)]),
    G(43642, False, deciding=True, atoms=[A('iVar3 + *(short *)(&DAT_0049d0ac + *(short *)(param_1 + 0x1dc + *(short *)(param_1 + 0x1da) * 2) * 0xc) < 0x186a1', 'army troops + the unit\'s troops', '<', 100001, False, NUMBER)], cite=[43642, 43644])],
    E('drop', [43662])))
add(R('R27', 'catalogue', 'TRecruitMercs_RecruitMercUnit', 43652, [MERC_ROW,
    G(43633, False, atoms=[A('(short)(&DAT_0047c1f8)[sVar4 * 0x148] <', 'purse vs price', '<', None, False)]),
    G(43642, True, atoms=[A('< 0x186a1', 'troops together', '<', 100001, True, NUMBER)], cite=[43642, 43644]),
    G(43646, True, atoms=[A('-1 < sVar4', 'the fleet the army is aboard (dialog +0x1d8)', '<', -1, True, 'concept:aboard_fleet')]),
    G(43648, True, deciding=True, atoms=[A('(int)(short)(&DAT_0049c27e)[sVar4 * 0xd] <', 'fleet ships vs (troops + the unit) / 500', '<', None, True, 'rel', rel=['ships', '<', '(troops + unit) / 500'], tokens=[r'500'])], cite=[43648])],
    E('drop', [43662], note='the box branch returns (L43655)')))

# ======================================================================== TArmyToArmy (transfer and disband between two armies)
def transfer(rid, fn, call, base, src, tgt20, fleet_word, sets, which, deciding_line, action):
    """sets = (line of bVar2 = true, bVar3 = true, bVar4 = true); which: 0 = 20 units, 1 = 100,000 troops, 2 = fleet capacity"""
    sel, loop_tests = base
    ctx = [C(sel, 'one or more units are selected')]
    t_slot, t_sel, t_20, t_troops, t_fleet, t_cap = loop_tests
    flag_test = {0: (call - 1, 'bVar2'), 1: (call - 1, 'bVar3'), 2: (call - 1, 'bVar4')}[which]
    s20 = A('*(short *)(param_1 + 0x%x) < 1' % tgt20, 'target army slot 19 troops (the dialog copy)', '<', 1, which != 0, 'concept:slot19_free')
    gs = list(ctx)
    loop_ctx = [C(t_slot, 'the slot holds a unit', reached=sets[which]), C(t_sel, 'the unit is selected', reached=sets[which])]
    if which == 0:
        gs += [G(flag_test[0], True, flag=F('bVar2', sets[0]), atoms=[A('bVar2', 'some unit met a full target (20 units)', None, None, True)])]
        gs += loop_ctx + [G(t_20, False, deciding=True, reached=sets[0], atoms=[s20])]
    elif which == 1:
        gs += [G(call - 5, False, flag=F('bVar2', sets[0]), atoms=[A('bVar2', 'no unit met a full target', None, None, False)]),
               G(flag_test[0], True, flag=F('bVar3', sets[1]), atoms=[A('bVar3', 'some unit would take the target over 100,000 troops', None, None, True)])]
        gs += loop_ctx + [G(t_20, True, reached=sets[1], atoms=[s20]),
                          G(t_troops, False, deciding=True, reached=sets[1], atoms=[A('iVar7 + iVar6 < 0x186a1', 'target troops + the unit\'s troops', '<', 100001, False, NUMBER)])]
    else:
        gs += [G(flag_test[0], True, flag=F('bVar4', sets[2]), atoms=[A('bVar4', 'some unit would overload the target\'s fleet', None, None, True)])]
        gs += loop_ctx + [G(t_20, True, reached=sets[2], atoms=[s20]),
                          G(t_troops, True, reached=sets[2], atoms=[A('iVar7 + iVar6 < 0x186a1', 'troops together', '<', 100001, True, NUMBER)]),
                          G(t_fleet, True, reached=sets[2], atoms=[A('-1 < sVar1', 'the target army is aboard a fleet (dialog +0x%x)' % fleet_word, '<', -1, True, 'concept:aboard_fleet')]),
                          G(t_cap, True, deciding=True, reached=sets[2], atoms=[A('iVar6 < (iVar7 + *(short *)(param_1 + 0x%x + sVar9 * 0x20)) / 500' % src, 'target fleet ships vs (target troops + the unit) / 500', '<', None, True, 'rel', rel=['ships', '<', '(troops + unit) / 500'], tokens=[r'500'])])]
    loop = sel + 6
    return R(rid, 'catalogue', fn, call, gs, E('clamp', [action], loop=loop, flag_set=sets[which]))

T1 = (44114, (44121, 44124, 44125, 44128, 44130, 44133))
T2 = (44195, (44202, 44205, 44206, 44209, 44211, 44214))
add(transfer('R28', 'TArmyToArmy_Army1Transfer', 44155, T1, 0x260, 0x750, 0x776, (44146, 44142, 44134), 0, 44125, 44138))
add(transfer('R29', 'TArmyToArmy_Army1Transfer', 44159, T1, 0x260, 0x750, 0x776, (44146, 44142, 44134), 1, 44128, 44138))
add(transfer('R30', 'TArmyToArmy_Army1Transfer', 44164, T1, 0x260, 0x750, 0x776, (44146, 44142, 44134), 2, 44133, 44138))
add(transfer('R31', 'TArmyToArmy_Army2Transfer', 44236, T2, 0x4f0, 0x4c0, 0x774, (44227, 44223, 44215), 0, 44206, 44219))
add(transfer('R32', 'TArmyToArmy_Army2Transfer', 44240, T2, 0x4f0, 0x4c0, 0x774, (44227, 44223, 44215), 1, 44209, 44219))
add(transfer('R33', 'TArmyToArmy_Army2Transfer', 44245, T2, 0x4f0, 0x4c0, 0x774, (44227, 44223, 44215), 2, 44214, 44219))


def disband(rid, fn, call, sel, yes, slot, chosen, test, setl, label_off, action, city_word, loop, prompt):
    return R(rid, 'catalogue', fn, call, [
        C(sel, 'one or more units are selected'),
        C(yes, 'the prompt %s was answered Yes (result 6)' % prompt, role='answer', atoms=[A('== 6', 'the prompt\'s result', '==', 6, True)]),
        G(call - 1, True, flag=F('cStack_b', setl, "'\\x01'"), atoms=[A("cStack_b != '\\0'", 'some selected regular unit was kept', '!=', 0, True)]),
        C(slot, 'the slot holds a unit', reached=setl), C(chosen, 'the unit is selected', reached=setl),
        G(test, True, deciding=True, reached=setl, combine='and', atoms=[
            A('*(short *)(param_1 + 0x%x) == -1' % city_word, 'the own city next to the dialog\'s FIRST army (set in the form\'s InitializeForm by FUN_004494e4)', '==', -1, True, NO_CITY),
            A('*(short *)(param_1 + 0x%x + sVar%d * 0x20) == 0' % (label_off, 6 if 'ArmyToArmy' in fn else 5), 'the unit\'s origin label (0 = regular)', '==', 0, True, 'concept:regular')],
          cite=[test, test + 1])],
        E('clamp', [action], loop=loop, flag_set=setl, note='units failing the test are kept; the others are removed in the loop'))

add(disband('R34', 'TArmyToArmy_Army1Disband', 44326, 44286, 44302, 44307, 44310, 44311, 44313, 0x25c, 44316, 0x770, 44306, 'P06'))
add(disband('R35', 'TArmyToArmy_Army2Disband', 44412, 44372, 44388, 44393, 44396, 44397, 44399, 0x4ec, 44402, 0x770, 44392, 'P07'))

# ======================================================================== TChangeArmyUnits (the Change units dialog)
SEL2 = lambda line, v: A('iVar%d < 2' % (2 if line == 45487 else 3), 'number of selected units', '<', 2, v, NUMBER)
add(R('R36', 'catalogue', 'TChangeArmyUnits_RenameUnit', 45513, [G(45487, False, deciding=True, atoms=[SEL2(45487, False)])], E('drop', [45503])))
add(R('R37', 'catalogue', 'TChangeArmyUnits_RenameUnit', 45507, [G(45487, True, atoms=[SEL2(45487, True)]),
    C(45489, 'exactly one unit is selected (none = nothing happens)', atoms=[A('iVar2 == 1', 'selected count', '==', 1, True)]),
    G(45502, False, deciding=True, atoms=[A('*(short *)(param_1 + 0x1ea + unaff_BP * 0x20) == 0', 'the selected unit\'s origin label (0 = regular)', '==', 0, False, 'concept:regular')])],
    E('drop', [45503])))
add(R('R38', 'catalogue', 'TChangeArmyUnits_SplitUnit', 45577, [G(45539, False, deciding=True, atoms=[SEL2(45539, False)])], E('drop', [45563])))
LBL = lambda v: A('*psVar1 == 0', 'the unit\'s origin label', '==', 0, v, 'concept:regular')
S19CU = lambda v: A('*(short *)(param_1 + 0x44e) < 1', 'army slot 19 troops (the dialog copy)', '<', 1, v, 'concept:slot19_free')
ONE = C(45541, 'exactly one unit is selected', atoms=[A('iVar3 == 1', 'selected count', '==', 1, True)])
add(R('R39', 'catalogue', 'TChangeArmyUnits_SplitUnit', 45572, [G(45539, True, atoms=[SEL2(45539, True)]), ONE, G(45556, False, deciding=True, atoms=[LBL(False)])], E('drop', [45563])))
add(R('R40', 'catalogue', 'TChangeArmyUnits_SplitUnit', 45568, [G(45539, True, atoms=[SEL2(45539, True)]), ONE, G(45556, True, atoms=[LBL(True)]),
    G(45557, False, deciding=True, atoms=[S19CU(False)])], E('drop', [45563])))
add(R('R41', 'catalogue', 'TChangeArmyUnits_SplitUnit', 45559, [G(45539, True, atoms=[SEL2(45539, True)]), ONE, G(45556, True, atoms=[LBL(True)]),
    G(45557, True, atoms=[S19CU(True)]),
    G(45558, True, deciding=True, atoms=[A('(int)psVar1[2] < ((short)(&DAT_00478fca)[psVar1[1] * 0x14] * 2) / 5', 'unit troops vs 2/5 of the type\'s size limit', '<', None, True, 'rel', rel=['troops', '<', 'two fifths of the size limit'], tokens=[r'two fifths|2/5|2 / 5'])])],
    E('drop', [45563])))
JU = [C(45609, 'two or more units are selected (fewer = nothing happens)', atoms=[A('1 < iVar6', 'selected count', '<', 1, True)])]
JU_LOOP = lambda setl: [C(45619, 'the slot holds a unit', reached=setl), C(45622, 'the unit is selected', reached=setl)]
add(R('R42', 'catalogue', 'TChangeArmyUnits_JoinUnits', 45642, JU + [
    G(45641, True, flag=F('bVar5', 45634), atoms=[A('bVar5', 'a selected unit is a mercenary', None, None, True)])] + JU_LOOP(45634) + [
    G(45623, False, deciding=True, reached=45634, atoms=[A('*psVar1 == 0', 'the unit\'s origin label', '==', 0, False, 'concept:regular')])],
    E('drop', [45665])))
add(R('R43', 'catalogue', 'TChangeArmyUnits_JoinUnits', 45678, JU + [
    G(45641, False, flag=F('bVar5', 45634), atoms=[A('bVar5', 'no selected unit is a mercenary', None, None, False)]),
    G(45645, False, flag=F('bVar3', 45630, 'false'), atoms=[A('bVar3', 'all selected units have one type', None, None, False)])] + JU_LOOP(45630) + [
    G(45623, True, reached=45630, atoms=[A('*psVar1 == 0', 'origin label', '==', 0, True, 'concept:regular')]),
    G(45629, True, deciding=True, reached=45630, atoms=[A('sVar10 != psVar1[1]', 'the unit\'s type vs the first selected regular unit\'s type', '!=', None, True, 'concept:types_differ')])],
    E('drop', [45665])))
add(R('R44', 'catalogue', 'TChangeArmyUnits_JoinUnits', 45647, JU + [
    G(45641, False, flag=F('bVar5', 45634), atoms=[A('bVar5', 'no mercenary selected', None, None, False)]),
    G(45645, True, flag=F('bVar3', 45630, 'false'), atoms=[A('bVar3', 'one type', None, None, True)]),
    G(45646, True, deciding=True, atoms=[A('(short)(&DAT_00478fca)[sVar10 * 0x14] < iStack_18', 'the type\'s size limit vs the selected troops in total', '<', None, True, 'rel', rel=['total', '>', 'size limit'])])],
    E('drop', [45665])))
add(R('R45', 'catalogue', 'TChangeArmyUnits_Disband', 45756, [
    C(45718, 'one or more units are selected'),
    C(45734, 'the prompt P08 was answered Yes (result 6)', role='answer', atoms=[A('iVar2 == 6', 'the prompt\'s result', '==', 6, True)]),
    G(45755, True, flag=F('cStack_b', 45745, "'\\x01'"), atoms=[A("cStack_b != '\\0'", 'some selected regular unit was kept', '!=', 0, True)]),
    C(45739, 'the slot holds a unit', reached=45745), C(45742, 'the unit is selected', reached=45745),
    G(45743, True, deciding=True, reached=45745, combine='and', atoms=[
        A('*(short *)(param_1 + 0x1d6) == -1', 'the own city next to the army (set in TChangeArmyUnits_InitializeForm)', '==', -1, True, NO_CITY),
        A('*(short *)(param_1 + 0x1ea + sVar5 * 0x20) == 0', 'origin label', '==', 0, True, 'concept:regular')], cite=[45743, 45744])],
    E('clamp', [45748], loop=45738, flag_set=45745)))

# ======================================================================== TArmyRecruits (the recruitment form)
S39 = lambda v: A('*(short *)(&DAT_00474a90 + DAT_004a0320 * 0x494) < 1', 'recruitment slot 39 troops (nation +0x420)', '<', 1, v, 'concept:slot39_free')
MOB = lambda v: A('(&DAT_00474ab2)[DAT_004a0320 * 0x24a] == 100', 'mobilisation rate (nation +0x442)', '==', 100, v, NUMBER)
add(R('R46', 'catalogue', 'TArmyRecruits_RecruitUnit', 56033, [G(55949, False, deciding=True, atoms=[S39(False)])], E('drop', [55973])))
add(R('R47', 'catalogue', 'TArmyRecruits_RecruitUnit', 55952, [G(55949, True, atoms=[S39(True)]), G(55950, True, deciding=True, atoms=[MOB(True)])], E('drop', [55973])))
add(R('R48', 'catalogue', 'TArmyRecruits_RecruitUnit', 56026, [G(55949, True, atoms=[S39(True)]), G(55950, False, atoms=[MOB(False)]),
    G(55957, False, deciding=True, combine='or', atoms=[
        A('sVar8 < 0', 'the chosen city (-1 = "All cities")', '<', 0, False, 'concept:all_cities'),
        A('0x4a < (short)(&DAT_004795aa)[sVar8 * 0x11]', 'the city\'s fortification', '<', 74, False, NUMBER),
        A('sVar8 == (&DAT_00474ab4)[DAT_004a0320 * 0x24a]', 'the city is the capital (nation +0x444)', '==', None, False, 'concept:capital')],
      cite=[55957, 55958])], E('drop', [55973])))
add(R('R49', 'catalogue', 'TArmyRecruits_MobilizeUnits', 56092, [
    C(56063, 'one or more units are selected'),
    G(56091, True, flag=F('bVar3', 56088, 'bVar2', via=56080), atoms=[A('bVar3', 'bVar2 after the loop (L56088)', None, None, True)]),
    C(56069, 'the list has rows', reached=56080), C(56073, 'the row is selected', reached=56080),
    G(56076, True, reached=56080, atoms=[A('0xf < (short)(&DAT_00474954)[DAT_004a0320 * 0x24a + iVar5 * 4]', 'the recruitment slot\'s state', '<', 15, True, NUMBER)]),
    G(56079, True, deciding=True, reached=56080, combine='or', atoms=[
        A('bVar2', 'an earlier unit already failed', None, None, True),
        A("(char)uStack_14 == '\\0'", 'FUN_0044a4e0 reported no place for the unit', '==', 0, True, 'concept:no_place')]),
    G(48973, True, fn='FUN_0044a4e0', reached=48974, atoms=[A('local_c == -1', 'no army found (FUN_0044a120) and none made (FUN_00449f08)', '==', -1, True)]),
    G(48969, None, kind='dataflow', fn='FUN_0044a4e0', means='FUN_0044a120 finds no own army on the city tile with < 20 units and room for the troops; then FUN_00449f08 is tried'),
    G(48725, False, kind='dataflow', fn='FUN_00449f08', atoms=[A('(-1 < (short)local_12) && (DAT_004a0324 < 0xc6)', 'a free tile next to the city and fewer than 198 armies', '<', 198, False)],
      means='FUN_00449f08 leaves the index at -1 unless a free tile is found and fewer than 198 armies exist')],
    E('clamp', [56077], loop=56070, flag_set=56080, note='each ready selected unit is mobilised by FUN_0044a4e0 when it finds a place')))

# ======================================================================== TPolitics (the relations form: a radio click)
add(R('R50', 'catalogue', 'TPolitics_MakePeace', 55177, [
    G(55170, True, deciding=True, combine='and', atoms=[
        A("(&DAT_00474b00)[iVar1 * 0x494] == '\\0'", 'the other nation\'s human flag (nation +0x490; 0 = computer)', '==', 0, True, 'concept:computer'),
        A('(&DAT_00474696)[DAT_004a0320 * 0x24a + iVar1] == 3', 'relation current -> other (3 = war)', '==', 3, True, 'concept:war')], cite=[55170, 55171])],
    E('drop', [55180], reports_failure=55172)))
add(R('R51', 'catalogue', 'TPolitics_MakeTrade', 55237, [
    G(55216, None, kind='dataflow', means='sVar4 counts the form\'s entries equal to 1 (marked for trade), L55217'),
    G(55235, True, deciding=True, atoms=[A('sVar4 == 3', 'nations marked for trade in the form', '==', 3, True, NUMBER)])],
    E('drop', [55260], reports_failure=55236)))
REL_NEG = lambda v: A('(short)(&DAT_00474696)[DAT_004a0320 * 0x24a + iVar3] < 0', 'relation current -> target (negative = cooldown)', '<', 0, v, 'concept:relation_negative')
add(R('R52', 'catalogue', 'TPolitics_MakeTrade', 55248, [
    G(55235, False, atoms=[A('sVar4 == 3', 'nations marked', '==', 3, False, NUMBER)]),
    G(55242, True, deciding=True, atoms=[REL_NEG(True)])], E('drop', [55260], reports_failure=55243)))
add(R('R53', 'catalogue', 'TPolitics_MakeTrade', 55257, [
    G(55235, False, atoms=[A('sVar4 == 3', 'nations marked', '==', 3, False, NUMBER)]),
    G(55242, False, atoms=[REL_NEG(False)]),
    G(55250, True, deciding=True, combine='or', atoms=[
        A('bVar1', 'the target trades with 3 nations already (L55229)', None, None, True),
        A('1 < (short)(&DAT_00474696)[DAT_004a0320 * 0x24a + (int)param_2]', 'relation current -> target (2 alliance, 3 war)', '<', 1, True, NUMBER)]),
    G(55229, True, reached=55230, combine='and', atoms=[
        A('sVar2 == 3', 'the target\'s trade partners (FUN_004499c0), less 1 when the current nation trades with it and the form cancels that (L55225)', '==', 3, True, NUMBER),
        A('(DAT_0049f00a != 1 || (param_2 != DAT_0049f008))', 'unless the target is the nation whose pending trade proposal N03 reports (DAT_0049f008 proposer, DAT_0049f00a 1 = trade)', None, None, True)]),
    G(55225, None, kind='dataflow', means='sVar2 = FUN_004499c0(target) - 1 when relation == 1 and the form value is not 1', cite=[55225, 55226])],
    E('drop', [55260], reports_failure=55251)))

ALLY_BASE = G(55310, True, deciding=True, atoms=[A("(&DAT_00474b00)[local_6 * 0x494] == '\\0'", 'the target\'s human flag (0 = computer)', '==', 0, True, 'concept:computer')])
add(R('R54', 'catalogue', 'TPolitics_MakeAlliance', 55321, None, alts=[
    [ALLY_BASE, G(55311, False, kind='pre', role='structure', atoms=[A('!bVar1', 'bVar1 = a pending war or a pending alliance with a nation at war', None, None, False)]),
     G(55300, True, deciding=True, reached=55302, atoms=[A('*(short *)(param_1 + 900 + sVar3 * 2) == 3', 'a form entry is 3 (a pending declaration of war)', '==', 3, True, 'concept:pending_war')])],
    [ALLY_BASE, G(55311, False, kind='pre', role='structure', atoms=[A('!bVar1', 'bVar1', None, None, False)]),
     G(55300, False, reached=55306, atoms=[A('*(short *)(param_1 + 900 + sVar3 * 2) == 3', 'form entry', '==', 3, False)]),
     G(55304, True, deciding=True, reached=55306, atoms=[A('*(short *)(param_1 + 900 + sVar3 * 2) == 2', 'a form entry is 2 (a pending alliance)', '==', 2, True, 'concept:pending_alliance')]),
     G(55306, True, kind='goto', deciding=True, flag=F('bVar1', 55302), atoms=[A("(char)uVar2 != '\\0'", 'FUN_00449cd8: that nation is at war with someone', '!=', 0, True, 'concept:ally_at_war')])],
    [ALLY_BASE, G(55311, True, kind='pre', role='structure', atoms=[A('!bVar1', 'no pending war or warlike alliance', None, None, True)]),
     G(55313, False, kind='goto', deciding=True, combine='and', atoms=[
         A("(char)uVar2 == '\\0'", 'FUN_00449cd8(current nation): at war with anyone', '==', 0, False, 'concept:not_at_war_any'),
         A('-1 < (short)(&DAT_00474696)[DAT_004a0320 * 0x24a + (int)local_6]', 'relation current -> target', '<', -1, False, 'concept:relation_nonneg')],
       cite=[55313, 55314])]],
    effect=E('drop', [55325], reports_failure=55316)))

# ======================================================================== TPremierForm_BuildNewFleet (the Build fleet command)
BUILDING_SET = [C(58498, 'fleets exist', reached=58518), G(58503, True, reached=58518, combine='and', atoms=[
    A('*(short *)(puVar2 + 2) == DAT_004a0320', 'fleet owner (fleet +8)', '=='), A('-1 < *(short *)((int)puVar2 + 10)', 'construction countdown (fleet +10; >= 0 = under construction)', '<', -1, True)])]
COAST = lambda v: A('sVar3 == -1', 'a free coastal own city (FUN_004496e0; -1 = none)', '==', -1, v, 'concept:no_coastal')
add(R('R55', 'catalogue', 'TPremierForm_BuildNewFleet', 58528, [
    G(58526, True, atoms=[COAST(True)]),
    G(58527, True, deciding=True, flag=F('cStack_5', 58518, "'\\x01'"), atoms=[A("cStack_5 == '\\0'", 'no own fleet under construction (cStack_5 is set by the N02 loop)', '==', 0, True, 'concept:none_building')])],
    E('drop', [58541])))
add(R('R56', 'catalogue', 'TPremierForm_BuildNewFleet', 58532, [
    G(58526, True, atoms=[COAST(True)]),
    G(58527, False, deciding=True, flag=F('cStack_5', 58518, "'\\x01'"), atoms=[A("cStack_5 == '\\0'", 'own fleet under construction', '==', 0, False, 'concept:none_building')])] + BUILDING_SET,
    E('drop', [58541])))
add(R('R57', 'catalogue', 'TPremierForm_BuildNewFleet', 58537, [
    G(58526, False, atoms=[COAST(False)]),
    G(58536, True, deciding=True, atoms=[A('DAT_004a0326 == 99', 'the fleet count', '==', 99, True, NUMBER)])],
    E('drop', [58541])))

# ======================================================================== prompts
SC = lambda code, var, op, const, v, check=None, means='': G(None, v, kind='sc', atoms=[A(code, var, op, const, v, check)], means=means)
add(R('P01', 'prompts', 'TUnitMap_DisbandArmy', 47106, [C(47096, 'an own army is selected'),
    G(47101, False, deciding=True, atoms=[A('sVar2 == -1', 'own city within one tile', '==', -1, False, NO_CITY)])],
    answers=ANS(47108, '==', 'then', [act(47110, 'the army\'s money (army +0xc) is added to the nation\'s treasury (nation +0x438)', 'treasury'),
                                      act(47113, 'its supplies (army +0xa) are added to that city\'s supplies (city +0x18)', 'city_supplies'),
                                      act(47115, 'the army is deleted (FUN_0044ab90)', 'army_deleted')])))
add(R('P02', 'prompts', 'TUnitMap_ScuttleFleet', 47345, [OWN_FLEET(47334), G(47336, True, atoms=[FLEET_ARMY_SCUT(True)]),
    G(47340, False, deciding=True, atoms=[A('sVar2 == -1', 'own city within one tile', '==', -1, False, NO_CITY)])],
    answers=ANS(47347, '==', 'then', [act(47350, 'the fleet\'s money (fleet +0x10) is added to the nation\'s treasury', 'treasury'),
                                      act(47354, 'its supplies (fleet +0xe) are added to the city\'s supplies', 'city_supplies'),
                                      act(47356, 'the fleet is deleted (FUN_0044ad38)', 'fleet_deleted')])))
add(R('P03', 'prompts', 'TUnitMap_SelectUnit', 46541, [
    BVAR4_DEF, C(46532, 'the clicked tile is a city', role='target'),
    G(46539, True, kind='sc', atoms=[A('bVar4', 'an army with 1 or more moves is selected one tile away (L46514)', None, None, True)]),
    G(46539, True, kind='sc', atoms=[A('uVar2 != DAT_004a0320', 'the city belongs to another nation', '!=', None, True)]),
    G(46539, False, kind='sc', deciding=True, atoms=[A('(&DAT_00474696)[(short)DAT_004a0320 * 0x24a + (int)(short)uVar2] == 3', 'relation current -> owner (3 = war)', '==', 3, False, 'concept:war')], cite=[46540])],
    answers=ANS(46543, '==', 'then', [act(46545, 'FUN_00449b40(current, owner, 3): the relation becomes 3 (war) both ways', 'war'),
                                      act(46547, 'FUN_0044b27c: the siege', 'attack')],
                after=[act(46551, 'the army selection is cleared (DAT_004a0328 = -1) whatever the answer', 'deselect')])))
add(R('P04', 'prompts', 'TUnitMap_SelectUnit', 46566, [
    BVAR4_DEF, C(46532, 'not a city', role='target', out=False), C(46555, 'an army', role='target'),
    G(46563, True, atoms=[A('uVar2 != DAT_004a0320', 'the army belongs to another nation', '!=', None, True)]),
    G(46564, True, kind='sc', atoms=[A('bVar4', 'an army with moves one tile away', None, None, True)]),
    G(46564, False, kind='sc', deciding=True, atoms=[A('(&DAT_00474696)[(short)DAT_004a0320 * 0x24a + (int)(short)uVar2] == 3', 'relation (3 = war)', '==', 3, False, 'concept:war')], cite=[46565])],
    answers=ANS(46568, '==', 'then', [act(46570, 'FUN_00449b40(..., 3): war', 'war'), act(46572, 'FUN_0044aee4: the field battle', 'attack')],
                after=[act(46575, 'the army selection is cleared whatever the answer', 'deselect')])))
add(R('P05', 'prompts', 'TUnitMap_SelectUnit', 46623, [
    C(46532, 'not a city', role='target', out=False), C(46555, 'not an army', role='target', out=False), C(46582, 'a fleet', role='target'),
    G(46590, False, atoms=[A('uVar2 == DAT_004a0320', 'the fleet is not own', '==', None, False)]),
    G(46611, False, combine='or', atoms=[A('DAT_004a032a < 0', 'own fleet selected', '<', 0, False),
                                         A('(short)(&DAT_0049c278)[DAT_004a032a * 0xd] < 1', 'its moves', '<', 1, False, 'concept:no_moves'),
                                         A('!bVar4', 'one tile apart', None, None, False)], cite=[46611, 46613]),
    G(46621, True, atoms=[A('sVar5 < 0', 'a city of the fleet\'s owner within one tile', '<', 0, True, 'concept:no_owner_city')]),
    G(46622, False, kind='sc', deciding=True, atoms=[A('(&DAT_00474696)[(short)DAT_004a0320 * 0x24a + (int)(short)uVar2] == 3', 'relation (3 = war)', '==', 3, False, 'concept:war')])],
    answers=ANS(46625, '==', 'then', [act(46627, 'FUN_00449b40(..., 3): war', 'war'), act(46629, 'FUN_0044b5d0: the sea battle', 'attack')])))


def disband_prompt(pid, fn, call, sel, yes, action, refusal):
    return R(pid, 'prompts', fn, call, [G(sel, True, deciding=True, atoms=[A('0 < iVar%d' % (2 if 'ChangeArmy' in fn else 3), 'number of selected units', '<', 0, True, NUMBER)])],
             answers=ANS(yes, '==', 'then', [act(action, 'the selected units are removed (subject to %s)' % refusal, 'units_removed'), act(action, 'see %s' % refusal, 'cite:' + refusal)]))


add(disband_prompt('P06', 'TArmyToArmy_Army1Disband', 44300, 44286, 44302, 44316, 'R34'))
add(disband_prompt('P07', 'TArmyToArmy_Army2Disband', 44386, 44372, 44388, 44402, 'R35'))
add(disband_prompt('P08', 'TChangeArmyUnits_Disband', 45732, 45718, 45734, 45748, 'R45'))
add(R('P09', 'prompts', 'TArmyRecruits_DisbandUnits', 56146, [G(56132, True, deciding=True, atoms=[A('0 < iVar3', 'number of selected queue rows', '<', 0, True, NUMBER)])],
    answers=ANS(56148, '==', 'then', [act(56160, 'the mobilisation rate (nation +0x442) drops by troops x 1000 / wealth + 1, not below 0: what queueing added (L56000-L56002)', 'mobilisation'),
                                      act(56167, 'the queue slot is deleted (FUN_0044a610); no treasury write: no refund', 'queue_deleted')])))
add(R('P10', 'prompts', 'TPremierForm_NewGame', 58018, [
    G(58017, True, kind='sc', deciding=True, atoms=[A("cVar1 != '\\0'", 'FUN_00449050: some nation\'s human flag is set (all_app_functions.txt L47764)', '!=', 0, True, 'concept:human_exists')])],
    answers=ANS(58019, '!=', 'after_return', [act(58034, 'the forms are closed and the new-game form opens (FUN_00424608 with 0x456d00)', 'new_game_form')]),
    note='with no human nation the new-game form opens without the prompt'))
add(R('P11', 'prompts', 'TPremierForm_CheckQuit', 58150, [
    G(58149, True, deciding=True, atoms=[A("cVar1 != '\\0'", 'FUN_00449050: a human nation exists', '!=', 0, True, 'concept:human_exists')])],
    answers=ANS(58152, '!=', 'after_return', [act(58157, 'CanClose = 1: the program quits', 'quit')], other_actions=[act(58153, 'CanClose = 0: the window stays', None)]),
    note='with no human nation the window closes without the prompt'))
add(R('P12', 'prompts', 'TPremierForm_NewNation', 58398, [],
    answers=ANS(58400, '==', 'then', [act(58401, 'FUN_00449078(current): the current nation\'s human flag is cleared (all_app_functions.txt L47789)', 'seat_to_computer'),
                                      act(58402, 'the new-game form opens (0x456d00), to pick a nation', None)])))
add(R('P13', 'prompts', 'TPremierForm_Abdicate', 58425, [],
    answers=ANS(58427, '==', 'then', [act(58428, 'FUN_00449078(current): the current nation goes to the computer', 'seat_to_computer'),
                                      act(58431, 'the turn ends when a human nation remains', None)])))

# ======================================================================== notices
add(R('N01', 'notices', 'TBuildFleet_OK', 56327, [G(56320, True, deciding=True, atoms=[A('0 < (short)param_1[0x7f]', 'the ordered fleet size', '<', 0, True, NUMBER)])],
    E('notice_after_action', [56321], note='FUN_0044a004 places the order before the notice')))
add(R('N02', 'notices', 'TPremierForm_BuildNewFleet', 58517, [C(58498, 'fleets exist'),
    G(58503, True, deciding=True, combine='and', atoms=[A('*(short *)(puVar2 + 2) == DAT_004a0320', 'fleet owner == current', '==', None, True, 'concept:own_fleet'),
                                                        A('-1 < *(short *)((int)puVar2 + 10)', 'construction countdown', '<', -1, True, 'concept:under_construction')])],
    E('info', note='one box per own fleet under construction; the loop sets cStack_5 (read by R55/R56)')))
add(R('N03', 'notices', 'TPremierForm_StartTurn', 58228, [
    G(58212, True, deciding=True, combine='and', atoms=[A('-1 < DAT_0049f008', 'a nation proposed trade or an alliance (DAT_0049f008 = that nation)', '<', -1, True, 'concept:proposal'),
                                                        A('(&DAT_00474696)[DAT_004a0320 * 0x24a + (int)DAT_0049f008] != DAT_0049f00a', 'the relation is not the proposed one (DAT_0049f00a)', '!=', None, True, 'concept:not_granted')], cite=[58212, 58213])],
    E('info')))

FIELDS = [  # memory address: meaning, with the line of docs/sav-layout-notes.md that gives the record and the field
    ('0x0047c1ec', 'army record base, stride 0x290', 127, 'In memory it is at `0x0047C1EC`, stride `0x290`'),
    ('0x0047c1f0', 'army +4 owner', 133, 'owner nation code'), ('0x0047c1f2', 'army +6 moves', 134, 'moves remaining this turn'),
    ('0x0047c1f4', 'army +8 covered cell, -1 = aboard a fleet', 135, '−1 = aboard a fleet'), ('0x0047c1f6', 'army +0xa supplies', 136, 'supplies, tons'),
    ('0x0047c1f8', 'army +0xc money', 137, 'money (the army purse)'), ('0x0047c1fc', 'army +0x10 unit slots, 32 bytes each', 139, 'unit slots; slot `k` is at `16 + 32*k`'),
    ('unit +0', 'origin label, 0 = regular', 156, 'origin label: **0 = regular**'), ('unit +2', 'unit type', 157, 'unit type'), ('unit +4', 'troops, <= 0 = empty', 158, 'troops. **≤ 0 = empty slot**'),
    ('0x0049c26c', 'fleet record base, stride 0x1a', 178, 'In memory it is at `0x0049C26C`, stride `0x1A`'),
    ('0x0049c274', 'fleet +8 owner', 186, 'owner nation code'), ('0x0049c276', 'fleet +10 construction countdown', 187, 'construction countdown'),
    ('0x0049c278', 'fleet +0xc moves', 188, 'moves'), ('0x0049c27a', 'fleet +0xe supplies', 189, 'supplies, tons'), ('0x0049c27c', 'fleet +0x10 money', 190, 'money (purse)'),
    ('0x0049c27e', 'fleet +0x12 ships', 191, 'ships'), ('0x0049c282', 'fleet +0x16 carried army, -1 = none', 193, 'index of the carried army. **−1 = none**'),
    ('0x00479590', 'city record base, stride 0x22', 101, 'in memory at `0x00479590`, stride `0x22`'), ('0x004795a2', 'city +0x12 owner', 108, 'owner (nation code)'),
    ('0x004795a8', 'city +0x18 supplies', 111, 'supplies, tons'), ('0x004795aa', 'city +0x1a fortification', 112, 'fortification'),
    ('0x00474670', 'nation record base, stride 0x494', 206, '`0x00474670`, stride `0x494`'), ('0x00474696', 'nation +0x26 relation to nation j (0 peace, 1 trade, 2 alliance, 3 war, < 0 cooldown)', 227, 'relation to nation `j`'),
    ('relation values', '0 peace, 1 trade, 2 alliance, 3 war; negative = cooldown', 253, '0 peace, 1 trade, 2 alliance, 3 war'),
    ('0x00474954', 'nation +0x2e4 recruitment slots {state, type, troops, city}', 230, 'recruitment slots'), ('0x00474aa8', 'nation +0x438 treasury', 234, 'treasury, talents'),
    ('0x00474ab2', 'nation +0x442 mobilisation %', 237, 'mobilization %'), ('0x00474ab4', 'nation +0x444 capital city', 238, 'capital city index'),
    ('0x00474b00', 'nation +0x490 human flag (0 = computer)', 248, 'human flag: **1 = human, 0 = computer**'),
]


def build():
    rows = ROWS
    for r in rows:
        for alt in r['paths']:
            for g in alt:
                g['fn'] = g['fn'] or r['function']
    ex = open(EXTRACT, 'rb').read()
    return {'schema': 'refusal-predicates/1', 'issue': 58,
            'source': {'extract': os.path.relpath(EXTRACT, ROOT), 'extract_sha256': hashlib.sha256(ex).hexdigest(),
                       'dump': 'all_app_functions.txt', 'dump_sha256_pinned': '2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8',
                       'layout': 'docs/sav-layout-notes.md'},
            'excluded': [{'id': 'X01', 'why': 'the battle screen (TBattleMap_Surrender): excluded by the task'}],
            'fields': [{'address': a, 'meaning': m, 'doc_line': l, 'doc_quote': q} for a, m, l, q in FIELDS],
            'rows': rows}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=os.path.join(DATA, 'predicates.json'))
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    from common import write_new
    p = write_new(a.out, json.dumps(build(), indent=1, ensure_ascii=False) + '\n')
    print(p)


if __name__ == '__main__':
    main()
