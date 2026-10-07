"""The AI-mover contact-resolution experiment (research pending request, 2026-10-07, from
imperial-conquest-main via the research session). FUN_0044d734 dispatches on the destination
cell when a mover's walk ends (army tile: FUN_0044aee4 only if at war and moves>0, else
nothing; city at war: siege FUN_0044b27c; city not at war: resupply FUN_0044f6d8) and the human
twin TUnitMap_MoveHumanArmy calls the same function — this experiment corroborates those
branches in play.

    source harness/env.sh && python3 runs/experiments/ai_contact/contact.py <subcommand>

Subcommands:
  control LAST    fresh new_game(seed), Rome idle, End turn to LAST; reproduces the ai-turn
                  run (seed 424242) whose 0722 save holds the natural AI-mover-vs-human-army
                  contact (Gaul v Rome) and the Celtiberian sieges.
  humanmover      the run-0 start (BASE.SAV), join + march to Gaul's army, then a MOVE (not
                  the attack click) whose destination is Gaul's army tile: the human-mover
                  contact control. Records position, popups, battle-flag and the army record
                  (moves/supplies/money) around the contact, then ends the turn for the save.

Turn errors are never retried blind (safe_end_turn pumps first, never a second End turn click;
same contract as ai_turn/watch.py)."""
import hashlib, json, os, shutil, struct, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from paths import ART, DATA
from common import write_new
from snapshot import snapshot
from harness.driver import Game, G, WORK, DriverError

SEED = 424242


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def log_lines():
    return len((G / 'AUTOSAVE.LOG').read_text().splitlines()) if (G / 'AUTOSAVE.LOG').exists() else 0


def keep(texts, tag=''):
    """The newest autosave -> artifacts + hash + tracked snapshot (rule 6). Returns its turn number."""
    line = (G / 'AUTOSAVE.LOG').read_text().splitlines()[-1]
    assert line.rstrip().endswith('OK'), line
    name = os.path.basename(line.split()[1])
    turn = int(name[4:8])
    dst = ART + (tag + '_' if tag else '') + name
    if not os.path.exists(dst):
        shutil.copy(G / name, dst)
        with open(DATA + 'SAVES.sha256', 'a') as f:
            f.write('%s  %s\n' % (sha(dst), os.path.basename(dst)))
    snap = snapshot(open(dst, 'rb').read(), os.path.basename(dst))
    snap['turn_texts'] = texts
    p = write_new('%sturns/%s.json' % (DATA, (tag + '_' if tag else '') + name), json.dumps(snap, indent=1) + '\n')
    print('kept %s -> %s' % (os.path.basename(dst), p), flush=True)
    return turn


def pump(g, n0, timeout=300):
    """Wait the running turn out WITHOUT clicking End turn (ai_turn/watch.py contract)."""
    texts, t0 = [], time.time()
    while time.time() - t0 < timeout:
        if log_lines() > n0:
            break
        if g.find_windows(r'^End turn \?$'):
            texts.append('CONFIRM ' + g.read_popup(g.find_windows(r'^End turn \?$')[0]))
            cs = None
            for _ in range(3):
                try:
                    cs = g.controls('End turn ?')
                    break
                except DriverError:
                    time.sleep(1)
            if cs is None:
                continue
            g.click_control(g.control(cs, text='End turn'), pause=1.5)
            continue
        if g.in_battle() and g.find_windows(' v '):
            texts.append('BATTLE ' + g.find_windows(' v ')[0][1])
            g.play_battle()
            continue
        texts += g.dismiss_popups()
        time.sleep(1)
    else:
        raise DriverError('pump: turn did not finish within %ds' % timeout)
    time.sleep(3)
    texts += g.dismiss_popups()
    line = (G / 'AUTOSAVE.LOG').read_text().splitlines()[-1]
    if not line.rstrip().endswith('OK'):
        raise DriverError('autosave: ' + line)
    return line.split()[1], texts


def safe_end_turn(g):
    n0 = log_lines()
    if log_lines() > n0 or g.find_windows(r'^End turn \?$') or (g.pid and g.in_battle()) or g.popups():
        try:
            return pump(g, n0, timeout=30)
        except DriverError:
            pass
    try:
        return g.end_turn()
    except DriverError as e:
        print('end_turn failed (%s); pumping the turn out' % e, flush=True)
        time.sleep(3)
        if log_lines() > n0:
            line = (G / 'AUTOSAVE.LOG').read_text().splitlines()[-1]
            return line.split()[1], ['recovered: turn completed after ' + str(e)]
        return pump(g, n0)


def rec_fields(g, i):
    """The contact-relevant army fields, read from live memory via the shared parser."""
    from state.sav import parse_army
    a = parse_army(g.army_rec(i), i)
    return {k: a[k] for k in ('id', 'x', 'y', 'moves', 'supplies', 'money', 'troops', 'morale')}


def control(last, resume=False):
    g = Game()
    if resume:
        # reattach to THIS run's game only (the prefix path disambiguates from other sessions' games)
        out = subprocess.check_output(['pgrep', '-f', 'ic2-work-contact']).split()
        g.pid = int(out[0])
        print('resumed on pid %d' % g.pid, flush=True)
    else:
        pre = ART + 'pre-run-game-folder/'
        os.makedirs(pre, exist_ok=True)
        for f in G.glob('AUTO*'):
            if not os.path.exists(pre + f.name):
                shutil.copy(f, pre + f.name)
        path, texts = g.new_game(row=0, seed=SEED)
        write_new(DATA + 'run.json', json.dumps(
            {'seed': SEED, 'last_turn': last, 'human_row': 0, 'human': 'Rome', 'mode': 'control',
             'seed_line': getattr(g, 'seed_line', ''), 'new_game_texts': texts}, indent=1) + '\n')
        keep(texts)
    while True:
        turn = int(os.path.basename((G / 'AUTOSAVE.LOG').read_text().splitlines()[-1].split()[1])[4:8])
        if turn >= last:
            break
        _p, texts = safe_end_turn(g)
        keep(texts)
    print('control done at %04d' % turn)


def humanmover():
    from state.sav import load
    BASE = WORK / 'fixtures' / 'BASE.SAV'
    g = Game()
    g.load(BASE, seed=SEED)
    write_new(DATA + 'run.json', json.dumps(
        {'seed': SEED, 'mode': 'humanmover', 'start': 'fixtures/BASE.SAV (run-0 start)',
         'seed_line': getattr(g, 'seed_line', '')}, indent=1) + '\n')
    # turn 1 (0720): bring army 1 to (113,45) — the proven gallic-army sequence
    g.move(1, 113, 45)
    _n, texts = safe_end_turn(g)
    keep(texts)
    # turn 2 (0721): close in and join into army 0
    g.move(1, 104, 36)
    g.move(0, 103, 36)
    g.join(0)
    _n, texts = safe_end_turn(g)
    keep(texts)
    # march toward Gaul's army one leg per turn; when adjacent, MOVE onto its tile (not attack)
    log = []
    for turn in range(10):
        name = os.path.basename((G / 'AUTOSAVE.LOG').read_text().splitlines()[-1].split()[1])
        s = load(G / name)
        gaul = next((a for a in s['armies'] if a['owner'] == 6), None)   # 6 = Gaul
        if gaul is None:
            log.append(dict(turn=turn, event='Gaul has no army'))
            write_new(DATA + 'humanmover_log.json', json.dumps(log, indent=1) + '\n')
            _n, texts = safe_end_turn(g); keep(texts)
            break
        t = (gaul['x'], gaul['y'])
        pos = g.army_pos(0)
        entry = dict(turn=turn, gaul=dict(x=t[0], y=t[1], troops=gaul['troops']),
                     rome=rec_fields(g, 0))
        if max(abs(pos[0] - t[0]), abs(pos[1] - t[1])) <= 1:
            # the contact: a MOVE whose destination is the enemy army's tile
            entry['rome_before'] = rec_fields(g, 0)
            npos, mtexts = g.move(0, *t)
            time.sleep(2)
            battle = bool(g.in_battle() and g.find_windows(' v '))
            entry.update(move_texts=mtexts, pos_after=npos,
                         battle_window=battle, rome_after=rec_fields(g, 0))
            log.append(entry)
            write_new(DATA + 'humanmover_log.json', json.dumps(log, indent=1) + '\n')
            if battle:
                entry['battle'] = g.find_windows(' v ')[0][1]
                write_new(DATA + 'humanmover_log.json', json.dumps(log, indent=1) + '\n')
                g.play_battle()
            _n, texts = safe_end_turn(g)
            entry['turn_texts'] = texts
            write_new(DATA + 'humanmover_log.json', json.dumps(log, indent=1) + '\n')
            keep(texts, tag='hm')
            break
        g.move(0, *t)
        _n, texts = safe_end_turn(g)
        entry['marched_to'] = t
        log.append(entry)
        write_new(DATA + 'humanmover_log.json', json.dumps(log, indent=1) + '\n')
        keep(texts)
    print('humanmover done')


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'control':
        control(int(args[0]), resume='--resume' in args)
    else:
        {'humanmover': humanmover}[cmd](*args)
