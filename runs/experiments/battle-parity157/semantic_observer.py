"""Expanded memory-only observer: full battle, movement steps and routine exits.

Isolates B11 configuration from the legacy recorder. Hook bytes are guarded by
the original builder; relocated instructions contain no PC-relative operands.
Must pass CPU and same-base live inertness before use as exact evidence.
"""
import importlib.util
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('_battle157_hook', ROOT / 'patches/battle_hook.py')
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
# More cave space; the original/private-stack operations remain the same.
H.CTL = 0x567000
H.SV, H.TAGV = H.CTL + 20, H.CTL + 24
H.BUSY, H.REENT = H.CTL + 32, H.CTL + 36
H.S_EAX, H.S_FL = H.CTL + 40, H.CTL + 44
H.PRIV_TOP = H.CTL + 0x100
H.BUF = 0x568000
H.RAW_SIZE = 0x4000
H.PARK = b'\xa3' + H.u32(H.S_EAX) + b'\x9f\x0f\x90\xc0\xa3' + H.u32(H.S_FL)
H.UNPARK = b'\xa1' + H.u32(H.S_FL) + b'\x04\x7f\x9e\xa1' + H.u32(H.S_EAX)
H.SWITCH_IN = b'\x89\x25' + H.u32(H.SV) + b'\xbc' + H.u32(H.PRIV_TOP) + b'\x9c\x60'
H.SWITCH_OUT = b'\x61\x9d\x8b\x25' + H.u32(H.SV) + b'\xc7\x05' + H.u32(H.BUSY) + H.u32(0)
SNAPSHOT = 0x567200
OVERFLOW = 0x567180
STATE_BUF = 0x868000
STATE_REC, STATE_CAP = 2304, 8192
STATE_END = STATE_BUF + STATE_REC * STATE_CAP
MAX_COUNTER = 65535
sys.path.insert(0, str(ROOT / 'runs/experiments/tactical25-trace'))
import observer as legacy

SEMANTIC_MARKERS = (
    ('walk_step', 0x438a6c, bytes.fromhex('558bec83c4f4')),
    ('walk_step_exit', 0x438d1b, bytes.fromhex('5f5e5b8be5')),
    ('walk_exit', 0x438f70, bytes.fromhex('5f5e5b8be5')),
    ('shot_exit', 0x439397, bytes.fromhex('83c4145d5f')),
    ('melee_exit', 0x439906, bytes.fromhex('83c4305d5f')),
    ('rout_exit', 0x439104, bytes.fromhex('5a5d5f5e5b')),
    ('remove', 0x438f78, bytes.fromhex('0fbfc06bc00b')),
    ('remove_after_state', 0x438fa2, bytes.fromhex('8b10a1a0e64500')),
    ('place', 0x4381a4, bytes.fromhex('5356575583c4f0')),
    ('setup', 0x439968, bytes.fromhex('558bec83c4b8')),
    ('end_half', 0x439c20, bytes.fromhex('803d7d0b4a0000')),
)
H.MARKERS += legacy.EXTRA_MARKERS + SEMANTIC_MARKERS
BaseAsm = H.Asm

class SnapshotAsm(BaseAsm):
    def b(self, *chunks):
        super().b(*chunks)
        if chunks == (b'\x89\x35' + H.u32(H.CTL + 8),):
            self.call(SNAPSHOT)
        return self

H.Asm = SnapshotAsm

def configure():
    """Configuration is isolated and completed at import; compatible runner API."""

def snapshot_code():
    a = H.Asm(SNAPSHOT)
    a.b(b'\x8b\x46\x04', b'\x3d' + H.u32(STATE_CAP))
    a.j8(0x72, 'room')
    a.b(b'\xc7\x05' + H.u32(OVERFLOW) + H.u32(1), b'\xc3')
    a.label('room')
    a.b(b'\x69\xf8' + H.u32(STATE_REC), b'\x81\xc7' + H.u32(STATE_BUF))
    a.b(b'\xfc', b'\xb9' + H.u32(12), b'\xf3\xa5')
    for va in [0x45e6ac, 0x45e6a8, 0x45e6a4, H.SV]:
        a.b(b'\xa1' + H.u32(va), b'\xab')
    a.b(b'\x89\xc6', b'\xb9' + H.u32(16), b'\xf3\xa5')
    for va, count in [(0x4a0344, 440), (0x4a0a24, 84), (0x45e6b0, 20)]:
        a.b(b'\xbe' + H.u32(va), b'\xb9' + H.u32(count), b'\xf3\xa5')
    a.b(b'\xc3')
    return a.done()

def apply(b):
    info = H.apply(b, 1, SimpleNamespace(BATTLE_START_CALL=0x45c1ae, SEED_CAVE=0x564400, TBATTLE_START=0x436fb4))
    code = snapshot_code()
    assert H.CTL + 0x200 <= SNAPSHOT and SNAPSHOT + len(code) < H.BUF
    off = H.PATCH_RAW_START + SNAPSHOT - H.PATCH_VA
    b[off:off + len(code)] = code
    hdr = 0x1f8 + 8 * 40
    struct.pack_into('<I', b, hdr + 8, STATE_END - H.PATCH_VA)
    struct.pack_into('<I', b, 0x118 + 56, (STATE_END - H.BASE + 0xfff) & ~0xfff)
    info.update(snapshot_va=SNAPSHOT, state_buf=STATE_BUF, state_rec=STATE_REC, state_cap=STATE_CAP,
                state_end=STATE_END, state_overflow=OVERFLOW, snapshot_max_counter=MAX_COUNTER,
                semantic_markers=[dict(name=n, va=va, expected_bytes=b.hex()) for n, va, b in SEMANTIC_MARKERS])
    return info

decode_snapshot = legacy.decode_snapshot
