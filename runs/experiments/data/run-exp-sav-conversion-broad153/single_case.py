"""Execute one named, already-converted case with normal immutable receipts."""
import json,sys
import live
cases=[json.loads(l) for l in (live.ART/'native-v1/manifest.jsonl').read_text().splitlines()]
index,case=next((i,c) for i,c in enumerate(cases) if c['name']==sys.argv[1])
try:
 live.run_case(case,index)
finally:
 if live.display is not None:live.display.terminate();live.display.wait(timeout=10)
receipt=live.HERE/f"live-{case['name']}-v1.json"
sys.exit(0 if json.loads(receipt.read_text())['complete'] else 1)
