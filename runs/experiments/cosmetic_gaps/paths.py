"""Locations, all derived from this file's place in the checkout (nothing is tied to one machine's checkout path).
Override with the environment: IC2_ARTIFACTS (the folder holding saves/ and screenshots: default <repo>/artifacts/run-exp-cosmetic-gaps),
IC2_DUMP (the Ghidra dump all_app_functions.txt, needed only by make_extract.py), IC2_WORK_REF (the private game folder the Wine plays use)."""
import os, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
ART = os.environ.get('IC2_ARTIFACTS', os.path.join(ROOT, 'artifacts', 'run-exp-cosmetic-gaps')).rstrip('/') + '/'
DATA = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-cosmetic-gaps') + '/'
DUMP = os.environ.get('IC2_DUMP', '/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt')
TMP = tempfile.gettempdir()
