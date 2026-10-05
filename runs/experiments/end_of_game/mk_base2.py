#!/usr/bin/env python3
"""New Game with Rome (row 0) and Gaul (row 6) human, seed 12345: the unedited two-human start save used as the source of every two-human scenario."""
import sys, os, shutil, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eog import *
from eog import _drv
clear_autos()
g = MyGame()
p, texts = g.new_game(rows=[0, 6], seed=12345)
log('base2', 'new game: %s popups %s seed line %s' % (p, texts, getattr(g, 'seed_line', None)))
dst = new_path(SAVEDIR + 'inputs/EOG_2h_base_AUTO0720.SAV'); shutil.copy(p, dst)
with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(dst), os.path.basename(dst)))
s = read_save(dst)
log('base2', 'saved %s: current nation %s, turn order %s, humans %s, date %s' % (os.path.basename(dst), s['current_nation'], s['turn_order'],
    [n['id'] for n in s['nations'] if n.get('human')], s['date']))
log('base2', 'AUTOSAVE.LOG: %s' % (_drv.G / 'AUTOSAVE.LOG').read_text().splitlines())
print(world_state(g, 'newgame'))
