import sys
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from dumputil import dump

T = [
 (0x1bf00, 'h_1bf00'), (0x1bf20, 'h_1bf20'), (0x1bf40, 'h_1bf40'),
 (0x22e30, 'h_22e30'), (0x1ee50, 'h_1ee50'), (0x1e70, 'h_1e70'),
 (0x2bd20, 'http_put'), (0x2b630, 'http_get'),
 (0x26780, 'h_26780'), (0x26840, 'h_26840'),
 (0x63f238, 'h_63f238'), (0x64aea0, 'h_64aea0'), (0x64d9c0, 'h_64d9c0'),
 (0x64dac0, 'h_64dac0'), (0x64e630, 'h_64e630'), (0x24290, 'h_24290'),
 (0xac90, 'h_ac90'), (0x6da1f0, 'http_req_get'), (0x6dbd40, 'http_req_put'),
 (0x6dab80, 'http_parse_a'), (0x6dc480, 'http_parse_b'),
 (0x65a530, 'logging_setup'), (0x7bb430, 'cns_infos'), (0xb8d0, 'source_version'),
 (0x5190b0, 'html_report'), (0x2b630, 'http_get2'),
]
for rva, fn in T:
    p, n = dump(rva, fn)
    print(f"{fn:16s} {rva:#08x} nins={n}")
