The .asm files here are capstone 5.0.7 linear-sweep excerpts of `Imperial Conquest 2.exe` (CODE section, file 0x400 → VA 0x401000, `skipdata`),
made read-only by `capstone.Cs(CS_ARCH_X86, CS_MODE_32).disasm(code, 0x401000)`; one line per instruction, `address mnemonic op_str`.
- `FUN_00448aa4.asm`: new-game nation setup; edi = 0x474670 (nation table), writes the three recolour dwords +0x424/+0x428/+0x42C of every nation as immediates (0x448c9b-0x448e63).
- `FUN_0044a6c8.asm`: recolours a 32x32 bitmap pixel by pixel (TColor 0x800080 -> nation[owner]+0x424, 0xFFFFFF -> +0x428, 0xFF0000 -> +0x42C).
- `unitmap_paint_445b.asm`: the unit-map tile switch: city words index the five city image lists directly; army words (word-200)/16 -> ArmiesList (field 0x1B4) then FUN_0044a6c8(owner=(word-200) mod 16); fleets (word-300) likewise with FleetsList (0x1B8).
