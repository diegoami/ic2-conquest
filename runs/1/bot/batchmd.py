"""Run 1 helper: split a notes file with '=== <turn>' markers and write each turn's file with turnmd.

    python3 runs/1/bot/batchmd.py <notes-batch.md>
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import turnmd  # noqa: E402

text = Path(sys.argv[1]).read_text()
for part in text.split("=== ")[1:]:
    head, body = part.split("\n", 1)
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(body)
    turnmd.main(int(head.strip()), f.name)
    print("wrote", head.strip())
