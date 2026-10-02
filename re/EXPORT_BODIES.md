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

## The implementers behind GetLength and GetHeight (round 371)

GetLength (0xB130) and GetHeight (0xB160) both take the sub-object at [order+0x08] with edx = 0 and tail-call one of
these. Their bodies are the actual geometry, so they are what has to be read before the two exports can be
implemented.

### 0x526160 (GetLength) -- 757 bytes, 171 instructions

```asm
00526160  push r12
00526162  push rbp
00526163  push rdi
00526164  push rsi
00526165  push rbx
00526166  sub rsp, 0xd0
0052616d  mov r12, rcx
00526170  mov dword ptr [rsp + 0x108], edx
00526177  call 0x51d0c0
0052617c  mov rdi, qword ptr [rax + 8]
00526180  cmp qword ptr [rax], rdi
00526183  je 0x526264
00526189  lea rsi, [rsp + 0xa0]
00526191  mov rcx, r12
00526194  call 0x51d0c0
00526199  lea rbp, [rsp + 0x70]
0052619e  pxor xmm0, xmm0
005261a2  mov byte ptr [rsp + 0x70], 1
005261a7  mov rbx, qword ptr [rax]
005261aa  movsd qword ptr [rsp + 0x78], xmm0
005261b0  movsd qword ptr [rsp + 0x80], xmm0
005261b9  mov rdi, qword ptr [rax + 8]
005261bd  movsd qword ptr [rsp + 0x88], xmm0
005261c6  movsd qword ptr [rsp + 0x90], xmm0
005261cf  cmp rbx, rdi
005261d2  je 0x5261f3
005261d4  mov rdx, rbx
005261d7  mov rcx, rsi
005261da  add rbx, 0x78
005261de  call 0x524ee0
005261e3  mov rdx, rsi
005261e6  mov rcx, rbp
005261e9  call 0x5c8c50
005261ee  cmp rdi, rbx
005261f1  jne 0x5261d4
005261f3  mov rcx, r12
005261f6  call 0x51d2f0
005261fb  test rax, rax
005261fe  mov rbx, rax
00526201  je 0x526280
00526203  mov rcx, rbx
00526206  call 0x4f9200
0052620b  mov rcx, rsi
0052620e  mov rdx, rax
00526211  call 0x5cd800
00526216  lea rcx, [rsp + 0x108]
0052621e  call 0x52f810
00526223  test al, al
00526225  jne 0x526244
00526227  movsd xmm0, qword ptr [rsp + 0xb8]
00526230  subsd xmm0, qword ptr [rsp + 0x78]
00526236  add rsp, 0xd0
0052623d  pop rbx
0052623e  pop rsi
0052623f  pop rdi
00526240  pop rbp
00526241  pop r12
00526243  ret 
00526244  movsd xmm0, qword ptr [rsp + 0x88]
0052624d  subsd xmm0, qword ptr [rsp + 0xa8]
00526256  add rsp, 0xd0
0052625d  pop rbx
0052625e  pop rsi
0052625f  pop rdi
00526260  pop rbp
00526261  pop r12
00526263  ret 
00526264  pxor xmm0, xmm0
00526268  add rsp, 0xd0
0052626f  pop rbx
00526270  pop rsi
00526271  pop rdi
00526272  pop rbp
00526273  pop r12
00526275  ret 
00526276  nop word ptr cs:[rax + rax]
00526280  lea rdi, [rsp + 0x50]
00526285  xor r8d, r8d
00526288  mov rcx, rsi
0052628b  mov qword ptr [rsp + 0x50], 0x1b
00526294  lea rax, [rsi + 0x10]
00526298  mov rdx, rdi
0052629b  mov qword ptr [rsp + 0xa0], rax
005262a3  lea rbp, [rsp + 0x30]
005262a8  call 0x910ba0
005262ad  mov rdx, qword ptr [rsp + 0x50]
005262b2  mov ecx, 0x2e67
005262b7  mov r8d, 0x586e
005262bd  mov qword ptr [rsp + 0xa0], rax
005262c5  mov qword ptr [rsp + 0xb0], rdx
005262cd  movabs rdx, 0x2626207465656873
005262d7  mov qword ptr [rax], rdx
005262da  movabs rdx, 0x6e756f626e752220
005262e4  mov qword ptr [rax + 8], rdx
005262e8  movabs rdx, 0x6e697473656e2064
005262f2  mov word ptr [rax + 0x18], cx
005262f6  mov rcx, rbp
005262f9  mov qword ptr [rax + 0x10], rdx
005262fd  mov byte ptr [rax + 0x1a], 0x22
00526301  mov rax, qword ptr [rsp + 0x50]
00526306  mov rdx, qword ptr [rsp + 0xa0]
0052630e  mov qword ptr [rsp + 0xa8], rax
00526316  mov byte ptr [rdx + rax], 0
0052631a  lea rax, [rdi + 0x10]
0052631e  movabs rdx, 0x6f69736e656d6944
00526328  mov qword ptr [rsp + 0x50], rax
0052632d  lea rax, [rbp + 0x10]
00526331  mov qword ptr [rsp + 0x60], rdx
00526336  lea rdx, [rsp + 0x28]
0052633b  mov word ptr [rdi + 0x18], r8w
00526340  xor r8d, r8d
00526343  mov qword ptr [rsp + 0x58], 0xa
0052634c  mov byte ptr [rsp + 0x6a], 0
00526351  mov qword ptr [rsp + 0x30], rax
00526356  mov qword ptr [rsp + 0x28], 0x16
0052635f  call 0x910ba0
00526364  mov rdx, qword ptr [rsp + 0x28]
00526369  mov qword ptr [rsp + 0x30], rax
0052636e  mov r9, rsi
00526371  mov r8, rdi
00526374  mov rcx, rbp
00526377  mov qword ptr [rsp + 0x40], rdx
0052637c  movabs rdx, 0x63757274735c2e2e
00526386  mov qword ptr [rax], rdx
00526389  movabs rdx, 0x6174735c65727574
00526393  mov qword ptr [rax + 8], rdx
00526397  mov edx, 0x7070
0052639c  mov word ptr [rax + 0x14], dx
005263a0  mov rdx, qword ptr [rsp + 0x30]
005263a5  mov dword ptr [rax + 0x10], 0x632e7374
005263ac  mov rax, qword ptr [rsp + 0x28]
005263b1  mov qword ptr [rsp + 0x38], rax
005263b6  mov byte ptr [rdx + rax], 0
005263ba  mov edx, 0x9a
005263bf  call 0x60a620
005263c4  mov rcx, qword ptr [rsp + 0x30]
005263c9  add rbp, 0x10
005263cd  cmp rcx, rbp
005263d0  je 0x5263d7
005263d2  call 0x9984b0
005263d7  mov rcx, qword ptr [rsp + 0x50]
005263dc  add rdi, 0x10
005263e0  cmp rcx, rdi
005263e3  je 0x5263ea
005263e5  call 0x9984b0
005263ea  mov rcx, qword ptr [rsp + 0xa0]
005263f2  lea rax, [rsi + 0x10]
005263f6  cmp rcx, rax
005263f9  je 0x526203
005263ff  call 0x9984b0
00526404  jmp 0x526203
00526409  mov rbx, rax
0052640c  mov rcx, qword ptr [rsp + 0x50]
00526411  add rdi, 0x10
00526415  cmp rcx, rdi
00526418  je 0x52641f
0052641a  call 0x9984b0
0052641f  mov rcx, qword ptr [rsp + 0xa0]
00526427  add rsi, 0x10
0052642b  cmp rcx, rsi
0052642e  je 0x526435
00526430  call 0x9984b0
00526435  mov rcx, rbx
00526438  call 0x62f280
0052643d  mov rcx, qword ptr [rsp + 0x30]
00526442  add rbp, 0x10
00526446  mov rbx, rax
00526449  cmp rcx, rbp
0052644c  je 0x52640c
0052644e  call 0x9984b0
00526453  jmp 0x52640c
```

Shape: NOT a simple double difference (it has calls or branches), so it is recorded, not implemented.

### 0x5266A0 (GetHeight) -- 759 bytes, 171 instructions

```asm
005266a0  push r12
005266a2  push rbp
005266a3  push rdi
005266a4  push rsi
005266a5  push rbx
005266a6  sub rsp, 0xd0
005266ad  mov r12, rcx
005266b0  mov dword ptr [rsp + 0x108], edx
005266b7  call 0x51d0c0
005266bc  mov rdi, qword ptr [rax + 8]
005266c0  cmp qword ptr [rax], rdi
005266c3  je 0x5267b0
005266c9  lea rsi, [rsp + 0xa0]
005266d1  mov rcx, r12
005266d4  call 0x51d0c0
005266d9  lea rbp, [rsp + 0x70]
005266de  pxor xmm0, xmm0
005266e2  mov byte ptr [rsp + 0x70], 1
005266e7  mov rbx, qword ptr [rax]
005266ea  movsd qword ptr [rsp + 0x78], xmm0
005266f0  movsd qword ptr [rsp + 0x80], xmm0
005266f9  mov rdi, qword ptr [rax + 8]
005266fd  movsd qword ptr [rsp + 0x88], xmm0
00526706  movsd qword ptr [rsp + 0x90], xmm0
0052670f  cmp rbx, rdi
00526712  je 0x526733
00526714  mov rdx, rbx
00526717  mov rcx, rsi
0052671a  add rbx, 0x78
0052671e  call 0x524ee0
00526723  mov rdx, rsi
00526726  mov rcx, rbp
00526729  call 0x5c8c50
0052672e  cmp rdi, rbx
00526731  jne 0x526714
00526733  mov rcx, r12
00526736  call 0x51d2f0
0052673b  test rax, rax
0052673e  mov rbx, rax
00526741  je 0x5267c2
00526743  mov rcx, rbx
00526746  call 0x4f9200
0052674b  mov rcx, rsi
0052674e  mov rdx, rax
00526751  call 0x5cd800
00526756  lea rcx, [rsp + 0x108]
0052675e  call 0x52f830
00526763  test al, al
00526765  jne 0x526790
00526767  movsd xmm0, qword ptr [rsp + 0xc0]
00526770  subsd xmm0, qword ptr [rsp + 0x80]
00526779  add rsp, 0xd0
00526780  pop rbx
00526781  pop rsi
00526782  pop rdi
00526783  pop rbp
00526784  pop r12
00526786  ret 
00526787  nop word ptr [rax + rax]
00526790  movsd xmm0, qword ptr [rsp + 0x90]
00526799  subsd xmm0, qword ptr [rsp + 0xb0]
005267a2  add rsp, 0xd0
005267a9  pop rbx
005267aa  pop rsi
005267ab  pop rdi
005267ac  pop rbp
005267ad  pop r12
005267af  ret 
005267b0  pxor xmm0, xmm0
005267b4  add rsp, 0xd0
005267bb  pop rbx
005267bc  pop rsi
005267bd  pop rdi
005267be  pop rbp
005267bf  pop r12
005267c1  ret 
005267c2  lea rdi, [rsp + 0x50]
005267c7  xor r8d, r8d
005267ca  mov rcx, rsi
005267cd  mov qword ptr [rsp + 0x50], 0x1b
005267d6  lea rax, [rsi + 0x10]
005267da  mov rdx, rdi
005267dd  mov qword ptr [rsp + 0xa0], rax
005267e5  lea rbp, [rsp + 0x30]
005267ea  call 0x910ba0
005267ef  mov rdx, qword ptr [rsp + 0x50]
005267f4  mov ecx, 0x2e67
005267f9  mov r8d, 0x596e
005267ff  mov qword ptr [rsp + 0xa0], rax
00526807  mov qword ptr [rsp + 0xb0], rdx
0052680f  movabs rdx, 0x2626207465656873
00526819  mov qword ptr [rax], rdx
0052681c  movabs rdx, 0x6e756f626e752220
00526826  mov qword ptr [rax + 8], rdx
0052682a  movabs rdx, 0x6e697473656e2064
00526834  mov word ptr [rax + 0x18], cx
00526838  mov rcx, rbp
0052683b  mov qword ptr [rax + 0x10], rdx
0052683f  mov byte ptr [rax + 0x1a], 0x22
00526843  mov rax, qword ptr [rsp + 0x50]
00526848  mov rdx, qword ptr [rsp + 0xa0]
00526850  mov qword ptr [rsp + 0xa8], rax
00526858  mov byte ptr [rdx + rax], 0
0052685c  lea rax, [rdi + 0x10]
00526860  movabs rdx, 0x6f69736e656d6944
0052686a  mov qword ptr [rsp + 0x50], rax
0052686f  lea rax, [rbp + 0x10]
00526873  mov qword ptr [rsp + 0x60], rdx
00526878  lea rdx, [rsp + 0x28]
0052687d  mov word ptr [rdi + 0x18], r8w
00526882  xor r8d, r8d
00526885  mov qword ptr [rsp + 0x58], 0xa
0052688e  mov byte ptr [rsp + 0x6a], 0
00526893  mov qword ptr [rsp + 0x30], rax
00526898  mov qword ptr [rsp + 0x28], 0x16
005268a1  call 0x910ba0
005268a6  mov rdx, qword ptr [rsp + 0x28]
005268ab  mov qword ptr [rsp + 0x30], rax
005268b0  mov r9, rsi
005268b3  mov r8, rdi
005268b6  mov rcx, rbp
005268b9  mov qword ptr [rsp + 0x40], rdx
005268be  movabs rdx, 0x63757274735c2e2e
005268c8  mov qword ptr [rax], rdx
005268cb  movabs rdx, 0x6174735c65727574
005268d5  mov qword ptr [rax + 8], rdx
005268d9  mov edx, 0x7070
005268de  mov word ptr [rax + 0x14], dx
005268e2  mov rdx, qword ptr [rsp + 0x30]
005268e7  mov dword ptr [rax + 0x10], 0x632e7374
005268ee  mov rax, qword ptr [rsp + 0x28]
005268f3  mov qword ptr [rsp + 0x38], rax
005268f8  mov byte ptr [rdx + rax], 0
005268fc  mov edx, 0xb0
00526901  call 0x60a620
00526906  mov rcx, qword ptr [rsp + 0x30]
0052690b  add rbp, 0x10
0052690f  cmp rcx, rbp
00526912  je 0x526919
00526914  call 0x9984b0
00526919  mov rcx, qword ptr [rsp + 0x50]
0052691e  add rdi, 0x10
00526922  cmp rcx, rdi
00526925  je 0x52692c
00526927  call 0x9984b0
0052692c  mov rcx, qword ptr [rsp + 0xa0]
00526934  lea rax, [rsi + 0x10]
00526938  cmp rcx, rax
0052693b  je 0x526743
00526941  call 0x9984b0
00526946  jmp 0x526743
0052694b  mov rbx, rax
0052694e  mov rcx, qword ptr [rsp + 0x50]
00526953  add rdi, 0x10
00526957  cmp rcx, rdi
0052695a  je 0x526961
0052695c  call 0x9984b0
00526961  mov rcx, qword ptr [rsp + 0xa0]
00526969  add rsi, 0x10
0052696d  cmp rcx, rsi
00526970  je 0x526977
00526972  call 0x9984b0
00526977  mov rcx, rbx
0052697a  call 0x62f280
0052697f  mov rcx, qword ptr [rsp + 0x30]
00526984  add rbp, 0x10
00526988  mov rbx, rax
0052698b  cmp rcx, rbp
0052698e  je 0x52694e
00526990  call 0x9984b0
00526995  jmp 0x52694e
```

Shape: NOT a simple double difference (it has calls or branches), so it is recorded, not implemented.

## Call graph and tail arithmetic of the box routines (round 373)

Three exports depend on these: GetLength (0xB130) and GetHeight (0xB160) tail-call the first two with the sub-object
at [order+0x08], and GetFillRatio (0xB4B0) tail-calls the third with the nesting container's address (order+0x50).
The calls below are in instruction order; the tail is everything after the last branch target that is still inside
the function.

### 0x526160 -- GetLength's implementer (757 bytes, 171 instructions)

Calls, in order:

* `0x51D0C0` (called from 0x526177), 5 bytes
* `0x51D0C0` (called from 0x526194), 5 bytes
* `0x524EE0` (called from 0x5261DE), 1054 bytes
* `0x5C8C50` (called from 0x5261E9), 255 bytes
* `0x51D2F0` (called from 0x5261F6), 5 bytes
* `0x4F9200` (called from 0x526206), 434 bytes
* `0x5CD800` (called from 0x526211), 610 bytes
* `0x52F810` (called from 0x52621E), 7 bytes
* `0x910BA0` (called from 0x5262A8), 109 bytes
* `0x910BA0` (called from 0x52635F), 109 bytes
* `0x60A620` (called from 0x5263BF), 2620 bytes
* `0x9984B0` (called from 0x5263D2), 5 bytes
* `0x9984B0` (called from 0x5263E5), 5 bytes
* `0x9984B0` (called from 0x5263FF), 5 bytes
* `0x9984B0` (called from 0x52641A), 5 bytes
* `0x9984B0` (called from 0x526430), 5 bytes
* `0x62F280` (called from 0x526438), 171 bytes
* `0x9984B0` (called from 0x52644E), 5 bytes

Last 24 instructions:

```asm
005263f6  cmp rcx, rax
005263f9  je 0x526203
005263ff  call 0x9984b0
00526404  jmp 0x526203
00526409  mov rbx, rax
0052640c  mov rcx, qword ptr [rsp + 0x50]
00526411  add rdi, 0x10
00526415  cmp rcx, rdi
00526418  je 0x52641f
0052641a  call 0x9984b0
0052641f  mov rcx, qword ptr [rsp + 0xa0]
00526427  add rsi, 0x10
0052642b  cmp rcx, rsi
0052642e  je 0x526435
00526430  call 0x9984b0
00526435  mov rcx, rbx
00526438  call 0x62f280
0052643d  mov rcx, qword ptr [rsp + 0x30]
00526442  add rbp, 0x10
00526446  mov rbx, rax
00526449  cmp rcx, rbp
0052644c  je 0x52640c
0052644e  call 0x9984b0
00526453  jmp 0x52640c
```

### 0x5266A0 -- GetHeight's implementer (759 bytes, 171 instructions)

Calls, in order:

* `0x51D0C0` (called from 0x5266B7), 5 bytes
* `0x51D0C0` (called from 0x5266D4), 5 bytes
* `0x524EE0` (called from 0x52671E), 1054 bytes
* `0x5C8C50` (called from 0x526729), 255 bytes
* `0x51D2F0` (called from 0x526736), 5 bytes
* `0x4F9200` (called from 0x526746), 434 bytes
* `0x5CD800` (called from 0x526751), 610 bytes
* `0x52F830` (called from 0x52675E), 10 bytes
* `0x910BA0` (called from 0x5267EA), 109 bytes
* `0x910BA0` (called from 0x5268A1), 109 bytes
* `0x60A620` (called from 0x526901), 2620 bytes
* `0x9984B0` (called from 0x526914), 5 bytes
* `0x9984B0` (called from 0x526927), 5 bytes
* `0x9984B0` (called from 0x526941), 5 bytes
* `0x9984B0` (called from 0x52695C), 5 bytes
* `0x9984B0` (called from 0x526972), 5 bytes
* `0x62F280` (called from 0x52697A), 171 bytes
* `0x9984B0` (called from 0x526990), 5 bytes

Last 24 instructions:

```asm
00526938  cmp rcx, rax
0052693b  je 0x526743
00526941  call 0x9984b0
00526946  jmp 0x526743
0052694b  mov rbx, rax
0052694e  mov rcx, qword ptr [rsp + 0x50]
00526953  add rdi, 0x10
00526957  cmp rcx, rdi
0052695a  je 0x526961
0052695c  call 0x9984b0
00526961  mov rcx, qword ptr [rsp + 0xa0]
00526969  add rsi, 0x10
0052696d  cmp rcx, rsi
00526970  je 0x526977
00526972  call 0x9984b0
00526977  mov rcx, rbx
0052697a  call 0x62f280
0052697f  mov rcx, qword ptr [rsp + 0x30]
00526984  add rbp, 0x10
00526988  mov rbx, rax
0052698b  cmp rcx, rbp
0052698e  je 0x52694e
00526990  call 0x9984b0
00526995  jmp 0x52694e
```

### 0x5297C0 -- GetFillRatio's implementer (881 bytes, 175 instructions)

Calls, in order:

* `0x51C020` (called from 0x5297E0), 4 bytes
* `0x51C020` (called from 0x5297FD), 4 bytes
* `0x51D2F0` (called from 0x52980D), 5 bytes
* `0x4F8D30` (called from 0x529824), 49 bytes
* `0x52F8C0` (called from 0x529838), 11 bytes
* `0x52F8B0` (called from 0x529844), 6 bytes
* `0x522D60` (called from 0x52984C), 528 bytes
* `0x528D10` (called from 0x5298E6), 2493 bytes
* `0x523A40` (called from 0x529923), 1044 bytes
* `0x910BA0` (called from 0x52998A), 109 bytes
* `0x910BA0` (called from 0x529A09), 109 bytes
* `0x60A620` (called from 0x529A75), 2620 bytes
* `0x9984B0` (called from 0x529A8B), 5 bytes
* `0x9984B0` (called from 0x529AA1), 5 bytes
* `0x9984B0` (called from 0x529ABB), 5 bytes
* `0x52F950` (called from 0x529AD0), 37 bytes
* `0x9984B0` (called from 0x529AEE), 5 bytes
* `0x62F280` (called from 0x529AF6), 171 bytes
* `0x9984B0` (called from 0x529B0F), 5 bytes
* `0x9984B0` (called from 0x529B25), 5 bytes

Last 24 instructions:

```asm
00529ad0  call 0x52f950
00529ad5  jmp 0x529829
00529ada  mov rbx, rax
00529add  mov rcx, qword ptr [rsp + 0x80]
00529ae5  add r12, 0x10
00529ae9  cmp rcx, r12
00529aec  je 0x529af3
00529aee  call 0x9984b0
00529af3  mov rcx, rbx
00529af6  call 0x62f280
00529afb  mov rcx, qword ptr [rsp + 0xd0]
00529b03  add rbp, 0x10
00529b07  mov rbx, rax
00529b0a  cmp rcx, rbp
00529b0d  je 0x529b14
00529b0f  call 0x9984b0
00529b14  mov rcx, qword ptr [rsp + 0xa0]
00529b1c  add rsi, 0x10
00529b20  cmp rcx, rsi
00529b23  je 0x529add
00529b25  call 0x9984b0
00529b2a  jmp 0x529add
00529b2c  mov rbx, rax
00529b2f  jmp 0x529b14
```

## The dependency chain behind GetLength, layer by layer (rounds 441 to 447)

0x524EE0 (1051 bytes, 241 instructions) turns one container element into a pair of values. Its dependencies, read from
the top down:

| address | bytes | what it is |
|---|---:|---|
| 0x5F4310 | 35 | stores a pointer at +0, hands +8 to 0x5F3900, stores a byte at +0x10 |
| 0x5F3900 | 22 | stores whatever 0x5F47C0 returns at +0 |
| 0x5F47C0 | 112 | allocates 16 bytes through operator new, stores a constant at +0, makes two IAT calls, then stores the QUOTIENT of their two results as a double at +8. A ratio singleton, and platform-flavoured for that reason |
| 0x5C6BE0 | 65 | clears a 24-byte object, then constructs through 0x8C4530, with 0x8C5090 and the platform stub on the exception path |
| 0x8C4530 | 1209 | the size idiom: (end - begin) shifted by four, multiplied by inv(3), so the element is 48 bytes |
| 0x8C5090 | 147 | the matching destructor, 133 callers, walking the same container |
| 0x5203C0 | 4 | mov eax, dword ptr [rcx + 0x20] -- differentially tested against the original in round 445 |
| 0x547620 | 5 | lea rax, [rcx + 0x18] -- differentially tested against the original in round 445 |

Still to read before this chain is finished: 0x520440 (479 bytes, 55 callers), 0x4F73E0 (530 bytes, 12 callers) and
0x524EE0 itself. The two accessors at the bottom are already held to the original bit for bit, which is what makes this
chain worth walking one layer at a time rather than in one go.

## The 0x52F8xx family (round 375)

GetLength's implementer (0x526160) and GetHeight's (0x5266A0) are otherwise identical and differ in one callee each:
0x52F810 against 0x52F830. That pair is where the length and the height are computed, so these listings are what an
implementation of GetLength (0xB130, ord 96) and GetHeight (0xB160, ord 100) has to be written from.

### 0x52F810 -- 7 bytes, 8 callers, 3 instructions

```asm
0052f810  cmp dword ptr [rcx], 1
0052f813  setbe al
0052f816  ret 
```

### 0x52F830 -- 10 bytes, 4 callers, 3 instructions

```asm
0052f830  test dword ptr [rcx], 0xfffffffd
0052f836  sete al
0052f839  ret 
```

### 0x52F8B0 -- 6 bytes, 4 callers, 2 instructions

```asm
0052f8b0  movsd qword ptr [rcx + 0x18], xmm1
0052f8b5  ret 
```

### 0x52F8C0 -- 11 bytes, 4 callers, 3 instructions

```asm
0052f8c0  movsd qword ptr [rcx + 8], xmm1
0052f8c5  movsd qword ptr [rcx + 0x10], xmm2
0052f8ca  ret 
```

### 0x52F950 -- 37 bytes, 3 callers, 9 instructions

```asm
0052f950  pxor xmm0, xmm0
0052f954  mov rax, rcx
0052f957  mov dword ptr [rcx], 0
0052f95d  movsd qword ptr [rcx + 8], xmm0
0052f962  movsd qword ptr [rcx + 0x10], xmm0
0052f967  movsd qword ptr [rcx + 0x18], xmm0
0052f96c  mov byte ptr [rcx + 0x20], 0
0052f970  mov byte ptr [rcx + 0x21], 0
0052f974  ret 
```

## The four callees reached only from the box routine's loop (round 376)

0x526160 (behind GetLength) has 18 calls, and these four are reached only from inside its loop, so they are where the
container's elements are actually turned into the scalar the export returns. 0x5266A0 (behind GetHeight) shares them.

### 0x524EE0 -- 1054 bytes, 22 callers, 241 instructions

```asm
00524ee0  push r13
00524ee2  push r12
00524ee4  push rbp
00524ee5  push rdi
00524ee6  push rsi
00524ee7  push rbx
00524ee8  sub rsp, 0x108
00524eef  movaps xmmword ptr [rsp + 0xf0], xmm7
00524ef7  xor r8d, r8d
00524efa  lea rdi, [rsp + 0x50]
00524eff  mov r12, rdx
00524f02  mov rbp, rcx
00524f05  lea rdx, [rip + 0x5fde74]
00524f0c  mov rcx, rdi
00524f0f  call 0x5f4310
00524f14  mov rcx, r12
00524f17  call 0x520440
00524f1c  test rax, rax
00524f1f  je 0x5250b7
00524f25  mov rcx, r12
00524f28  call 0x5203c0
00524f2d  mov rcx, r12
00524f30  mov ebx, eax
00524f32  call 0x520440
00524f37  mov edx, ebx
00524f39  mov rcx, rax
00524f3c  call 0x4f73e0
00524f41  mov rcx, rax
00524f44  call 0x547620
00524f49  lea r13, [rsp + 0x70]
00524f4e  mov rdx, rax
00524f51  mov rcx, r13
00524f54  call 0x5c6be0
00524f59  lea rcx, [rsp + 0x30]
00524f5e  mov rdx, r12
00524f61  call 0x5203d0
00524f66  lea rbx, [rsp + 0xd0]
00524f6e  mov rdx, r12
00524f71  movdqu xmm7, xmmword ptr [rsp + 0x30]
00524f77  mov rcx, rbx
00524f7a  call 0x5203f0
00524f7f  lea r9, [rsp + 0x20]
00524f84  mov r8, rbx
00524f87  mov rdx, r13
00524f8a  movaps xmmword ptr [rsp + 0x20], xmm7
00524f8f  lea rsi, [rsp + 0xb0]
00524f97  mov rcx, rsi
00524f9a  call 0x5d3ea0
00524f9f  mov rdx, rsi
00524fa2  mov rcx, rbp
00524fa5  call 0x5cd800
00524faa  mov r13, qword ptr [rsp + 0xb8]
00524fb2  mov r12, qword ptr [rsp + 0xb0]
00524fba  cmp r13, r12
00524fbd  je 0x525017
00524fbf  nop 
00524fc0  mov rsi, qword ptr [r12 + 0x20]
00524fc5  mov rbx, qword ptr [r12 + 0x18]
00524fca  cmp rsi, rbx
00524fcd  je 0x524feb
... (241 instructions in total)
```

### 0x5C8C50 -- 255 bytes, 56 callers, 62 instructions

```asm
005c8c50  cmp byte ptr [rdx], 0
005c8c53  je 0x5c8c60
005c8c55  ret 
005c8c56  nop word ptr cs:[rax + rax]
005c8c60  cmp byte ptr [rcx], 0
005c8c63  jne 0x5c8d10
005c8c69  movsd xmm0, qword ptr [rdx + 8]
005c8c6e  movsd xmm1, qword ptr [rcx + 8]
005c8c73  ucomisd xmm1, xmm0
005c8c77  jbe 0x5c8c88
005c8c79  movsd qword ptr [rcx + 8], xmm0
005c8c7e  movsd xmm0, qword ptr [rdx + 8]
005c8c83  movsd xmm1, qword ptr [rcx + 8]
005c8c88  ucomisd xmm0, qword ptr [rcx + 0x18]
005c8c8d  jbe 0x5c8c94
005c8c8f  movsd qword ptr [rcx + 0x18], xmm0
005c8c94  movsd xmm0, qword ptr [rdx + 0x10]
005c8c99  movsd xmm3, qword ptr [rcx + 0x10]
005c8c9e  ucomisd xmm3, xmm0
005c8ca2  jbe 0x5c8cb2
005c8ca4  movsd qword ptr [rcx + 0x10], xmm0
005c8ca9  movapd xmm3, xmm0
005c8cad  movsd xmm0, qword ptr [rdx + 0x10]
005c8cb2  movsd xmm2, qword ptr [rcx + 0x20]
005c8cb7  ucomisd xmm0, xmm2
005c8cbb  jbe 0x5c8cc6
005c8cbd  movsd qword ptr [rcx + 0x20], xmm0
005c8cc2  movapd xmm2, xmm0
005c8cc6  movsd xmm0, qword ptr [rdx + 0x18]
005c8ccb  ucomisd xmm1, xmm0
005c8ccf  jbe 0x5c8cdb
005c8cd1  movsd qword ptr [rcx + 8], xmm0
005c8cd6  movsd xmm0, qword ptr [rdx + 0x18]
005c8cdb  ucomisd xmm0, qword ptr [rcx + 0x18]
005c8ce0  jbe 0x5c8ce7
005c8ce2  movsd qword ptr [rcx + 0x18], xmm0
005c8ce7  movsd xmm0, qword ptr [rdx + 0x20]
005c8cec  ucomisd xmm3, xmm0
005c8cf0  jbe 0x5c8cfc
005c8cf2  movsd qword ptr [rcx + 0x10], xmm0
005c8cf7  movsd xmm0, qword ptr [rdx + 0x20]
005c8cfc  ucomisd xmm0, xmm2
005c8d00  jbe 0x5c8c55
005c8d06  movsd qword ptr [rcx + 0x20], xmm0
005c8d0b  ret 
005c8d0c  nop dword ptr [rax]
005c8d10  mov r9, qword ptr [rdx + 8]
005c8d14  mov byte ptr [rcx], 0
005c8d17  mov r10, qword ptr [rdx + 0x10]
005c8d1b  mov qword ptr [rcx + 8], r9
005c8d1f  movsd xmm1, qword ptr [rcx + 8]
005c8d24  mov qword ptr [rcx + 0x10], r10
005c8d28  mov r9, qword ptr [rdx + 8]
005c8d2c  mov r10, qword ptr [rdx + 0x10]
005c8d30  movsd xmm3, qword ptr [rcx + 0x10]
005c8d35  mov qword ptr [rcx + 0x18], r9
005c8d39  mov qword ptr [rcx + 0x20], r10
005c8d3d  movsd xmm0, qword ptr [rdx + 0x18]
005c8d42  movsd xmm2, qword ptr [rcx + 0x20]
005c8d47  ucomisd xmm1, xmm0
... (62 instructions in total)
```

### 0x4F9200 -- 434 bytes, 21 callers, 97 instructions

```asm
004f9200  push rbp
004f9201  push rdi
004f9202  push rsi
004f9203  push rbx
004f9204  sub rsp, 0x98
004f920b  cmp byte ptr [rcx + 0x100], 0
004f9212  mov rbx, rcx
004f9215  je 0x4f9230
004f9217  lea rax, [rbx + 0x108]
004f921e  add rsp, 0x98
004f9225  pop rbx
004f9226  pop rsi
004f9227  pop rdi
004f9228  pop rbp
004f9229  ret 
004f922a  nop word ptr [rax + rax]
004f9230  lea rdi, [rsp + 0x70]
004f9235  mov ecx, 0x7274
004f923a  xor r8d, r8d
004f923d  mov qword ptr [rsp + 0x78], 0xf
004f9246  lea rax, [rdi + 0x10]
004f924a  mov byte ptr [rsp + 0x68], 0
004f924f  movabs rsi, 0x675f657661685f6d
004f9259  lea rbp, [rsp + 0x50]
004f925e  mov qword ptr [rsp + 0x70], rax
004f9263  lea rax, [rbp + 0x10]
004f9267  mov qword ptr [rsp + 0x80], rsi
004f926f  mov qword ptr [rsp + 0x50], rax
004f9274  lea rsi, [rsp + 0x30]
004f9279  movabs rax, 0x797274656d6f6567
004f9283  mov word ptr [rdi + 0x1c], cx
004f9287  lea rdx, [rsp + 0x28]
004f928c  mov rcx, rsi
004f928f  mov dword ptr [rdi + 0x18], 0x656d6f65
004f9296  mov byte ptr [rdi + 0x1e], 0x79
004f929a  mov qword ptr [rsp + 0x60], rax
004f929f  lea rax, [rsi + 0x10]
004f92a3  mov byte ptr [rsp + 0x8f], 0
004f92ab  mov qword ptr [rsp + 0x58], 8
004f92b4  mov qword ptr [rsp + 0x30], rax
004f92b9  mov qword ptr [rsp + 0x28], 0x16
004f92c2  call 0x910ba0
004f92c7  mov rdx, qword ptr [rsp + 0x28]
004f92cc  mov qword ptr [rsp + 0x30], rax
004f92d1  mov r9, rdi
004f92d4  mov r8, rbp
004f92d7  mov rcx, rsi
004f92da  mov qword ptr [rsp + 0x40], rdx
004f92df  movabs rdx, 0x63757274735c2e2e
004f92e9  mov qword ptr [rax], rdx
004f92ec  movabs rdx, 0x6568735c65727574
004f92f6  mov qword ptr [rax + 8], rdx
004f92fa  mov edx, 0x7070
004f92ff  mov word ptr [rax + 0x14], dx
004f9303  mov rdx, qword ptr [rsp + 0x30]
004f9308  mov dword ptr [rax + 0x10], 0x632e7465
004f930f  mov rax, qword ptr [rsp + 0x28]
004f9314  mov qword ptr [rsp + 0x38], rax
004f9319  mov byte ptr [rdx + rax], 0
004f931d  mov edx, 0x13b
... (97 instructions in total)
```

### 0x5CD800 -- 610 bytes, 112 callers, 145 instructions

```asm
005cd800  push r12
005cd802  push rbp
005cd803  push rdi
005cd804  push rsi
005cd805  push rbx
005cd806  sub rsp, 0xa0
005cd80d  mov rdi, rcx
005cd810  mov rcx, rdx
005cd813  mov rbx, rdx
005cd816  call 0x5c61d0
005cd81b  mov rsi, qword ptr [rax + 8]
005cd81f  cmp qword ptr [rax], rsi
005cd822  je 0x5cd8a0
005cd824  lea rsi, [rsp + 0x70]
005cd829  mov rcx, rbx
005cd82c  call 0x5c61d0
005cd831  mov rcx, qword ptr [rax]
005cd834  call 0x5c5f30
005cd839  mov rcx, rax
005cd83c  call 0x5c5260
005cd841  mov rcx, rdi
005cd844  mov rdx, rax
005cd847  call 0x5cd360
005cd84c  mov rcx, rbx
005cd84f  call 0x5c61d0
005cd854  mov rbp, qword ptr [rax + 8]
005cd858  mov rbx, qword ptr [rax]
005cd85b  cmp rbx, rbp
005cd85e  je 0x5cd88f
005cd860  mov rcx, rbx
005cd863  add rbx, 0x30
005cd867  call 0x5c5f30
005cd86c  mov rcx, rax
005cd86f  call 0x5c5260
005cd874  mov rcx, rsi
005cd877  mov rdx, rax
005cd87a  call 0x5cd360
005cd87f  mov rdx, rsi
005cd882  mov rcx, rdi
005cd885  call 0x5c8c50
005cd88a  cmp rbp, rbx
005cd88d  jne 0x5cd860
005cd88f  mov rax, rdi
005cd892  add rsp, 0xa0
005cd899  pop rbx
005cd89a  pop rsi
005cd89b  pop rdi
005cd89c  pop rbp
005cd89d  pop r12
005cd89f  ret 
005cd8a0  lea rbp, [rsp + 0x50]
005cd8a5  xor r8d, r8d
005cd8a8  mov qword ptr [rsp + 0x50], 0x19
005cd8b1  lea rsi, [rsp + 0x70]
005cd8b6  mov rdx, rbp
005cd8b9  lea rax, [rsi + 0x10]
005cd8bd  mov rcx, rsi
005cd8c0  mov qword ptr [rsp + 0x70], rax
005cd8c5  lea r12, [rsp + 0x30]
005cd8ca  call 0x910ba0
... (145 instructions in total)
```

## 0x5C8C50 in full -- the box merge, now executable (round 378)

Round 377 embedded this block and the classifier marked it callable (no calls, no RIP-relative data, 62
instructions, 56 callers), so tests/test_boxacc.cpp can call the original and compare a C++ model with it bit for
bit. This is the listing that model must reproduce, and it is the common step behind GetLength, GetHeight and the
container construction of 0x5CD800.

```asm
005c8c50  cmp byte ptr [rdx], 0
005c8c53  je 0x5c8c60
005c8c55  ret 
005c8c56  nop word ptr cs:[rax + rax]
005c8c60  cmp byte ptr [rcx], 0
005c8c63  jne 0x5c8d10
005c8c69  movsd xmm0, qword ptr [rdx + 8]
005c8c6e  movsd xmm1, qword ptr [rcx + 8]
005c8c73  ucomisd xmm1, xmm0
005c8c77  jbe 0x5c8c88
005c8c79  movsd qword ptr [rcx + 8], xmm0
005c8c7e  movsd xmm0, qword ptr [rdx + 8]
005c8c83  movsd xmm1, qword ptr [rcx + 8]
005c8c88  ucomisd xmm0, qword ptr [rcx + 0x18]
005c8c8d  jbe 0x5c8c94
005c8c8f  movsd qword ptr [rcx + 0x18], xmm0
005c8c94  movsd xmm0, qword ptr [rdx + 0x10]
005c8c99  movsd xmm3, qword ptr [rcx + 0x10]
005c8c9e  ucomisd xmm3, xmm0
005c8ca2  jbe 0x5c8cb2
005c8ca4  movsd qword ptr [rcx + 0x10], xmm0
005c8ca9  movapd xmm3, xmm0
005c8cad  movsd xmm0, qword ptr [rdx + 0x10]
005c8cb2  movsd xmm2, qword ptr [rcx + 0x20]
005c8cb7  ucomisd xmm0, xmm2
005c8cbb  jbe 0x5c8cc6
005c8cbd  movsd qword ptr [rcx + 0x20], xmm0
005c8cc2  movapd xmm2, xmm0
005c8cc6  movsd xmm0, qword ptr [rdx + 0x18]
005c8ccb  ucomisd xmm1, xmm0
005c8ccf  jbe 0x5c8cdb
005c8cd1  movsd qword ptr [rcx + 8], xmm0
005c8cd6  movsd xmm0, qword ptr [rdx + 0x18]
005c8cdb  ucomisd xmm0, qword ptr [rcx + 0x18]
005c8ce0  jbe 0x5c8ce7
005c8ce2  movsd qword ptr [rcx + 0x18], xmm0
005c8ce7  movsd xmm0, qword ptr [rdx + 0x20]
005c8cec  ucomisd xmm3, xmm0
005c8cf0  jbe 0x5c8cfc
005c8cf2  movsd qword ptr [rcx + 0x10], xmm0
005c8cf7  movsd xmm0, qword ptr [rdx + 0x20]
005c8cfc  ucomisd xmm0, xmm2
005c8d00  jbe 0x5c8c55
005c8d06  movsd qword ptr [rcx + 0x20], xmm0
005c8d0b  ret 
005c8d0c  nop dword ptr [rax]
005c8d10  mov r9, qword ptr [rdx + 8]
005c8d14  mov byte ptr [rcx], 0
005c8d17  mov r10, qword ptr [rdx + 0x10]
005c8d1b  mov qword ptr [rcx + 8], r9
005c8d1f  movsd xmm1, qword ptr [rcx + 8]
005c8d24  mov qword ptr [rcx + 0x10], r10
005c8d28  mov r9, qword ptr [rdx + 8]
005c8d2c  mov r10, qword ptr [rdx + 0x10]
005c8d30  movsd xmm3, qword ptr [rcx + 0x10]
005c8d35  mov qword ptr [rcx + 0x18], r9
005c8d39  mov qword ptr [rcx + 0x20], r10
005c8d3d  movsd xmm0, qword ptr [rdx + 0x18]
005c8d42  movsd xmm2, qword ptr [rcx + 0x20]
005c8d47  ucomisd xmm1, xmm0
005c8d4b  ja 0x5c8cd1
005c8d4d  jmp 0x5c8cdb
```

## GetFillRatio implementer 0x5297C0, head read (round 409)

881 bytes, 175 instructions, 20 calls. The entry hands it the NESTING CONTAINER (rcx = order + 0x50, i.e.
NestingOwner::nestings) and jumps. What the head shows:

    5297DD  rbx = rcx                       ; the container address
    5297E0  call 0x51C020                   ; a begin/end view of it
    5297E5  rdi = [rax] ; cmp [rax+8], rdi ; je 0x529AC5   ; EMPTY CONTAINER returns early
    529802  rcx = [rax+8] - 0x138           ; the LAST element, stride 312 again
    52980D  call 0x51D2F0                   ; its sub-object pointer
    529824  call 0x4F8D30                   ; fills a stack object from it
    529838  call 0x52F8C0                   ; writes +0x08 and +0x10 (read in round 375)
    529844  call 0x52F8B0                   ; writes +0x18
    52984C  call 0x522D60                   ; one more value

Three things this settles. First, the 312-byte stride appears again (sub rcx, 0x138), which is now four independent
confirmations of the element size: 0xB0C0, 0x50FD40, 0x5C8C50 and this. Second, an empty container has an early return,
which any implementation must reproduce. Third, it reuses the two small writers read in round 375, so it builds a
window or range object rather than computing a bare number.

The second half (0x52988A to 0x529B2C), with its loop and its 0x62F280 and 0x9984B0 calls, is where the ratio itself
and the cleanup live, and it is what must be read next before this export can be implemented.

## GetFillRatio implementer 0x5297C0, calculation skeleton (round 411)

The calculation is short; the rest of the 175 instructions are stack object construction, string building and logging on
the error paths.

    529892  xmm3 = [rip + 0x4B237E]      ; one RIP-relative constant
    5298C1  edx = 1                      ; second argument
    5298E6  call 0x528D10                ; the numerator comes back in xmm0
    5298EB  ucomisd xmm0, xmm6           ; xmm6 was cleared, so this compares with zero
    5298F3  jp  0x529920                 ; NaN goes to the division path
    5298F9  jne 0x529920                 ; non-zero goes to the division path, zero returns xmm0 as it stands
    529920  mov rcx, rbx ; call 0x523A40 ; the denominator
    529928  divsd xmm0, xmm7             ; the ratio
    52992C  jmp 0x5298FB                 ; the shared epilogue

So GetFillRatio is a quotient of two calls on the same container, and a zero (or NaN) numerator returns zero without
dividing. The null-sub-object branch at 0x529930 builds a five-character string whose bytes are 0x65656873 and 0x74 --
sheet -- plus a longer literal that begins GetLastUsedFra, and hands it to 0x910BA0, which is the logging or throwing
helper that appears in the cleanup paths of several functions read earlier. That is consistent with round 369: these are
diagnostic paths, not part of the value returned.

Next: read 0x528D10 (the numerator) and 0x523A40 (the denominator). Both are small, and with them GetFillRatio can be
implemented and tested behaviourally, since the original cannot execute from the embedded copy.

## GetFillRatio operators are not small (round 413)

Reading the two calls the skeleton needs showed both to be subsystems, so this export needs two more layers read
before it can be implemented.

| function | role | bytes | instructions |
|---|---|---:|---:|
| 0x528D10 | numerator | 2493 | 477 |
| 0x523A40 | denominator | 1044 | 264 |

The numerator saves ten xmm registers and uses a 0x1d8 frame, so it is a routine in its own right. The denominator
begins with 0x51C250 and, on its error path, builds strings whose bytes read as solution and .IsBound through the
0x910BA0 helper -- consistent with a denominator about a solution being bound, and again a diagnostic path rather than
a returned value. Neither is small, which is why GetFillRatio is listed as needing two more layers rather than guessed at.
