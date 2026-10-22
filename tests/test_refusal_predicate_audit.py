#!/usr/bin/env python3
"""Offline tests (no Wine, no private inputs) for runs/experiments/refusal_texts/predicate_audit.py (issue #58).

A small synthetic function (not game code) with two refusals and one prompt, its predicate table and a three-table finding are
written to a temporary folder. The clean set must pass; each mutation must be reported with its kind:
 catalogue side: a removed citation, a removed answer citation, an unresolved quote, an inverted condition, a changed constant,
 an inverted branch marker, a changed answer number, a changed answer effect, a changed effect kind;
 table side: an inverted outcome, a changed constant, a dropped test, an acting line moved into the box's branch.
The tracked predicate table is also audited against the tracked extract and finding (both in git): it must have 0 table errors
and 0 mismatches.

Run: python3 -m tests.test_refusal_predicate_audit   (exit 1 on a failure)."""
import copy, json, os, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'runs', 'experiments', 'refusal_texts'))
import predicate_audit as PA  # noqa: E402
from predicates_def import A, G, C, R, E, ANS, act  # noqa: E402

SRC = r'''// ==== TFoo_Split @ 00400000 ====

void TFoo_Split(int param_1)

{
  short sVar1;
  int iVar2;

  sVar1 = *(short *)(param_1 + 0x10);
  if (-1 < sVar1) {
    if ((short)(&DAT_00500000)[sVar1 * 0xd] < 0x14) {
      FUN_0042d750((uint *)"Too few ships.",CONCAT31(0,2),DAT_1,0);
    }
    else if ((short)(&DAT_00500004)[sVar1 * 0xd] < 0) {
      iVar2 = FUN_0042d750((uint *)"Split it ?",CONCAT31(0,3),DAT_1,0);
      if (iVar2 == 6) {
        FUN_00401000(sVar1);
      }
    }
    else {
      FUN_0042d750((uint *)"It carries an army.",CONCAT31(0,2),DAT_1,0);
    }
  }
  return;
}
'''
FIRST = 101   # line numbers: 101 = the header; 110 = the own-fleet test; 111 = ships < 20; 112 = box 1; 114 = army test; 115 = prompt;
              # 116 = answer test; 117 = the act; 121 = box 2


def predicates():
    ships = lambda v: A('(short)(&DAT_00500000)[sVar1 * 0xd] < 0x14', 'ships', '<', 20, v, 'number')
    army = lambda v: A('(short)(&DAT_00500004)[sVar1 * 0xd] < 0', 'carried army', '<', 0, v, 'concept:fleet_no_army')
    own = C(110, 'a fleet is selected')
    rows = [
        R('R01', 'catalogue', 'TFoo_Split', 112, [own, G(111, True, deciding=True, atoms=[ships(True)])], E('drop', [117])),
        R('R02', 'catalogue', 'TFoo_Split', 121, [own, G(111, False, atoms=[ships(False)]), G(114, False, deciding=True, atoms=[army(False)])], E('drop', [117])),
        R('P01', 'prompts', 'TFoo_Split', 115, [own, G(111, False, atoms=[ships(False)]), G(114, True, deciding=True, atoms=[army(True)])],
          answers=ANS(116, '==', 'then', [act(117, 'the fleet is scuttled', 'fleet_deleted')])),
    ]
    for r in rows:
        for alt in r['paths']:
            for g in alt: g['fn'] = g['fn'] or r['function']
    return {'schema': 'refusal-predicates/1', 'fields': [], 'rows': json.loads(json.dumps(rows))}


FINDING = '''# synthetic

<!-- table: catalogue -->
| id | test order | literal | function:call line | box [buttons] | condition [derived] | effect [derived] | play [confirmed] |
|---|---|---|---|---|---|---|---|
| R01 | 1 of 2 | `Too few ships.` | TFoo_Split:112 | mtInformation [mbOK] | the fleet has fewer than 20 ships: L111 «if ((short)(&DAT_00500000)[sVar1 * 0xd] < 0x14) {» | dropped: nothing happens | - |
| R02 | 2 of 2 | `It carries an army.` | TFoo_Split:121 | mtInformation [mbOK] | 20 or more ships and the fleet carries an army: the else of L114 «else if ((short)(&DAT_00500004)[sVar1 * 0xd] < 0) {» | dropped: nothing happens | - |

<!-- table: prompts -->
| id | literal | function:call line | box [buttons] | raised when [derived] | answers [derived] | play [confirmed] |
|---|---|---|---|---|---|---|
| P01 | `Split it ?` | TFoo_Split:115 | mtConfirmation [mbYes+mbNo+mbCancel] | 20 or more ships (the else of L111 «< 0x14») and no army aboard: L114 «(short)(&DAT_00500004)[sVar1 * 0xd] < 0» | Yes (6) scuttles the fleet: L116 «if (iVar2 == 6) {»; No or Cancel: nothing | - |

<!-- table: notices -->
| id | kind | literal | function:call line | box [buttons] | raised when | note |
|---|---|---|---|---|---|---|
'''


class Fixture:
    def __init__(self):
        self.d = tempfile.mkdtemp(prefix='pa58_')
        self.extract = os.path.join(self.d, 'extract.txt')
        with open(self.extract, 'w', encoding='utf-8') as f:
            f.write('# synthetic\n')
            for k, line in enumerate(SRC.rstrip('\n').split('\n')):
                f.write('%d\t%s\n' % (FIRST + k, line))

    def run(self, finding_text=FINDING, table=None):
        fp = os.path.join(self.d, 'finding.md'); tp = os.path.join(self.d, 'pred.json')
        open(fp, 'w', encoding='utf-8').write(finding_text)
        json.dump(table or predicates(), open(tp, 'w', encoding='utf-8'))
        PA.cflow._cache.clear()
        return PA.run(fp, tp, self.extract)


def kinds(res): return sorted(set(k for k, _, _ in res['mismatches']))


def main():
    fails = []
    def expect(name, cond, detail=''):
        print('%-55s %s' % (name, 'ok' if cond else 'FAIL ' + str(detail)[:300]))
        if not cond: fails.append(name)
    fx = Fixture()
    clean = fx.run()
    expect('clean synthetic set: no table error', clean['table_errors'] == [], clean['table_errors'])
    expect('clean synthetic set: no mismatch', clean['mismatches'] == [], clean['mismatches'])
    # ---------------------------------------------------------- catalogue mutations
    def cat(name, old, new, kind):
        assert FINDING.count(old) == 1, old
        res = fx.run(FINDING.replace(old, new))
        expect(name, kind in kinds(res) and res['table_errors'] == [], (kinds(res), res['mismatches']))
    cat('removed citation -> missing citation', ': L111 «if ((short)(&DAT_00500000)[sVar1 * 0xd] < 0x14) {»', '', 'missing citation')
    cat('removed answer citation -> missing citation', ': L116 «if (iVar2 == 6) {»', '', 'missing citation')
    cat('changed quote -> unresolved citation', 'L114 «(short)(&DAT_00500004)[sVar1 * 0xd] < 0»', 'L114 «(short)(&DAT_00500004)[sVar1 * 0xd] < 1»', 'unresolved citation')
    cat('inverted condition -> condition', 'the fleet has fewer than 20 ships', 'the fleet has 20 or more ships', 'condition')
    cat('changed constant -> condition', 'the fleet has fewer than 20 ships', 'the fleet has fewer than 25 ships', 'condition')
    cat('inverted state -> condition', '20 or more ships and the fleet carries an army', '20 or more ships and the fleet carries no army', 'condition')
    cat('inverted branch marker -> branch direction', 'the else of L114', 'L114', 'branch direction')
    cat('added branch marker -> branch direction', 'ships: L111', 'ships: the else of L111', 'branch direction')
    cat('changed answer number -> answer', 'Yes (6) scuttles', 'No (7) scuttles', 'answer')
    cat('changed answer effect -> answer', 'Yes (6) scuttles the fleet', 'Yes (6) repairs the fleet', 'answer')
    cat('changed effect kind -> effect', '| dropped: nothing happens | - |\n| R02', '| clamped: nothing happens | - |\n| R02', 'effect')
    # ---------------------------------------------------------- table mutations
    def tab(name, mutate):
        t = predicates(); mutate(t); res = fx.run(table=t)
        expect(name, len(res['table_errors']) > 0, res['table_errors'])
    def g(t, rid, line): return [x for x in [r for r in t['rows'] if r['id'] == rid][0]['paths'][0] if x['line'] == line][0]
    tab('table: inverted outcome -> table error', lambda t: g(t, 'R01', 111).update(out=False))
    tab('table: changed constant -> table error', lambda t: g(t, 'R01', 111)['atoms'][0].update(const=21))
    tab('table: changed operator -> table error', lambda t: g(t, 'R02', 114)['atoms'][0].update(op='<='))
    tab('table: dropped test -> table error', lambda t: [r for r in t['rows'] if r['id'] == 'R02'][0]['paths'][0].remove(g(t, 'R02', 111)))
    tab('table: act moved into the box branch -> table error', lambda t: [r for r in t['rows'] if r['id'] == 'R01'][0]['effect'].update(action=[112]))
    tab('table: answer acting on No -> table error', lambda t: [r for r in t['rows'] if r['id'] == 'P01'][0]['answers'].update(op='!='))
    # ---------------------------------------------------------- the tracked table, extract and finding
    pred = PA.latest(os.path.join(PA.DATA, 'predicates.json')) if os.path.isdir(PA.DATA) else None
    if pred:
        PA.cflow._cache.clear()
        real = PA.run(PA.FINDING, pred, PA.EXTRACT)
        expect('tracked table: 0 table errors (%d checks)' % real['table_checks'], real['table_errors'] == [], real['table_errors'][:5])
        expect('tracked finding: 0 mismatches (%d checks, %d rows)' % (real['catalogue_checks'], real['rows']), real['mismatches'] == [], real['mismatches'][:5])
    else:
        expect('tracked table present', False, 'no predicates.json under %s' % PA.DATA)
    print('%d failure(s)' % len(fails))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
