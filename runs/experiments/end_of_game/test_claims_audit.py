#!/usr/bin/env python3
"""Tests of claims_audit.py: the audit passes on the real sources, and it FAILS on (a) a doctored save, (b) a doctored staged input, (c) a doctored screenshot,
(d) each of several doctored claims in the finding, (e) a doctored tracked reading. Run after fetch_archive.py has prepared the artifacts folder.

  python3 runs/experiments/end_of_game/test_claims_audit.py"""
import os, sys, shutil, subprocess, tempfile, struct, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths
sys.path.insert(0, paths.ROOT)
AUDIT = os.path.join(HERE, 'claims_audit.py')
FINDING = os.path.join(paths.ROOT, 'findings', '2026-10-05-end-of-game-screens.md')

def run(finding=FINDING, art=paths.ART, data=paths.DATA):
    r = subprocess.run([sys.executable, AUDIT, '--finding', finding, '--artifacts', art, '--data', data, '--out', 'none', '--quiet'], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr

def expect(name, code, out, want_fail, needle=None):
    ok = (code != 0) if want_fail else (code == 0 and ' 0 mismatches' in out)
    if want_fail and needle: ok = ok and needle in out
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ': ' + out[-400:].replace('\n', ' | ')))
    return ok

results = []
tmp = tempfile.mkdtemp(prefix='eog_audit_test_')
try:
    code, out = run(); results.append(expect('baseline: the real sources give 0 mismatches', code, out, False)); print('   ', out.strip().splitlines()[-1])
    # artifacts copy for doctoring
    art = os.path.join(tmp, 'art'); shutil.copytree(paths.ART.rstrip('/'), art)
    def flip(path, offset_fn):
        b = bytearray(open(path, 'rb').read()); o = offset_fn(b); b[o] ^= 0x01; open(path, 'wb').write(bytes(b)); return o
    from state import sav as SAV
    import fmt
    # (a) a doctored autosave: one bit of Rome's treasury (+0x438) in the debt autosave
    p = os.path.join(art, 'saves', 'EOG_debt_b1_AUTO0721.SAV')
    flip(p, lambda b: fmt.nation0(b) + 0x438)
    code, out = run(art=art); results.append(expect('doctored autosave (treasury bit flipped) fails', code, out, True, 'W1')); 
    shutil.copy(os.path.join(paths.ART, 'saves', 'EOG_debt_b1_AUTO0721.SAV'), p)
    # (b) a doctored staged input: the staged unity value
    p = os.path.join(art, 'saves', 'inputs', 'EOG_unity_b1_staged.SAV')
    flip(p, lambda b: fmt.nation0(b) + 0x440)
    code, out = run(art=art); results.append(expect('doctored staged input (unity bit flipped) fails', code, out, True, 'EOG_unity_b1_staged.SAV'))
    shutil.copy(os.path.join(paths.ART, 'saves', 'inputs', 'EOG_unity_b1_staged.SAV'), p)
    # (c) a doctored screenshot
    p = os.path.join(art, 'EOG_y250_b1_04_window.png'); b = bytearray(open(p, 'rb').read()); b[-20] ^= 0xFF; open(p, 'wb').write(bytes(b))
    code, out = run(art=art); results.append(expect('doctored screenshot fails', code, out, True, 'W4'))
    shutil.copy(os.path.join(paths.ART, 'EOG_y250_b1_04_window.png'), p)
    # (c2) a doctored base save: a start value
    p = os.path.join(art, 'saves', 'inputs', 'EOG_2h_base_AUTO0720.SAV')
    flip(p, lambda b: fmt.nation0(b) + 6 * SAV.NATION_LEN + 0x43C)
    code, out = run(art=art); results.append(expect('doctored base save (a start value) fails', code, out, True, 'base'))
    shutil.copy(os.path.join(paths.ART, 'saves', 'inputs', 'EOG_2h_base_AUTO0720.SAV'), p)
    # (d) doctored claims in the finding
    text = open(FINDING, encoding='utf-8').read()
    def doctor(name, old, new, needle):
        assert old in text, old
        f = os.path.join(tmp, 'finding_%s.md' % re.sub(r'\W', '_', name)); open(f, 'w', encoding='utf-8').write(text.replace(old, new, 1))
        code, out = run(finding=f); return expect('doctored claim: ' + name, code, out, True, needle)
    results.append(doctor('a population figure', '| 2,601,000 | 25 | 25 | 2,200 | 2,221 | `EOG_y250_b1_04_window.png`', '| 2,601,001 | 25 | 25 | 2,200 | 2,221 | `EOG_y250_b1_04_window.png`', 'W4'))
    results.append(doctor('a reason text', 'Your unpopularity has forced the army to overthrow you. | Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 25 | 2,200 | 2,200 | `EOG_unity_b1', 'Your army have deposed you because they have not been paid. | Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 25 | 2,200 | 2,200 | `EOG_unity_b1', 'W3'))
    results.append(doctor('the years line', 'Your 20 years in power in Rome produced these changes. | 2,577,000 | 2,601,000 | 25 | 25 | 2,200 | 2,221 | `EOG_y250_b1', 'Your 19 years in power in Rome produced these changes. | 2,577,000 | 2,601,000 | 25 | 25 | 2,200 | 2,221 | `EOG_y250_b1', 'W4'))
    results.append(doctor('the cities count of the conquest', '| 1,512,000 | 1,497,000 | 28 | 4 |', '| 1,512,000 | 1,497,000 | 28 | 0 |', 'W13'))
    results.append(doctor('humans after a fall with two humans', '| G8 | debt of Gaul, two humans | [0, 6] | [0] |', '| G8 | debt of Gaul, two humans | [0, 6] | [] |', 'G8'))
    results.append(doctor('Abdicate after state', '| S14 | Abdicate, two humans (Rome) | 0 | abdicate | Appius Claudius | Appius Claudius | 821 | 821 | 2,200 | 2,200 |', '| S14 | Abdicate, two humans (Rome) | 0 | abdicate | Appius Claudius | Appius Claudius | 821 | 821 | 2,200 | 3,200 |', 'S14'))
    results.append(doctor('a staged old/new value', '| EOG_debt_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | treasury[0] | 2200 | -30000 | 4 |', '| EOG_debt_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | treasury[0] | 2200 | -29000 | 4 |', 'EOG_debt_b1_staged.SAV'))
    results.append(doctor('a start-table count', '| run0-start-AUTO0720-seed12345.SAV | 16 | 11 | 16 | 16 |', '| run0-start-AUTO0720-seed12345.SAV | 16 | 12 | 16 | 16 |', 'start'))
    results.append(doctor('a code citation line', '| 56391 | DAT_004a0332 == 0xfa |', '| 56392 | DAT_004a0332 == 0xfa |', 'code line 56392'))
    results.append(doctor('a re-run hash prefix', '| W14 | EOG_debt_b1_04_window.png | EOG_debt_b9_04_window.png | a589ba017226 |', '| W14 | EOG_debt_b1_04_window.png | EOG_debt_b9_04_window.png | a589ba017227 |', 'W14'))
    results.append(doctor('a count', '| windows captured (rows of the windows table) | 17 |', '| windows captured (rows of the windows table) | 18 |', 'count'))
    results.append(doctor('the double space of the short-time line', 'Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 25 | 2,200 | 2,200 | `EOG_unity_b1', 'Your short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 25 | 2,200 | 2,200 | `EOG_unity_b1', 'W3'))
    # (e0) the code extract under --data is the source of the literals and thresholds: an altered literal or threshold changes the recomputed text
    def doctor_extract(name, old, new, needle):
        d2 = os.path.join(tmp, 'data_' + re.sub(r'\W', '_', name)); shutil.copytree(paths.DATA.rstrip('/'), d2)
        cands = sorted(f for f in os.listdir(d2) if f.startswith('code_extract_end_of_game'))
        p2 = os.path.join(d2, cands[-1]); x = open(p2, encoding='utf-8').read(); assert old in x, old
        open(p2, 'w', encoding='utf-8').write(x.replace(old, new))
        code, out = run(data=d2); return expect('doctored code extract: ' + name, code, out, True, needle)
    results.append(doctor_extract('a result literal', 'Your army have deposed you because they have not been paid.', 'Your army has deposed you because they have not been paid.', 'W1'))
    results.append(doctor_extract('the years literal', ' years ', ' yrs ', 'W4'))
    results.append(doctor_extract('the 250 threshold of the window', 'DAT_004a0332 == 0xfa) {', 'DAT_004a0332 == 0xfb) {', 'thresholds'))
    results.append(doctor_extract('the unity threshold of the window', ']  < 400) {'.replace(']  <', '] <'), '] < 399) {', 'thresholds'))
    results.append(doctor_extract('the human flag the hand-over writes', '(&DAT_00474b00)[iVar4 * 0x494] = 0;', '(&DAT_00474b00)[iVar4 * 0x494] = 2;', 'human flag'))
    # (e) a doctored tracked reading: a memory string of one window
    data = os.path.join(tmp, 'data'); shutil.copytree(paths.DATA.rstrip('/'), data)
    for fn in os.listdir(data):
        if fn.startswith('ocr_b1.jsonl'):
            t = open(os.path.join(data, fn)).read(); open(os.path.join(data, fn), 'w').write(t.replace('Your army have deposed you because they have not been paid.', 'Your army have deposed you because they have not been paid!'))
    code, out = run(data=data); results.append(expect('doctored tracked memory reading fails', code, out, True, 'W1'))
    # (f) a doctored per-label OCR reading
    for fn in os.listdir(data):
        if fn.startswith('ocr_labels'):
            t = open(os.path.join(data, fn)).read(); open(os.path.join(data, fn), 'w').write(t.replace('Cities 28', 'Cities 29'))
    code, out = run(data=data); results.append(expect('doctored per-label OCR fails', code, out, True, 'OCR'))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print('%d of %d tests passed' % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
