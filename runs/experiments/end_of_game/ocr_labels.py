#!/usr/bin/env python3
"""OCR each label of every captured End of Game window separately: the label rectangles are read from the form resource of THumanFalls (forms.json of the
feature-inventory data, tracked), each is cropped from the window screenshot (the window is captured without decoration, so form client coordinates are
screenshot coordinates), enlarged 4x and read with tesseract (psm 7). Writes ocr_labels.jsonl (the next free version) beside the other tracked outputs.
usage: ocr_labels.py [ARTIFACTS_DIR]"""
import sys, os, re, json, glob, subprocess, hashlib, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ART, DATA, ROOT
from common import write_new
FORMS = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-feature-inventory', 'forms.json')
art = (sys.argv[1] if len(sys.argv) > 1 else ART).rstrip('/') + '/'

def label_rects():
    f = [x for x in json.load(open(FORMS)) if x['class'] == 'THumanFalls'][0]
    return {c['name']: tuple(c['props'][k] for k in ('Left', 'Top', 'Width', 'Height')) for c in f['children'] if c['class'] == 'TLabel'}

def read(png, rect):
    l, t, w, h = rect
    tmp = os.path.join(tempfile.gettempdir(), 'ic2_eog_label.png')
    subprocess.run(['convert', png, '-crop', '%dx%d+%d+%d' % (w, h, l, t), '+repage', '-bordercolor', 'white', '-border', '6', '-resize', '400%', '-colorspace', 'Gray', tmp], check=True)
    return ' '.join(subprocess.run(['tesseract', tmp, 'stdout', '--psm', '7'], capture_output=True, text=True).stdout.split())

if __name__ == '__main__':
    rects = label_rects(); out = []
    for png in sorted(glob.glob(art + '*.png')):
        if not re.search(r'_window(\.v\d+)?\.png$', png): continue
        sha = hashlib.sha256(open(png, 'rb').read()).hexdigest()
        out.append({'png': os.path.basename(png), 'sha256': sha, 'labels': {n: read(png, r) for n, r in rects.items()}})
    p = write_new(os.path.join(DATA, 'ocr_labels.jsonl'), ''.join(json.dumps(o) + '\n' for o in out))
    print(p, len(out), 'windows')
    for o in out[:3]: print(json.dumps(o)[:600])
