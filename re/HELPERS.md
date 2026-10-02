# The logging and assertion helpers the cheap exports call

Read whole in round 369 because re/EXPORT_QUEUE.md shows that the cheapest unimplemented exports all reach the
module through one of these: 0x64AEA0 alone is what five of the ten cheapest entries call first. Whether such a
call can be left out of an implementation, or has to be reproduced, depends on what it does to memory and on what
it returns -- which is what these listings answer. The bytes of every caller are already embedded in the project
(re/g_embed.py embeds the whole export set), so any claim made from these listings can be checked against the
module by re/check_embeddings.py.

## 0x64AEA0 -- 403 bytes, 53 callers

```asm
0064aea0  push rsi
0064aea1  push rbx
0064aea2  sub rsp, 0x38
0064aea6  movzx eax, byte ptr [rip + 0x4d416b]
0064aead  test al, al
0064aeaf  mov rsi, rcx
0064aeb2  je 0x64af90
0064aeb8  lea rcx, [rip + 0x4d4161]
0064aebf  mov byte ptr [rsp + 0x28], 0
0064aec4  mov qword ptr [rsp + 0x20], rcx
0064aec9  call 0x63f6c0
0064aece  test eax, eax
0064aed0  jne 0x64b00a
0064aed6  mov byte ptr [rsp + 0x28], 1
0064aedb  call 0x1bf40
0064aee0  test rax, rax
0064aee3  mov rbx, rax
0064aee6  je 0x64af4e
0064aee8  mov r8d, 3
0064aeee  mov rcx, rax
0064aef1  lea rdx, [rip + 0x361199]
0064aef8  call 0x978010
0064aefd  test rsi, rsi
0064af00  je 0x64aff0
0064af06  mov rcx, rsi
0064af09  call 0x63f238
0064af0e  mov rdx, rsi
0064af11  mov rcx, rbx
0064af14  mov r8, rax
0064af17  call 0x978010
0064af1c  mov rax, qword ptr [rbx]
0064af1f  mov rax, qword ptr [rax - 0x18]
0064af23  mov rsi, qword ptr [rbx + rax + 0xf0]
0064af2b  test rsi, rsi
0064af2e  je 0x64b011
0064af34  cmp byte ptr [rsi + 0x38], 0
0064af38  je 0x64af60
0064af3a  movsx edx, byte ptr [rsi + 0x43]
0064af3e  mov rcx, rbx
0064af41  call 0x867bf0
0064af46  mov rcx, rax
0064af49  call 0x867df0
0064af4e  cmp byte ptr [rsp + 0x28], 0
0064af53  jne 0x64afd0
0064af55  add rsp, 0x38
0064af59  pop rbx
0064af5a  pop rsi
0064af5b  ret 
0064af5c  nop dword ptr [rax]
0064af60  mov rcx, rsi
0064af63  call 0x8264e0
0064af68  mov rax, qword ptr [rsi]
0064af6b  lea rcx, [rip + 0x1db7ae]
0064af72  mov edx, 0xa
0064af77  mov rax, qword ptr [rax + 0x30]
0064af7b  cmp rax, rcx
0064af7e  je 0x64af3e
0064af80  mov rcx, rsi
0064af83  call rax
0064af85  movsx edx, al
... (truncated in this document; the bytes are embedded in the project)
```

## 0x64E120 -- 209 bytes, 7 callers

```asm
0064e120  push rdi
0064e121  push rsi
0064e122  push rbx
0064e123  sub rsp, 0x30
0064e127  mov rdi, rcx
0064e12a  mov esi, edx
0064e12c  call 0xab20
0064e131  mov byte ptr [rsp + 0x28], 0
0064e136  test rax, rax
0064e139  mov qword ptr [rsp + 0x20], rax
0064e13e  je 0x64e1ca
0064e144  mov rcx, rax
0064e147  call 0x63f6c0
0064e14c  test eax, eax
0064e14e  jne 0x64e1c3
0064e150  mov byte ptr [rsp + 0x28], 1
0064e155  call 0x1bf40
0064e15a  test rax, rax
0064e15d  mov rbx, rax
0064e160  je 0x64e1a9
0064e162  mov r8d, 3
0064e168  mov rcx, rax
0064e16b  lea rdx, [rip + 0x35e71c]
0064e172  call 0x978010
0064e177  mov rdx, rdi
0064e17a  mov rcx, rbx
0064e17d  call 0x9920c0
0064e182  mov r8d, 1
0064e188  mov rcx, rbx
0064e18b  lea rdx, [rip + 0x35e9ec]
0064e192  call 0x978010
0064e197  mov edx, esi
0064e199  mov rcx, rbx
0064e19c  call 0x869d00
0064e1a1  mov rcx, rbx
0064e1a4  call 0x9878c0
0064e1a9  cmp byte ptr [rsp + 0x28], 0
0064e1ae  je 0x64e1bb
0064e1b0  lea rcx, [rsp + 0x20]
0064e1b5  call 0x8761b0
0064e1ba  nop 
0064e1bb  add rsp, 0x30
0064e1bf  pop rbx
0064e1c0  pop rsi
0064e1c1  pop rdi
0064e1c2  ret 
0064e1c3  mov ecx, eax
0064e1c5  call 0x97abf0
0064e1ca  mov ecx, 1
0064e1cf  call 0x97abf0
0064e1d4  cmp byte ptr [rsp + 0x28], 0
0064e1d9  mov rbx, rax
0064e1dc  je 0x64e1e8
0064e1de  lea rcx, [rsp + 0x20]
0064e1e3  call 0x8761b0
0064e1e8  mov rcx, rbx
0064e1eb  call 0x62f280
0064e1f0  nop 
```

## 0x64E630 -- 209 bytes, 10 callers

```asm
0064e630  push rdi
0064e631  push rsi
0064e632  push rbx
0064e633  sub rsp, 0x30
0064e637  mov rdi, rcx
0064e63a  mov esi, edx
0064e63c  call 0xab20
0064e641  mov byte ptr [rsp + 0x28], 0
0064e646  test rax, rax
0064e649  mov qword ptr [rsp + 0x20], rax
0064e64e  je 0x64e6da
0064e654  mov rcx, rax
0064e657  call 0x63f6c0
0064e65c  test eax, eax
0064e65e  jne 0x64e6d3
0064e660  mov byte ptr [rsp + 0x28], 1
0064e665  call 0x1bf40
0064e66a  test rax, rax
0064e66d  mov rbx, rax
0064e670  je 0x64e6b9
0064e672  mov r8d, 3
0064e678  mov rcx, rax
0064e67b  lea rdx, [rip + 0x35e20c]
0064e682  call 0x978010
0064e687  mov rdx, rdi
0064e68a  mov rcx, rbx
0064e68d  call 0x9920c0
0064e692  mov r8d, 1
0064e698  mov rcx, rbx
0064e69b  lea rdx, [rip + 0x35e4dc]
0064e6a2  call 0x978010
0064e6a7  mov edx, esi
0064e6a9  mov rcx, rbx
0064e6ac  call 0x868f70
0064e6b1  mov rcx, rbx
0064e6b4  call 0x9878c0
0064e6b9  cmp byte ptr [rsp + 0x28], 0
0064e6be  je 0x64e6cb
0064e6c0  lea rcx, [rsp + 0x20]
0064e6c5  call 0x8761b0
0064e6ca  nop 
0064e6cb  add rsp, 0x30
0064e6cf  pop rbx
0064e6d0  pop rsi
0064e6d1  pop rdi
0064e6d2  ret 
0064e6d3  mov ecx, eax
0064e6d5  call 0x97abf0
0064e6da  mov ecx, 1
0064e6df  call 0x97abf0
0064e6e4  cmp byte ptr [rsp + 0x28], 0
0064e6e9  mov rbx, rax
0064e6ec  je 0x64e6f8
0064e6ee  lea rcx, [rsp + 0x20]
0064e6f3  call 0x8761b0
0064e6f8  mov rcx, rbx
0064e6fb  call 0x62f280
0064e700  nop 
```

## 0x64ABF0 -- 232 bytes, 3 callers

```asm
0064abf0  push rsi
0064abf1  push rbx
0064abf2  sub rsp, 0x58
0064abf6  movaps xmmword ptr [rsp + 0x40], xmm6
0064abfb  mov rsi, rcx
0064abfe  movapd xmm6, xmm1
0064ac02  call 0xab20
0064ac07  mov byte ptr [rsp + 0x38], 0
0064ac0c  test rax, rax
0064ac0f  mov qword ptr [rsp + 0x30], rax
0064ac14  je 0x64acb1
0064ac1a  mov rcx, rax
0064ac1d  call 0x63f6c0
0064ac22  test eax, eax
0064ac24  jne 0x64acaa
0064ac2a  mov byte ptr [rsp + 0x38], 1
0064ac2f  call 0x1bf40
0064ac34  test rax, rax
0064ac37  mov rbx, rax
0064ac3a  je 0x64ac8c
0064ac3c  mov r8d, 3
0064ac42  mov rcx, rax
0064ac45  lea rdx, [rip + 0x361c42]
0064ac4c  call 0x978010
0064ac51  mov rdx, rsi
0064ac54  mov rcx, rbx
0064ac57  call 0x9920c0
0064ac5c  mov r8d, 1
0064ac62  mov rcx, rbx
0064ac65  movsd qword ptr [rsp + 0x20], xmm6
0064ac6b  lea rdx, [rip + 0x361f0c]
0064ac72  call 0x978010
0064ac77  lea rdx, [rsp + 0x20]
0064ac7c  mov rcx, rbx
0064ac7f  call 0x1c0c0
0064ac84  mov rcx, rbx
0064ac87  call 0x9878c0
0064ac8c  cmp byte ptr [rsp + 0x38], 0
0064ac91  je 0x64ac9e
0064ac93  lea rcx, [rsp + 0x30]
0064ac98  call 0x8761b0
0064ac9d  nop 
0064ac9e  movaps xmm6, xmmword ptr [rsp + 0x40]
0064aca3  add rsp, 0x58
0064aca7  pop rbx
0064aca8  pop rsi
0064aca9  ret 
0064acaa  mov ecx, eax
0064acac  call 0x97abf0
0064acb1  mov ecx, 1
0064acb6  call 0x97abf0
0064acbb  cmp byte ptr [rsp + 0x38], 0
0064acc0  mov rbx, rax
0064acc3  je 0x64accf
0064acc5  lea rcx, [rsp + 0x30]
0064acca  call 0x8761b0
0064accf  mov rcx, rbx
0064acd2  call 0x62f280
0064acd7  nop 
```

## 0x64CA50 -- 211 bytes, 5 callers

```asm
0064ca50  push rdi
0064ca51  push rsi
0064ca52  push rbx
0064ca53  sub rsp, 0x30
0064ca57  mov rdi, rcx
0064ca5a  mov rsi, rdx
0064ca5d  call 0xab20
0064ca62  mov byte ptr [rsp + 0x28], 0
0064ca67  test rax, rax
0064ca6a  mov qword ptr [rsp + 0x20], rax
0064ca6f  je 0x64cafc
0064ca75  mov rcx, rax
0064ca78  call 0x63f6c0
0064ca7d  test eax, eax
0064ca7f  jne 0x64caf5
0064ca81  mov byte ptr [rsp + 0x28], 1
0064ca86  call 0x1bf40
0064ca8b  test rax, rax
0064ca8e  mov rbx, rax
0064ca91  je 0x64cadb
0064ca93  mov r8d, 3
0064ca99  mov rcx, rax
0064ca9c  lea rdx, [rip + 0x35fdeb]
0064caa3  call 0x978010
0064caa8  mov rdx, rdi
0064caab  mov rcx, rbx
0064caae  call 0x9920c0
0064cab3  mov r8d, 1
0064cab9  mov rcx, rbx
0064cabc  lea rdx, [rip + 0x3600bb]
0064cac3  call 0x978010
0064cac8  mov rdx, rsi
0064cacb  mov rcx, rbx
0064cace  call 0x868490
0064cad3  mov rcx, rbx
0064cad6  call 0x9878c0
0064cadb  cmp byte ptr [rsp + 0x28], 0
0064cae0  je 0x64caed
0064cae2  lea rcx, [rsp + 0x20]
0064cae7  call 0x8761b0
0064caec  nop 
0064caed  add rsp, 0x30
0064caf1  pop rbx
0064caf2  pop rsi
0064caf3  pop rdi
0064caf4  ret 
0064caf5  mov ecx, eax
0064caf7  call 0x97abf0
0064cafc  mov ecx, 1
0064cb01  call 0x97abf0
0064cb06  cmp byte ptr [rsp + 0x28], 0
0064cb0b  mov rbx, rax
0064cb0e  je 0x64cb1a
0064cb10  lea rcx, [rsp + 0x20]
0064cb15  call 0x8761b0
0064cb1a  mov rcx, rbx
0064cb1d  call 0x62f280
0064cb22  nop 
```

## 0x64ACE0 -- 435 bytes, 6 callers

```asm
0064ace0  push rdi
0064ace1  push rsi
0064ace2  push rbx
0064ace3  sub rsp, 0x30
0064ace7  movzx eax, byte ptr [rip + 0x4d4342]
0064acee  test al, al
0064acf0  mov rsi, rcx
0064acf3  mov edi, edx
0064acf5  je 0x64adf0
0064acfb  lea rcx, [rip + 0x4d4336]
0064ad02  mov byte ptr [rsp + 0x28], 0
0064ad07  mov qword ptr [rsp + 0x20], rcx
0064ad0c  call 0x63f6c0
0064ad11  test eax, eax
0064ad13  jne 0x64ae6a
0064ad19  mov byte ptr [rsp + 0x28], 1
0064ad1e  call 0x1bf40
0064ad23  test rax, rax
0064ad26  mov rbx, rax
0064ad29  je 0x64adb4
0064ad2f  mov r8d, 3
0064ad35  mov rcx, rax
0064ad38  lea rdx, [rip + 0x361621]
0064ad3f  call 0x978010
0064ad44  test rsi, rsi
0064ad47  je 0x64ae50
0064ad4d  mov rcx, rsi
0064ad50  call 0x63f238
0064ad55  mov rdx, rsi
0064ad58  mov rcx, rbx
0064ad5b  mov r8, rax
0064ad5e  call 0x978010
0064ad63  mov r8d, 1
0064ad69  mov rcx, rbx
0064ad6c  lea rdx, [rip + 0x3615f1]
0064ad73  call 0x978010
0064ad78  mov edx, edi
0064ad7a  mov rcx, rbx
0064ad7d  call 0x869d00
0064ad82  mov rax, qword ptr [rbx]
0064ad85  mov rax, qword ptr [rax - 0x18]
0064ad89  mov rsi, qword ptr [rbx + rax + 0xf0]
0064ad91  test rsi, rsi
0064ad94  je 0x64ae71
0064ad9a  cmp byte ptr [rsi + 0x38], 0
0064ad9e  je 0x64adc3
0064ada0  movsx edx, byte ptr [rsi + 0x43]
0064ada4  mov rcx, rbx
0064ada7  call 0x867bf0
0064adac  mov rcx, rax
0064adaf  call 0x867df0
0064adb4  cmp byte ptr [rsp + 0x28], 0
0064adb9  jne 0x64ae30
0064adbb  add rsp, 0x30
0064adbf  pop rbx
0064adc0  pop rsi
0064adc1  pop rdi
0064adc2  ret 
0064adc3  mov rcx, rsi
0064adc6  call 0x8264e0
... (truncated in this document; the bytes are embedded in the project)
```

## 0x64B040 -- 380 bytes, 5 callers

```asm
0064b040  push rbp
0064b041  push rdi
0064b042  push rsi
0064b043  push rbx
0064b044  sub rsp, 0x78
0064b048  mov rbp, rcx
0064b04b  mov rdi, rdx
0064b04e  call 0xab20
0064b053  mov byte ptr [rsp + 0x28], 0
0064b058  test rax, rax
0064b05b  mov qword ptr [rsp + 0x20], rax
0064b060  je 0x64b166
0064b066  mov rcx, rax
0064b069  call 0x63f6c0
0064b06e  test eax, eax
0064b070  jne 0x64b15f
0064b076  mov byte ptr [rsp + 0x28], 1
0064b07b  call 0x1bf40
0064b080  test rax, rax
0064b083  mov rbx, rax
0064b086  je 0x64b144
0064b08c  mov r8d, 3
0064b092  mov rcx, rax
0064b095  lea rdx, [rip + 0x3617f2]
0064b09c  call 0x978010
0064b0a1  mov rdx, qword ptr [rdi]
0064b0a4  lea rsi, [rsp + 0x30]
0064b0a9  lea rax, [rsi + 0x10]
0064b0ad  mov rcx, rsi
0064b0b0  mov qword ptr [rsp + 0x30], rax
0064b0b5  mov r8, rdx
0064b0b8  add r8, qword ptr [rdi + 8]
0064b0bc  call 0xab90
0064b0c1  mov rdx, rbp
0064b0c4  mov rcx, rbx
0064b0c7  call 0x9920c0
0064b0cc  mov rdx, qword ptr [rsp + 0x30]
0064b0d1  lea rdi, [rsp + 0x50]
0064b0d6  lea rax, [rdi + 0x10]
0064b0da  mov rcx, rdi
0064b0dd  mov qword ptr [rsp + 0x50], rax
0064b0e2  mov r8, rdx
0064b0e5  add r8, qword ptr [rsp + 0x38]
0064b0ea  call 0xab90
0064b0ef  mov r8d, 1
0064b0f5  mov rcx, rbx
0064b0f8  lea rdx, [rip + 0x361a7f]
0064b0ff  call 0x978010
0064b104  mov r8, qword ptr [rsp + 0x58]
0064b109  mov rcx, rbx
0064b10c  mov rdx, qword ptr [rsp + 0x50]
0064b111  call 0x978010
0064b116  mov rcx, qword ptr [rsp + 0x50]
0064b11b  add rdi, 0x10
0064b11f  cmp rcx, rdi
0064b122  je 0x64b129
0064b124  call 0x9984b0
0064b129  mov rcx, qword ptr [rsp + 0x30]
0064b12e  add rsi, 0x10
0064b132  cmp rcx, rsi
... (truncated in this document; the bytes are embedded in the project)
```

## 0x62F280 -- 171 bytes, 5209 callers (round 374)

The highest-leverage internal function left: the three box routines behind GetLength, GetHeight and GetFillRatio all
end by calling it, and re/EXPORT_QUEUE.md counts it as the blocker of 100 unimplemented entries. It is not itself an
export, so it is read as a part rather than as an entry point.

```asm
0062f280  push rbp
0062f281  push rdi
0062f282  push rsi
0062f283  push rbx
0062f284  sub rsp, 0x688
0062f28b  xor eax, eax
0062f28d  lea rsi, [rsp + 0x30]
0062f292  mov rbx, rcx
0062f295  mov ecx, 0x13
0062f29a  mov dword ptr [rsp + 0x1e0], 0x10001f
0062f2a5  lea rbp, [rsp + 0xd0]
0062f2ad  mov rdi, rsi
0062f2b0  rep stosq qword ptr [rdi], rax
0062f2b3  mov ecx, 0x1b
0062f2b8  mov rdi, rbp
0062f2bb  mov qword ptr [rsp + 0x50], rbx
0062f2c0  rep stosq qword ptr [rdi], rax
0062f2c3  mov rax, qword ptr [rbx + 0x18]
0062f2c7  lea rdi, [rsp + 0x1b0]
0062f2cf  mov dword ptr [rsp + 0x30], 0x20474343
0062f2d7  mov rcx, rdi
0062f2da  mov dword ptr [rsp + 0x34], 1
0062f2e2  mov dword ptr [rsp + 0x48], 4
0062f2ea  mov qword ptr [rsp + 0x58], rax
0062f2ef  mov rax, qword ptr [rbx + 0x20]
0062f2f3  mov qword ptr [rsp + 0x60], rax
0062f2f8  mov rax, qword ptr [rbx + 0x28]
0062f2fc  mov qword ptr [rsp + 0x68], rax
0062f301  call qword ptr [rip + 0x4f9815]
0062f307  mov rdx, qword ptr [rbx + 0x20]
0062f30b  mov r9, rbx
0062f30e  mov r8, rsi
0062f311  mov rcx, qword ptr [rbx + 0x18]
0062f315  mov qword ptr [rsp + 0x28], rbp
0062f31a  mov qword ptr [rsp + 0x20], rdi
0062f31f  call qword ptr [rip + 0x4f9807]
0062f325  call 0x63f420
0062f32a  nop 
```
