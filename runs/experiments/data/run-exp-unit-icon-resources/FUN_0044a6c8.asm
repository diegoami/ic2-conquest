0044a6c8 push ebx
0044a6c9 push esi
0044a6ca push edi
0044a6cb push ebp
0044a6cc push ecx
0044a6cd mov word ptr [esp], ax
0044a6d1 mov eax, dword ptr [edx]
0044a6d3 call 0x41d198
0044a6d8 mov edi, eax
0044a6da xor esi, esi
0044a6dc xor ebx, ebx
0044a6de movsx ecx, bx
0044a6e1 movsx ebp, si
0044a6e4 mov edx, ebp
0044a6e6 mov eax, edi
0044a6e8 call 0x41a0bc
0044a6ed cmp eax, 0x800080
0044a6f2 jne 0x44a714
0044a6f4 movsx eax, word ptr [esp]
0044a6f8 imul eax, eax, 0x125
0044a6fe mov eax, dword ptr [eax*4 + 0x474a94]
0044a705 push eax
0044a706 movsx ecx, bx
0044a709 mov edx, ebp
0044a70b mov eax, edi
0044a70d call 0x41a0e8
0044a712 jmp 0x44a778
0044a714 movsx ecx, bx
0044a717 mov edx, ebp
0044a719 mov eax, edi
0044a71b call 0x41a0bc
0044a720 cmp eax, 0xffffff
0044a725 jne 0x44a747
0044a727 movsx eax, word ptr [esp]
0044a72b imul eax, eax, 0x125
0044a731 mov eax, dword ptr [eax*4 + 0x474a98]
0044a738 push eax
0044a739 movsx ecx, bx
0044a73c mov edx, ebp
0044a73e mov eax, edi
0044a740 call 0x41a0e8
0044a745 jmp 0x44a778
0044a747 movsx ecx, bx
0044a74a mov edx, ebp
0044a74c mov eax, edi
0044a74e call 0x41a0bc
0044a753 cmp eax, 0xff0000
0044a758 jne 0x44a778
0044a75a movsx eax, word ptr [esp]
0044a75e imul eax, eax, 0x125
0044a764 mov eax, dword ptr [eax*4 + 0x474a9c]
0044a76b push eax
0044a76c movsx ecx, bx
0044a76f mov edx, ebp
0044a771 mov eax, edi
0044a773 call 0x41a0e8
0044a778 inc ebx
0044a779 cmp bx, 0x20
0044a77d jne 0x44a6de
0044a783 inc esi
0044a784 cmp si, 0x20
0044a788 jne 0x44a6dc
0044a78e pop edx
0044a78f pop ebp
0044a790 pop edi
0044a791 pop esi
0044a792 pop ebx
0044a793 ret 
