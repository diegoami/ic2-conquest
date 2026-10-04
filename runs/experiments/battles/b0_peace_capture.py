#!/usr/bin/env python3
"""Capture the "Offer of peace" box (TBattlePols) that a game left open: the gate's 6th trial (lab seed 2) stopped on it because
play_out waited for the map. Run it against that live process (it starts nothing): screenshot, OCR, controls, then No, then
a Save As to read the news and the relation. Written as a one-off after the fact; the finding quotes its log."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import b0_probe as B  # noqa: E402  (same folder)
from harness.driver import Game, G, sh  # noqa: E402

g = Game()
log = B.Log("b0-peace-capture")
ws = g.find_windows(".")
log("windows", windows=[(w[1], w[2], w[3], w[4], w[5]) for w in ws])
box = g.find_windows("^Offer of peace$")
if not box:
    sys.exit("no 'Offer of peace' window")
log.shot(g, "01-offer-of-peace-root")
pw = log.shot(g, "01b-offer-of-peace-window", window=str(box[0][0]))
log("ocr", text=B.ocr(pw), geometry=box[0][2:])
cs = B.dump_controls(g, log, "Offer of peace", "offer of peace")
for i in range(3):
    log("tick", windows=B.win_list(g))
    time.sleep(1)
no = g.control(cs, text="No")
for attempt in range(3):
    g.click_control(no, pause=1.5)
    if not g.find_windows("^Offer of peace$"):
        break
    log("no_click_did_not_close", attempt=attempt + 1)
time.sleep(2)
log("after_no", windows=B.win_list(g), popups=g.popups())
log.shot(g, "02-after-no")
p = g.save_as("lab2_a_after_no.SAV")
kept = B.keep(p)
B.describe_save(kept, log, "after No on the peace offer")
