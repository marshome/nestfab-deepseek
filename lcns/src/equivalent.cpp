// lcns/equivalent.cpp -- see equivalent.hpp for the instruction-level evidence.
#include "lcns/equivalent.hpp"

#include <cstddef>

LCNS_STRUCTURAL(verify.defect_reduction);

namespace lcns {
namespace equivalent {

double reduce(double x, double p) {
    // RE 0x4BCA56 mulsd + 0x4BCA5B subsd, in that order: x - (0.5 * p).
    return x - kDefectWeight * p;
}

bool isValidReduction(double reduction) {
    // RE 0x4BCA60 ucomisd xmm6, xmm7 (zero) plus the function's own assertion text.
    return reduction > 0.0;
}

double reduceFromSource(const double* object, double p) {
    // RE 0x4F9C30 reads a double at +0x58; the offset is in bytes, so index by bytes / 8.
    if (object == nullptr) {
        return 0.0;
    }
    const double x = *(object + (kReductionSourceOffset / sizeof(double)));
    return reduce(x, p);
}

}  // namespace equivalent
}  // namespace lcns
