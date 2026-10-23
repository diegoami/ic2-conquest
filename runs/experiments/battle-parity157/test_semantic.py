"""CPU inertness for expanded hooks, including exits and full-counter payloads."""
import contextlib
import hashlib
import io
import json
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import semantic_observer as O
from tests import test_battle_hook_caves as T
from unicorn.x86_const import *

T.H = O.H
T.L.CTL, T.L.BUF = O.H.CTL, O.H.BUF
T.HIGH = O.STATE_END
T.STACK_TOP = 0x3010000
T.rng_small = lambda seed: seed % 100  # includes counters beyond the old prefix.
old_state, old_new = T.random_state, T.new_machine

def state(rng):
    regs, stack, seed = old_state(rng)
    # Valid caller frame/read pointer for the real displaced exit instructions.
    regs[UC_X86_REG_ESP] = T.STACK_TOP - 0x1000
    regs[UC_X86_REG_EBP] = T.STACK_TOP - 0x800
    regs[UC_X86_REG_EAX] = 0x47c000 + rng.randrange(0x20000)
    return regs, stack, seed

def machine(state):
    uc, caves = old_new(state)
    uc.mem_write(O.SNAPSHOT, O.snapshot_code())
    return uc, caves

T.random_state, T.new_machine = state, machine
stdout = io.StringIO()
checks = []
with contextlib.redirect_stdout(stdout):
    sys.argv = [sys.argv[0], '--trials', '100']
    rc = T.main()
    assert rc == 0
    rng = random.Random(157)
    for df in [0, 1]:
        for counter in [0, 6, 15, 100]:
            for index in [0, O.STATE_CAP - 1, O.STATE_CAP]:
                seed_state = state(rng)
                regs, stack, seed = seed_state
                regs[UC_X86_REG_EFLAGS] = (regs[UC_X86_REG_EFLAGS] & ~0x400) | (df << 10)
                uc, caves = machine(seed_state)
                T.prepare(uc, seed_state, T.SITE, b'\xe8' + O.H.rel32(T.SITE, caves['random'][0]) + b'\xf4')
                payload = rng.randbytes(2176)
                uc.mem_write(0x4a0344, payload[:2096])
                uc.mem_write(0x45e6b0, payload[2096:])
                uc.mem_write(O.H.COUNTER_HR, struct.pack('<H', counter))
                uc.mem_write(O.H.CTL, struct.pack('<I', index))
                T.run(uc, T.SITE, T.SITE + 5)
                assert struct.unpack('<I', uc.mem_read(O.OVERFLOW, 4))[0] == int(index >= O.STATE_CAP)
                if index < O.STATE_CAP:
                    raw = bytes(uc.mem_read(O.STATE_BUF + index * O.STATE_REC, O.STATE_REC))
                    assert raw[128:] == payload
                    base = T.L.decode(bytes(uc.mem_read(O.H.BUF + index * O.H.REC, O.H.REC)), index)
                    snap = O.decode_snapshot(raw, base)
                    assert snap['counter'] == counter and snap['original_esp'] == regs[UC_X86_REG_ESP] - 4
                    assert snap['stack_words'][0] == T.SITE + 5
                assert uc.reg_read(UC_X86_REG_EFLAGS) & 0x400 == df << 10
                checks.append(dict(df=df, counter=counter, index=index, passed=True))

report = dict(exit=rc, checks=stdout.getvalue(), active_payload_cases=checks,
              observer_sha256=hashlib.sha256(Path(O.__file__).read_bytes()).hexdigest(),
              scope='Expanded original-versus-hook CPU preservation, reentry/overflow/mutation controls. Wine inertness still required.')
out = ROOT / 'runs/experiments/data/run-exp-battle-parity157/semantic-cpu-v1.json'
with out.open('x') as f:
    json.dump(report, f, indent=2)
    f.write('\n')
print(stdout.getvalue(), out, flush=True)
