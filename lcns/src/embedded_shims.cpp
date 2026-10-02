// lcns/src/embedded_shims.cpp -- the C++ functions a relocated copy jumps to.
//
// A relocated copy rewrites an external call to reach a symbol this project defines, which is how a block that is only
// blocked by a call becomes executable and therefore differentially testable. The shim must have the same ABI as the
// original target, and it must be the project's own behaviour rather than a copy of the original bytes -- otherwise the
// differential test would compare the original with itself and prove nothing.
//
// 0x62FE20 is libm's sqrt (round 356: the name string "sqrt" at rva 0xA06820, EDOM stored through the errno helper), so
// the shim is std::sqrt. The original also sets errno on a negative argument through the library routine; the kernel
// under test can only produce a non-negative sum of squares, so that path is not reachable from it, and the difference
// is recorded here rather than left implicit.

#include <cmath>

extern "C" double lcns_sqrt_shim(double x) {
    return std::sqrt(x);
}
