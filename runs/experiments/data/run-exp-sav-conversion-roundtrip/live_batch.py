"""Serial original-game scenarios; one isolated prefix/display, no blind retry."""
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
cases = [('native-orders', 'B', []), ('native-progress-6', 'C', []),
         ('native-progress-12', 'D', []), ('native-progress-24', 'E', [])]
if len(sys.argv) > 1 and sys.argv[1] == 'extended':
    cases = [('native-cargo', 'F', []), ('native-orders', 'G', ['--seed-build', '--attempt', 'seed-v1'])]
for scenario, case, extra in cases:
    print('Starting original executable scenario:', scenario, flush=True)
    result = subprocess.run([sys.executable, str(here / 'live.py'), scenario, case, *extra])
    if result.returncode:
        raise SystemExit(f'{scenario} failed: read its complete receipt before proceeding')
