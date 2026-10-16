"""Task-local extension of the tested battle observer: control flags and timing.

Adds entry markers at setup, control predicate, general-on and Walk. Reserved
record word holds the four bytes at 0x45e6a4 (attacker/defender general, end,
interrupted). Only observer output is changed; game fields are never written.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'patches'))
import battle_hook as H


def configure():
    if getattr(H,'oct16_configured',False):return
    base=H.Asm
    class FlagsAsm(base):
        def b(self,*chunks):
            if chunks==(b'\x31\xc0',b'\x89\x46\x28'):
                chunks=(b'\xa1'+H.u32(0x45e6a4),chunks[1])
            return super().b(*chunks)
    H.Asm=FlagsAsm
    H.MARKERS+= (
        ('setup',0x439968,bytes.fromhex('558bec83c4b8')),
        ('control_predicate',0x438378,bytes.fromhex('0fbf05aae64500')),
        ('general_on',0x437ab8,bytes.fromhex('66833d780b4a0000')),
        ('walk',0x438d24,bytes.fromhex('558bec83c4e8')),
    )
    H.oct16_configured=True


configure()
