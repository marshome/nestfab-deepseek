# The cheapest read-only exports, read whole (round 370)

re/EXPORT_QUEUE.md ranks these first, and round 369 showed that the logger they call (0x64AEA0) does nothing on its
default path, so their return value is the whole of their behaviour. The listings below are the input for
implementing them, and the note under each is a claim to be checked by the test that lands with the implementation.

## GetBuildVersion (ord 88) -- 0xB490, 31 bytes

```asm
0000b490  sub rsp, 0x28
0000b494  lea rcx, [rip + 0x9a1539]
0000b49b  call 0x64aea0
0000b4a0  mov rax, qword ptr [rip + 0x9fc1b9]
0000b4a7  mov rax, qword ptr [rax]
0000b4aa  add rsp, 0x28
0000b4ae  ret 
```

## GetBuildDate (ord 90) -- 0xB470, 31 bytes

```asm
0000b470  sub rsp, 0x28
0000b474  lea rcx, [rip + 0x9a154c]
0000b47b  call 0x64aea0
0000b480  mov rax, qword ptr [rip + 0x9fc209]
0000b487  mov rax, qword ptr [rax]
0000b48a  add rsp, 0x28
0000b48e  ret 
```

## GetMajorVersion (ord 92) -- 0xB450, 31 bytes

```asm
0000b450  sub rsp, 0x28
0000b454  lea rcx, [rip + 0x9a155c]
0000b45b  call 0x64aea0
0000b460  mov rax, qword ptr [rip + 0x9fc209]
0000b467  mov rax, qword ptr [rax]
0000b46a  add rsp, 0x28
0000b46e  ret 
```

## GetFillRatio (ord 168) -- 0xB4B0, 34 bytes

```asm
0000b4b0  push rbx
0000b4b1  sub rsp, 0x20
0000b4b5  mov rbx, rcx
0000b4b8  lea rcx, [rip + 0x9a1525]
0000b4bf  call 0x64aea0
0000b4c4  lea rcx, [rbx + 0x50]
0000b4c8  add rsp, 0x20
0000b4cc  pop rbx
0000b4cd  jmp 0x5297c0
```

## GetLength (ord 96) -- 0xB130, 36 bytes

```asm
0000b130  push rbx
0000b131  sub rsp, 0x20
0000b135  mov rbx, rcx
0000b138  lea rcx, [rip + 0x9a17ac]
0000b13f  call 0x64aea0
0000b144  mov rcx, qword ptr [rbx + 8]
0000b148  xor edx, edx
0000b14a  add rsp, 0x20
0000b14e  pop rbx
0000b14f  jmp 0x526160
```

## GetHeight (ord 100) -- 0xB160, 36 bytes

```asm
0000b160  push rbx
0000b161  sub rsp, 0x20
0000b165  mov rbx, rcx
0000b168  lea rcx, [rip + 0x9a1786]
0000b16f  call 0x64aea0
0000b174  mov rcx, qword ptr [rbx + 8]
0000b178  xor edx, edx
0000b17a  add rsp, 0x20
0000b17e  pop rbx
0000b17f  jmp 0x5266a0
```

## GetNestingFillRatio (ord 192) -- 0xB4E0, 38 bytes

```asm
0000b4e0  push rbx
0000b4e1  sub rsp, 0x20
0000b4e5  mov rbx, rcx
0000b4e8  lea rcx, [rip + 0x9a1502]
0000b4ef  call 0x64aea0
0000b4f4  movzx edx, byte ptr [rbx + 0x10]
0000b4f8  mov rcx, qword ptr [rbx + 8]
0000b4fc  add rsp, 0x20
0000b500  pop rbx
0000b501  jmp 0x5257d0
```

## GetComputationStatus (ord 15) -- 0x107E0, 155 bytes

```asm
000107e0  push rsi
000107e1  push rbx
000107e2  sub rsp, 0x48
000107e6  lea rax, [rip + 0x99caac]
000107ed  lea rdx, [rip + 0x99ca9f]
000107f4  cmp byte ptr [rcx + 0x48], 0
000107f8  cmove rdx, rax
000107fc  mov rsi, rcx
000107ff  lea rbx, [rsp + 0x20]
00010804  lea rax, [rbx + 0x10]
00010808  mov rcx, rbx
0001080b  lea r8, [rdx + 5]
0001080f  mov qword ptr [rsp + 0x20], rax
00010814  call 0xab90
00010819  lea rcx, [rip + 0x99caff]
00010820  mov rdx, rbx
00010823  call 0x64b040
00010828  mov rcx, qword ptr [rsp + 0x20]
0001082d  add rbx, 0x10
00010831  cmp rcx, rbx
00010834  je 0x1083b
00010836  call 0x9984b0
0001083b  mov rcx, rsi
0001083e  call 0x1be20
00010843  lea rcx, [rip + 0x99caea]
0001084a  mov ebx, eax
0001084c  mov edx, eax
0001084e  call 0x64ace0
00010853  mov eax, ebx
00010855  add rsp, 0x48
00010859  pop rbx
0001085a  pop rsi
0001085b  ret 
0001085c  mov rcx, qword ptr [rsp + 0x20]
00010861  add rbx, 0x10
00010865  mov rsi, rax
00010868  cmp rcx, rbx
0001086b  je 0x10872
0001086d  call 0x9984b0
00010872  mov rcx, rsi
00010875  call 0x62f280
0001087a  nop 
```

