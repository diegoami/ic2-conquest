00448aa4 push ebx
00448aa5 push esi
00448aa6 push edi
00448aa7 push ebp
00448aa8 add esp, -0x14
00448aab mov edi, 0x474670
00448ab0 call 0x402744
00448ab5 mov eax, dword ptr [0x45e62c]
00448aba call 0x423290
00448abf mov word ptr [esp], ax
00448ac3 mov byte ptr [0x4a0334], 0
00448aca mov byte ptr [0x4a0b7c], 0
00448ad1 mov byte ptr [0x4a0b7d], 0
00448ad8 mov word ptr [0x4a032e], 0
00448ae1 mov word ptr [0x4a0330], 1
00448aea mov word ptr [0x4a0332], 0x10e
00448af3 mov word ptr [0x49f008], 0xffff
00448afc mov word ptr [0x4a031c], 0xffff
00448b05 mov word ptr [0x4a031e], 0x1a
00448b0e call 0x449130
00448b13 call 0x451304
00448b18 xor esi, esi
00448b1a mov dword ptr [esp + 4], edi
00448b1e mov dword ptr [esp + 8], 0x49dc68
00448b26 mov eax, dword ptr [esp + 4]
00448b2a mov ebx, eax
00448b2c mov eax, 0xc
00448b31 call 0x40284c
00448b36 imul eax, eax, 0xd
00448b39 mov edx, dword ptr [esp + 8]
00448b3d lea edx, [edx + eax*2]
00448b40 lea eax, [ebx + 0xb]
00448b43 call 0x405b00
00448b48 mov byte ptr [ebx + 0x490], 0
00448b4f lea eax, [ebx + 0x450]
00448b55 mov ebx, eax
00448b57 mov byte ptr [ebx + 0x1b], 1
00448b5b mov byte ptr [ebx + 0x1c], 1
00448b5f mov word ptr [ebx + 0x36], 0x2d
00448b65 mov word ptr [ebx + 0x38], 0x37
00448b6b mov word ptr [ebx + 0x3a], si
00448b6f mov word ptr [ebx + 0x3c], 0x1e
00448b75 mov word ptr [ebx + 0x3e], 0x14
00448b7b lea ebp, [ebx + 0x1e]
00448b7e mov word ptr [ebp], 2
00448b84 lea edx, [esp + 0xc]
00448b88 mov eax, dword ptr [0x4a0bd0]
00448b8d mov ecx, dword ptr [eax]
00448b8f call dword ptr [ecx + 0x28]
00448b92 mov ax, word ptr [esp + 0x10]
00448b97 add ax, 0x1e
00448b9b dec eax
00448b9c mov word ptr [ebp + 2], ax
00448ba0 mov word ptr [ebp + 6], 0x140
00448ba6 mov word ptr [ebp + 4], 0xaa
00448bac lea ebp, [ebx + 0x26]
00448baf mov word ptr [ebp], 0x14c
00448bb5 lea edx, [esp + 0xc]
00448bb9 mov eax, dword ptr [0x4a0bd0]
00448bbe mov ecx, dword ptr [eax]
00448bc0 call dword ptr [ecx + 0x28]
00448bc3 mov ax, word ptr [esp + 0x10]
00448bc8 add ax, 0x1e
00448bcc dec eax
00448bcd mov word ptr [ebp + 2], ax
00448bd1 cmp word ptr [esp], 0x258
00448bd7 jl 0x448be7
00448bd9 mov word ptr [ebp + 6], 0x1af
00448bdf mov word ptr [ebp + 4], 0x1cd
00448be5 jmp 0x448bf3
00448be7 mov word ptr [ebp + 6], 0x12f
00448bed mov word ptr [ebp + 4], 0x16d
00448bf3 lea eax, [ebx + 0x2e]
00448bf6 mov ebx, eax
00448bf8 mov word ptr [ebx], 2
00448bfd lea edx, [esp + 0xc]
00448c01 mov eax, dword ptr [0x4a0bd0]
00448c06 mov ecx, dword ptr [eax]
00448c08 call dword ptr [ecx + 0x28]
00448c0b mov ax, word ptr [esp + 0x10]
00448c10 add ax, 0x1e
00448c14 add ax, 0xc2
00448c18 mov word ptr [ebx + 2], ax
00448c1c mov word ptr [ebx + 6], 0x140
00448c22 mov ax, word ptr [esp]
00448c26 sub ax, 0x13c
00448c2a mov word ptr [ebx + 4], ax
00448c2e inc esi
00448c2f add dword ptr [esp + 8], 0x138
00448c37 add dword ptr [esp + 4], 0x494
00448c3f cmp si, 0x10
00448c43 jne 0x448b26
00448c49 xor esi, esi
00448c4b mov eax, 0x49efe8
00448c50 mov word ptr [eax], si
00448c53 inc esi
00448c54 add eax, 2
00448c57 cmp si, 0x10
00448c5b jne 0x448c50
00448c5d mov si, 0x10
00448c61 mov ebx, 0x49efe8
00448c66 mov eax, 0x10
00448c6b call 0x40284c
00448c70 lea edx, [eax*2 + 0x49efe8]
00448c77 mov eax, ebx
00448c79 call 0x448fe0
00448c7e add ebx, 2
00448c81 dec si
00448c84 jne 0x448c66
00448c86 mov word ptr [0x4a0322], 0
00448c8f mov ax, word ptr [0x49efe8]
00448c95 mov word ptr [0x4a0320], ax
00448c9b mov dword ptr [edi + 0x424], 0x800080
00448ca5 mov dword ptr [edi + 0x428], 0xffffff
00448caf mov dword ptr [edi + 0x42c], 0xff0000
00448cb9 mov dword ptr [edi + 0x8b8], 0xff
00448cc3 xor eax, eax
00448cc5 mov dword ptr [edi + 0x8bc], eax
00448ccb mov dword ptr [edi + 0x8c0], 0xffffff
00448cd5 mov dword ptr [edi + 0xd4c], 0x8080
00448cdf mov dword ptr [edi + 0xd50], 0xffffff
00448ce9 mov dword ptr [edi + 0xd54], 0x80
00448cf3 mov dword ptr [edi + 0x11e0], 0x800000
00448cfd mov dword ptr [edi + 0x11e4], 0xffffff
00448d07 mov dword ptr [edi + 0x11e8], 0xff00ff
00448d11 mov dword ptr [edi + 0x1674], 0xffffff
00448d1b mov dword ptr [edi + 0x1678], 0xff0000
00448d25 mov dword ptr [edi + 0x167c], 0x808080
00448d2f mov dword ptr [edi + 0x1b08], 0xff00
00448d39 xor eax, eax
00448d3b mov dword ptr [edi + 0x1b0c], eax
00448d41 mov dword ptr [edi + 0x1b10], 0x808080
00448d4b mov dword ptr [edi + 0x1f9c], 0x80
00448d55 mov dword ptr [edi + 0x1fa0], 0xffff00
00448d5f mov dword ptr [edi + 0x1fa4], 0x808080
00448d69 mov dword ptr [edi + 0x2430], 0xffff00
00448d73 xor eax, eax
00448d75 mov dword ptr [edi + 0x2434], eax
00448d7b mov dword ptr [edi + 0x2438], 0xff00ff
00448d85 mov dword ptr [edi + 0x28c4], 0xffff
00448d8f xor eax, eax
00448d91 mov dword ptr [edi + 0x28c8], eax
00448d97 mov dword ptr [edi + 0x28cc], 0xff
00448da1 mov dword ptr [edi + 0x2d58], 0x800000
00448dab mov dword ptr [edi + 0x2d5c], 0x8080
00448db5 mov dword ptr [edi + 0x2d60], 0xffff00
00448dbf mov dword ptr [edi + 0x31ec], 0x8000
00448dc9 xor eax, eax
00448dcb mov dword ptr [edi + 0x31f0], eax
00448dd1 mov dword ptr [edi + 0x31f4], 0xffff
00448ddb mov dword ptr [edi + 0x3680], 0x808000
00448de5 xor eax, eax
00448de7 mov dword ptr [edi + 0x3684], eax
00448ded mov dword ptr [edi + 0x3688], 0xff0000
00448df7 mov dword ptr [edi + 0x3b14], 0xff0000
00448e01 xor eax, eax
00448e03 mov dword ptr [edi + 0x3b18], eax
00448e09 mov dword ptr [edi + 0x3b1c], 0xffff00
00448e13 mov dword ptr [edi + 0x3fa8], 0xff00ff
00448e1d xor eax, eax
00448e1f mov dword ptr [edi + 0x3fac], eax
00448e25 mov dword ptr [edi + 0x3fb0], 0xff
00448e2f mov dword ptr [edi + 0x443c], 0xff
00448e39 mov dword ptr [edi + 0x4440], 0xc0c0c0
00448e43 mov dword ptr [edi + 0x4444], 0x800080
00448e4d mov dword ptr [edi + 0x48d0], 0x808080
00448e57 mov dword ptr [edi + 0x48d4], 0xffffff
00448e61 xor eax, eax
00448e63 mov dword ptr [edi + 0x48d8], eax
00448e69 add esp, 0x14
00448e6c pop ebp
00448e6d pop edi
00448e6e pop esi
00448e6f pop ebx
00448e70 ret 
