// tests/check.hpp -- minimal assertion helpers (no external test framework).
#pragma once

#include <cmath>
#include <cstdio>
#include <string>

namespace check {

inline int& failures() {
    static int f = 0;
    return f;
}
inline int& checks() {
    static int c = 0;
    return c;
}

inline void report(const char* file, int line, const char* expr, const std::string& detail) {
    ++failures();
    std::printf("FAIL %s:%d: %s%s%s\n", file, line, expr, detail.empty() ? "" : "  -- ",
                detail.c_str());
}

inline int finish(const char* name) {
    if (failures() == 0) {
        std::printf("PASS %s (%d checks)\n", name, checks());
        return 0;
    }
    std::printf("FAILED %s: %d/%d checks failed\n", name, failures(), checks());
    return 1;
}

}  // namespace check

#define CHECK(expr)                                                             \
    do {                                                                        \
        ++::check::checks();                                                    \
        if (!(expr)) ::check::report(__FILE__, __LINE__, #expr, std::string()); \
    } while (0)

#define CHECK_MSG(expr, msg)                                                          \
    do {                                                                              \
        ++::check::checks();                                                          \
        if (!(expr)) ::check::report(__FILE__, __LINE__, #expr, std::string(msg));    \
    } while (0)

#define CHECK_NEAR(a, b, eps)                                                            \
    do {                                                                                 \
        ++::check::checks();                                                             \
        const double _a = (a), _b = (b);                                                 \
        if (!(std::fabs(_a - _b) <= (eps))) {                                            \
            char _buf[160];                                                              \
            std::snprintf(_buf, sizeof(_buf), "%s=%.12g vs %s=%.12g (eps %.3g)", #a, _a, \
                          #b, _b, static_cast<double>(eps));                             \
            ::check::report(__FILE__, __LINE__, "CHECK_NEAR(" #a "," #b ")", _buf);      \
        }                                                                                \
    } while (0)
