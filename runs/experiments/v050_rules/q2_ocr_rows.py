"""Q2: read the numbers of the Balance sheet screenshots row by row (tesseract on a crop of each value box) into a tracked tsv.
The dialog is 422x380 at (23,49); the revenue column's values sit at x 150-210, the expenditure column's at x 360-420 (screen px of the 1280x1024 screen)."""
import sys, subprocess, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new, DATA
from paths import ART
ROWS = (('Taxes', 150, 111), ('Tribute', 150, 140), ('Trade', 150, 170), ('Total revenue', 150, 282),
        ('Administration', 360, 111), ('Fleet', 360, 140), ('Army recruits', 360, 170), ('Regular units', 360, 200),
        ('Mercenary units', 360, 230), ('Total expenditure', 360, 282), ('Balance', 150, 348), ('Debt limit', 360, 348))
def read(p, x, y):
    tmp = os.path.join(__import__('tempfile').gettempdir(), 'ic2_v050_ocr_row.png')
    subprocess.run(['convert', p, '-crop', '60x20+%d+%d' % (x, y - 10), '+repage', '-resize', '400%', '-colorspace', 'Gray', tmp], check=True)
    return subprocess.run(['tesseract', tmp, 'stdout', '--psm', '7', '-c', 'tessedit_char_whitelist=0123456789,'], capture_output=True, text=True).stdout.strip()
lines = ['screenshot\trow\tocr']
for p in sorted(glob.glob(ART + 'Q2_*_balance_sheet*.png')):
    for name, x, y in ROWS:
        lines.append('%s\t%s\t%s' % (os.path.basename(p), name, read(p, x, y)))
print(write_new(os.path.join(DATA, 'q2_balance_values.tsv'), '\n'.join(lines) + '\n'))
