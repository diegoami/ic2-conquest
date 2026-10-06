#!/usr/bin/env python3
"""Re-read the message of every box screenshot (REF_*_box_box*.png of the artifacts) with a tighter crop (the text area right of the icon, above the button), at 4x, psm 6 and
psm 7 per line; writes a NEW versioned tracked ocr_reread.jsonl (png, wid-independent). The first readings in ocr_b*.jsonl are kept untouched."""
import os, sys, json, glob, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new
from paths import ART, DATA
rows = []
for p in sorted(glob.glob(ART + 'REF_*_box_box*.png')):
    w, h = [int(x) for x in subprocess.run(['identify', '-format', '%w %h', p], capture_output=True, text=True).stdout.split()]
    tmp = os.path.join(tempfile.gettempdir(), 'ic2_ref_reread.png')
    subprocess.run(['convert', p, '-crop', '%dx%d+%d+0' % (int(w * 0.81), int(h * 0.62), int(w * 0.19)), '+repage', '-resize', '400%', '-colorspace', 'Gray', '-sharpen', '0x1', tmp], check=True)
    t6 = subprocess.run(['tesseract', tmp, 'stdout', '--psm', '6'], capture_output=True, text=True).stdout
    t4 = subprocess.run(['tesseract', tmp, 'stdout', '--psm', '4'], capture_output=True, text=True).stdout
    rows.append({'png': os.path.basename(p), 'size': [w, h], 'psm6': ' '.join(t6.split()), 'psm4': ' '.join(t4.split())})
print(write_new(os.path.join(DATA, 'ocr_reread.jsonl'), '\n'.join(json.dumps(r) for r in rows) + '\n'), len(rows))
