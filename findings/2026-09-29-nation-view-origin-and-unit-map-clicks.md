# Nation `+0x486`/`+0x488` is the unit map's view origin; how a click becomes a tile

**Status:** draft finding from `ic2-conquest`, awaiting promotion. It names two nation-record fields that `ptolemaic-player-and-week9.md` left unknown ("changed when a human seat was added"), and closes the "map pixel ↔ tile" gap.

**Answer.**
- Nation record `+0x488` is the **x** and `+0x486` the **y** of the top-left tile shown in the *Unit map* window, per nation (so a loaded game keeps each human nation's view).
- The unit map's mouse handler (`0x446420`) computes the clicked tile as `x = X div 32 + nation[+0x488]`, `y = (Y − 30) div 32 + nation[+0x486]`, with `(X, Y)` relative to the map's paint box. The first 30 px are the strip above the tiles. It then reads the map word `[0x45E870 + x·280 + y·2]` (the map is column-major, 140 words per column) and dispatches on the marker code: 20–99 city, 200–247 army, 300–347 fleet.
- A click on the *Area map* sets the origin so that the clicked tile sits at column 6, row 7 of the unit map.

## Method

- Code: capstone disassembly of `0x446400`–`0x446600` in the original executable.
- Live: the running game's memory read through `/proc/<pid>/mem` under Wine (the Windows address space maps 1:1), before and after area-map clicks at tiles (101,43), (150,70), (20,20) and (300,130): the origin became (95,36), (144,63), (14,13) and (294,123). Screenshots of the unit map matched the city tiles predicted from the save's city table (Teanum Apulum (116,45), Luceria (115,48), Venusia (118,51) with origin (109,39)).
- Save: the view origin in `BASE.SAV` is (97,39), and the unit map then shows Rome (101,43) at column 4, row 4.

## Reproduction

`harness/driver.py`: `Game.view_origin()`, `Game.show(x, y)`.
