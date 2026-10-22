00445b22 .byte 0xff
00445b23 dec dword ptr [esi]
00445b25 add byte ptr [eax], al
00445b27 add byte ptr [ebx + 0x62], dh
00445b2a pop edi
00445b2b outsw dx, word ptr [esi]
00445b2d jb 0x445ba3
00445b2f imul esp, dword ptr [esi + 0x79], 0x79746963
00445b36 add byte ptr [eax], al
00445b38 push ebx
00445b39 push esi
00445b3a push edi
00445b3b push ebp
00445b3c add esp, -8
00445b3f mov dword ptr [esp], edx
00445b42 mov esi, eax
00445b44 mov dl, 1
00445b46 mov eax, 0x418b10
00445b4b call 0x41cdd8
00445b50 mov dword ptr [esp + 4], eax
00445b54 movsx eax, word ptr [0x4a0320]
00445b5b imul eax, eax, 0x125
00445b61 lea eax, [eax*4 + 0x474ac0]
00445b68 mov dx, word ptr [esp]
00445b6c mov edi, edx
00445b6e sub di, word ptr [eax + 0x38]
00445b72 mov bp, word ptr [esp + 2]
00445b77 sub bp, word ptr [eax + 0x36]
00445b7b movsx eax, word ptr [esp + 2]
00445b80 movsx edx, dx
00445b83 imul edx, edx, 0x23
00445b86 lea edx, [edx*8 + 0x45e870]
00445b8d mov bx, word ptr [edx + eax*2]
00445b91 movsx eax, bx
00445b94 cmp eax, 0x44
00445b97 jge 0x445bb9
00445b99 sub eax, 0xc
00445b9c jb 0x445beb
00445b9e add eax, -8
00445ba1 sub eax, 0x10
00445ba4 jb 0x445c02
00445ba6 sub eax, 0x10
00445ba9 jb 0x445c1c
00445bab sub eax, 0x10
00445bae jb 0x445c36
00445bb4 jmp 0x445d04
00445bb9 add eax, -0x44
00445bbc sub eax, 0x10
00445bbf jb 0x445c50
00445bc5 sub eax, 0x10
00445bc8 jb 0x445c6a
00445bce add eax, -0x64
00445bd1 sub eax, 0x30
00445bd4 jb 0x445c84
00445bda add eax, -0x34
00445bdd sub eax, 0x30
00445be0 jb 0x445cc5
00445be6 jmp 0x445d04
00445beb movsx edx, bx
00445bee mov ecx, dword ptr [esp + 4]
00445bf2 mov eax, dword ptr [esi + 0x1b0]
00445bf8 call 0x417200
00445bfd jmp 0x445d04
00445c02 movsx edx, bx
00445c05 sub edx, 0x14
00445c08 mov ecx, dword ptr [esp + 4]
00445c0c mov eax, dword ptr [esi + 0x1c4]
00445c12 call 0x417200
00445c17 jmp 0x445d04
00445c1c movsx edx, bx
00445c1f sub edx, 0x24
00445c22 mov ecx, dword ptr [esp + 4]
00445c26 mov eax, dword ptr [esi + 0x1c8]
00445c2c call 0x417200
00445c31 jmp 0x445d04
00445c36 movsx edx, bx
00445c39 sub edx, 0x34
00445c3c mov ecx, dword ptr [esp + 4]
00445c40 mov eax, dword ptr [esi + 0x1cc]
00445c46 call 0x417200
00445c4b jmp 0x445d04
00445c50 movsx edx, bx
00445c53 sub edx, 0x44
00445c56 mov ecx, dword ptr [esp + 4]
00445c5a mov eax, dword ptr [esi + 0x1d0]
00445c60 call 0x417200
00445c65 jmp 0x445d04
00445c6a movsx edx, bx
00445c6d sub edx, 0x54
00445c70 mov ecx, dword ptr [esp + 4]
00445c74 mov eax, dword ptr [esi + 0x1d4]
00445c7a call 0x417200
00445c7f jmp 0x445d04
00445c84 movsx edx, bx
00445c87 sub edx, 0xc8
00445c8d test edx, edx
00445c8f jns 0x445c94
00445c91 add edx, 0xf
00445c94 sar edx, 4
00445c97 mov ecx, dword ptr [esp + 4]
00445c9b mov eax, dword ptr [esi + 0x1b4]
00445ca1 call 0x417200
00445ca6 lea edx, [esp + 4]
00445caa movsx eax, bx
00445cad sub eax, 0xc8
00445cb2 and eax, 0x8000000f
00445cb7 jns 0x445cbe
00445cb9 dec eax
00445cba or eax, 0xfffffff0
00445cbd inc eax
00445cbe call 0x44a6c8
00445cc3 jmp 0x445d04
00445cc5 movsx edx, bx
00445cc8 sub edx, 0x12c
00445cce test edx, edx
00445cd0 jns 0x445cd5
00445cd2 add edx, 0xf
00445cd5 sar edx, 4
00445cd8 mov ecx, dword ptr [esp + 4]
00445cdc mov eax, dword ptr [esi + 0x1b8]
00445ce2 call 0x417200
00445ce7 lea edx, [esp + 4]
00445ceb movsx eax, bx
00445cee sub eax, 0x12c
00445cf3 and eax, 0x8000000f
00445cf8 jns 0x445cff
00445cfa dec eax
00445cfb or eax, 0xfffffff0
00445cfe inc eax
00445cff call 0x44a6c8
00445d04 mov eax, dword ptr [esp + 4]
