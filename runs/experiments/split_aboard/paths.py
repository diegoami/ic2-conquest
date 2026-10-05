"""Locations, all derived from this file's place in the checkout (nothing is tied to one machine's checkout path).
Override with the environment: IC2_ARTIFACTS (the folder holding saves/, inputs/ and screenshots: default <repo>/artifacts/run-exp-split-aboard),
IC2_DUMP (the Ghidra dump all_app_functions.txt, needed only by extract_code.py and the optional dump check),
IC2_DAT (Imperial Conquest 2.dat, needed only by extract_dat_prices.py), IC2_WORK_SPLIT (the private game folder the Wine plays use)."""
import os, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
ART = os.environ.get('IC2_ARTIFACTS', os.path.join(ROOT, 'artifacts', 'run-exp-split-aboard')).rstrip('/') + '/'
DATA = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-split-aboard') + '/'
DUMP = os.environ.get('IC2_DUMP', os.path.expanduser('~') + '/ic2-dump/all_app_functions.txt')
DAT = os.environ.get('IC2_DAT', os.path.expanduser('~/ic2-work/prefix/drive_c/IC2/Imperial Conquest 2.dat'))
TMP = tempfile.gettempdir()
