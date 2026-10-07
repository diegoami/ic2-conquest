"""Drive a fixed-seed new game (Rome human, 15 AI seats) turn by turn and keep ONE SAV per watched turn:
the fast rollingsave exe writes AUTOnnnn.SAV at every human turn; this copies each into the gitignored
artifacts dir, hashes it into the tracked SAVES.sha256, and writes the parsed snapshot (snapshot.py) to
the tracked data dir (rule 6: text outputs straight to the tracked path, never overwritten).

    source harness/env.sh && python3 runs/experiments/ai_turn/watch.py <seed> <last_turn> [--resume]

`last_turn` is the last AUTOnNNN to collect (e.g. 732: two week-11 boundaries, 0725->0726 and 0731->0732).
--resume reattaches to the already-running game (pid from pgrep) instead of a new game: the seed is read
back from the tracked run.json, so the record stays honest about which run the turns belong to.

Turn errors are never retried blind (driver pitfall: never click End turn twice): safe_end_turn first
PUMPS the game for up to 20 s without clicking anything (an "End turn ?" box left over from a failed
interaction gets its End turn button clicked, a turn already running gets waited out), and only when the
game is provably idle does it click End turn once; a mid-turn error falls back to the same pump."""
import hashlib, json, os, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from paths import ART, DATA
from common import write_new
from snapshot import snapshot
from harness.driver import Game, G, DriverError

SEED = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 424242
LAST = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 732
RESUME = '--resume' in sys.argv


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def log_lines():
    return len((G / 'AUTOSAVE.LOG').read_text().splitlines()) if (G / 'AUTOSAVE.LOG').exists() else 0


def keep(texts):
    """The newest autosave -> artifacts + hash + tracked snapshot. Returns its turn number."""
    line = (G / 'AUTOSAVE.LOG').read_text().splitlines()[-1]
    assert line.rstrip().endswith('OK'), line
    name = os.path.basename(line.split()[1])
    turn = int(name[4:8])
    dst = ART + name
    if not os.path.exists(dst):
        shutil.copy(G / name, dst)
        with open(DATA + 'SAVES.sha256', 'a') as f:
            f.write('%s  %s\n' % (sha(dst), name))
    snap = snapshot(open(dst, 'rb').read(), name)
    snap['turn_texts'] = texts
    p = write_new('%sturns/%s.json' % (DATA, name), json.dumps(snap, indent=1) + '\n')
    print('kept %s -> %s' % (name, p), flush=True)
    return turn


def pump(g, n0, timeout=300, first_box=True):
    """Wait the running turn out WITHOUT clicking End turn: dismiss/answer whatever is up
    (an "End turn ?" box gets its End turn button clicked, battles are auto-played, news boxes
    dismissed) until the autosave line appears. DriverError on timeout. `first_box=False` skips
    the initial box-only phase (used after our own click)."""
    texts, t0 = [], time.time()
    while time.time() - t0 < timeout:
        if log_lines() > n0:
            break
        if g.find_windows(r'^End turn \?$'):
            texts.append('CONFIRM ' + g.read_popup(g.find_windows(r'^End turn \?$')[0]))
            cs = None                                # the box can vanish between the two reads: read with retries
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
        # something is pending from an earlier interaction: pump it, never click End turn on top of it
        try:
            return pump(g, n0, timeout=30)
        except DriverError:
            pass                                        # game was idle after all: fall through to the click
    try:
        return g.end_turn()
    except DriverError as e:
        print('end_turn failed (%s); pumping the turn out' % e, flush=True)
        time.sleep(3)
        if log_lines() > n0:
            line = (G / 'AUTOSAVE.LOG').read_text().splitlines()[-1]
            return line.split()[1], ['recovered: turn completed after ' + str(e)]
        return pump(g, n0)


def main():
    g = Game()
    if RESUME:
        g.pid = int(subprocess.check_output(['pgrep', '-f', '^Imperial Conquest']).split()[0])
        print('resumed on pid %d' % g.pid, flush=True)
    else:
        # keep the game folder's previous scratch autosaves out of new_game's way (rule 6 caution)
        pre = ART + 'pre-run-game-folder/'
        os.makedirs(pre, exist_ok=True)
        for f in G.glob('AUTO*'):
            if not os.path.exists(pre + f.name):
                shutil.copy(f, pre + f.name)
        path, texts = g.new_game(row=0, seed=SEED)
        write_new(DATA + 'run.json', json.dumps(
            {'seed': SEED, 'last_turn': LAST, 'human_row': 0, 'human': 'Rome',
             'seed_line': getattr(g, 'seed_line', ''), 'new_game_texts': texts}, indent=1) + '\n')
        keep(texts)
    while True:
        turn = int(os.path.basename((G / 'AUTOSAVE.LOG').read_text().splitlines()[-1].split()[1])[4:8])
        if turn >= LAST:
            break
        _p, texts = safe_end_turn(g)
        keep(texts)
    print('done at %04d' % turn)


if __name__ == '__main__':
    main()
