"""Locations, derived from this file's place in the checkout (same pattern as cosmetic_gaps)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
ART = os.environ.get('IC2_ARTIFACTS', os.path.join(ROOT, 'artifacts', 'run-exp-ai-contact')).rstrip('/') + '/'
DATA = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-ai-contact') + '/'
