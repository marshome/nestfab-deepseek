// -*- coding: utf-8 -*-
// Measure the model's own layout, so the allocation sizes can be compared against it.
//
// **THE QUESTION IS ARITHMETIC AND IT HAS TO BE ANSWERED WITH NUMBERS**: the module allocates 0x28 bytes for FlipNester and MultiTorchNester, 0x9E8 for
// FilterNester and 0x48 for LimitedNester. **If the model's objects are larger than the allocation, one of its base parts is too big** -- and three rounds have now
// shown that the base parts are where the errors live.
#include "lcns/nester.hpp"
#include <cstdio>

int main() {
    std::printf("sizeof(Nester)            = 0x%zX\n", sizeof(lcns::Nester));
    std::printf("sizeof(CompositeNester)   = 0x%zX\n", sizeof(lcns::CompositeNester));
    std::printf("sizeof(FlipNester)        = 0x%zX   (the module allocates 0x28)\n", sizeof(lcns::FlipNester));
    std::printf("sizeof(MultiTorchNester)  = 0x%zX   (0x28)\n", sizeof(lcns::MultiTorchNester));
    std::printf("sizeof(FilterNester)      = 0x%zX   (0x9E8)\n", sizeof(lcns::FilterNester));
    std::printf("sizeof(LimitedNester)     = 0x%zX   (0x48)\n", sizeof(lcns::LimitedNester));
    std::printf("sizeof(NestingNester)     = 0x%zX   (direct from Nester)\n", sizeof(lcns::NestingNester));
    std::printf("sizeof(Mt19937)           = 0x%zX\n", sizeof(lcns::Mt19937));
    return 0;
}
