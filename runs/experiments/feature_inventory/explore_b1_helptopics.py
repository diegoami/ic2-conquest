from explore_lib import *
g = Game(); g.reset_ui()
g.click(304, 36, pause=1.0); g.click(348, 57, pause=4.0)
g.shot(ART + 'FI_b1_06_help_topics.png'); wins(g, 'b1', 'help topics')
