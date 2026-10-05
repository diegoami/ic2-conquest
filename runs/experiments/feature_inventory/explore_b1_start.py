from explore_lib import *
xvfb()
g = Game()
g.load(ROOT + '/saves/run0-start-AUTO0720-seed12345.SAV' if False else '/home/diego/ic2-work-inv/fixtures/BASE.SAV', seed=12345)
log('b1', 'loaded BASE.SAV seed 12345; seed line: ' + g.seed_line)
wins(g, 'b1', 'start'); g.shot(ART + 'FI_b1_01_main.png')
