"""Debug server: owns the game process (so /proc/<pid>/mem is readable) and executes command files dropped in CMD dir.
usage: server.py [save [seed]]   then: cmd NAME  (writes NAME.py in CMD, waits for NAME.out)."""
import sys, os, time, io, traceback, contextlib
sys.path.insert(0, '/home/diego/projects/wt-rules/runs/experiments/v050_rules')
from lib import *
CMD = '/tmp/claude-1000/cmd/'
os.makedirs(CMD, exist_ok=True)
g = MyGame(); xvfb()
if len(sys.argv) > 1:
    print(g.load(sys.argv[1], seed=int(sys.argv[2]) if len(sys.argv) > 2 else 12345), flush=True)
done = set()
ns = dict(globals())
while True:
    for f in sorted(os.listdir(CMD)):
        if f.endswith('.py') and f not in done:
            done.add(f)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                try: exec(open(CMD + f).read(), ns)
                except SystemExit: pass
                except Exception: traceback.print_exc(file=buf)
            open(CMD + f[:-3] + '.out', 'w').write(buf.getvalue())
        if f == 'quit': g.kill(); sys.exit(0)
    time.sleep(0.3)
