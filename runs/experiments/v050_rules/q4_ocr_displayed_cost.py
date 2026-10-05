"""Q4: read the dialog's "Quarterly cost" box from each offer-selected screenshot into a tracked tsv (the observation the audit compares the
displayed-estimate formula with). Box = 40x16 at (320,121) on the 1280x1024 screen. usage: q4_ocr_displayed_cost.py [artifacts-dir]"""
import sys, os, glob, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ART, DATA
from common import write_new
art = (sys.argv[1] if len(sys.argv) > 1 else ART).rstrip('/') + '/'
tmp = os.path.join(tempfile.gettempdir(), 'ic2_v050_q4_ocr.png')
rows = ['screenshot\tdisplayed_quarterly_cost']
for p in sorted(glob.glob(art + 'Q4_*_offer_selected*.png')):
    subprocess.run(['convert', p, '-crop', '40x16+320+121', '+repage', '-resize', '600%', '-colorspace', 'Gray', tmp], check=True)
    v = subprocess.run(['tesseract', tmp, 'stdout', '--psm', '7', '-c', 'tessedit_char_whitelist=0123456789'], capture_output=True, text=True).stdout.strip()
    rows.append('%s\t%s' % (os.path.basename(p), v))
print(write_new(os.path.join(DATA, 'q4_displayed_cost.tsv'), '\n'.join(rows) + '\n'))
