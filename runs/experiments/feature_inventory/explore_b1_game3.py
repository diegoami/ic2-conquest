from explore_lib import *
g = Game()
wins(g, 'b1', 'state before')
if g.find_windows('^Confirm$'): g.answer('Confirm', yes=False)
wins(g, 'b1', 'after answering No (new nation)')
g.menu('game', 3); time.sleep(1); g.shot(ART + 'FI_b1_10_game_abdicate.png'); wins(g, 'b1', 'Game>Abdicate')
if g.find_windows('^Confirm$'): g.answer('Confirm', yes=False)
wins(g, 'b1', 'after answering No (abdicate)')
