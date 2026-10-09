0x44dba8 push ebp
0x44dba9 mov ebp, esp
0x44dbab add esp, -0x10
0x44dbae push ebx
0x44dbaf push esi
0x44dbb0 mov dword ptr [ebp - 6], edx
0x44dbb3 mov word ptr [ebp - 2], ax
0x44dbb7 movsx eax, word ptr [ebp - 2]
0x44dbbb imul eax, eax, 0x52
0x44dbbe lea ebx, [eax*8 + 0x47c1ec]
0x44dbc5 mov si, word ptr [ebx + 6]
0x44dbc9 cmp word ptr [ebx + 8], -1
0x44dbce jne 0x44dc01
0x44dbd0 mov eax, dword ptr [ebx]
0x44dbd2 call 0x449970
0x44dbd7 lea edx, [ebp - 0xe]
0x44dbda push edx
0x44dbdb movsx edx, ax
0x44dbde imul esi, edx, 0xd
0x44dbe1 lea ecx, [esi*2 + 0x49c270]
0x44dbe8 mov edx, dword ptr [esi*2 + 0x49c26c]
0x44dbef mov eax, dword ptr [ebp - 6]
0x44dbf2 call 0x44cd08
0x44dbf7 sub word ptr [ebx + 6], 2
0x44dbfc jmp 0x44dca6
