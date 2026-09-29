# Battle-lab probe (not a shipped patch): fast + autosave, plus a fixed battle
# seed and a snapshot save at every half-round of a tactical battle.
#   py lab.py [seed]      -> "IC2 lab.exe" next to the original
import struct, sys
import patch_exe as P

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 12345
RAND_SEED = 0x45E030                    # System.RandSeed
BATTLE_START_CALL = 0x45C1AE            # TPremierForm.StartBattle: call TBattleMap.StartBattle
TBATTLE_START = 0x436FB4                # also the resume path when a battle save is loaded
ROUND_END = 0x439C20                    # end of one side's half-round (melee phase)
ROUND_END_CALLS = (0x439D06, 0x437A94)  # computer side / TBattleMap.EndTurn (human side)
SEED_CAVE, SNAP_CAVE, SAVED, COUNTER = 0x564400, 0x564420, 0x564580, 0x5645F0


def battle_lab(b):
    # RandSeed := SEED whenever a battle starts or resumes; before every
    # half-round, save to BATTLEnn.SAV (the save then carries the battle block).
    raw = lambda va: va - P.EXTRA_VA + P.EXTRA_RAW
    seed = P.assemble(SEED_CAVE, [b"\xC7\x05" + struct.pack("<II", RAND_SEED, SEED), ("jmp", TBATTLE_START)])
    snap = P.assemble(SNAP_CAVE, [
        b"\x60\xFE\x05" + struct.pack("<I", COUNTER),                    # pushad; inc byte [COUNTER]
        b"\xBE" + struct.pack("<I", P.FILE_NAME), b"\xBF" + struct.pack("<I", SAVED),
        b"\xB9\x64\x00\x00\x00\xF3\xA4",                                  # SAVED = FILE_NAME
        b"\xBF" + struct.pack("<I", P.FILE_NAME),                        # FILE_NAME = "BATTLEnn.SAV"
        b"\xC7\x07BATT\xC7\x47\x02TTLE\xC7\x47\x08.SAV\xC6\x47\x0C\x00",
        b"\x0F\xB6\x05" + struct.pack("<I", COUNTER), b"\xD4\x0A\x66\x05\x30\x30",   # movzx; aam; add ax,'00'
        b"\x88\x67\x06\x88\x47\x07",
        ("call", P.SAVE_GAME),
        b"\xBE" + struct.pack("<I", SAVED), b"\xBF" + struct.pack("<I", P.FILE_NAME),
        b"\xB9\x64\x00\x00\x00\xF3\xA4",                                  # FILE_NAME = SAVED
        b"\x61", ("jmp", ROUND_END)])
    b[raw(SEED_CAVE):raw(SEED_CAVE) + len(seed)] = seed
    b[raw(SNAP_CAVE):raw(SNAP_CAVE) + len(snap)] = snap
    b[raw(COUNTER)] = 0
    struct.pack_into("<I", b, P.EXTRA_HEADER + 36, 0xE0000020)          # .patch writable (counter, SAVED)
    P.patch(b, BATTLE_START_CALL, b"\xE8" + P.rel32(BATTLE_START_CALL, TBATTLE_START),
            b"\xE8" + P.rel32(BATTLE_START_CALL, SEED_CAVE))
    for site in ROUND_END_CALLS:
        P.patch(b, site, b"\xE8" + P.rel32(site, ROUND_END), b"\xE8" + P.rel32(site, SNAP_CAVE))


P.build("IC2 lab.exe", P.async_sound, P.no_delay, P.autosave, battle_lab)
