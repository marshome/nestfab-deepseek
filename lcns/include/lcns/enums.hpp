// lcns/enums.hpp -- enums recovered from the binary, shared by the DLL layer and the model.
//
// Values decoded from the dump function at RVA 0x511080 (re/REPORT.md 7.4).
#pragma once

#include <cstdint>

namespace lcns {

enum class Objective : int {
    MinimizeX = 0,
    MinimizeY = 1,
    NoOffcut = 2,
    MinimizeArea = 3,
    MinimizeXThenY = 4,
    MinimizeYThenX = 5,
    IntelligentMinimizeX = 6,
    IntelligentMinimizeY = 7,
};

enum class NestingOrigin : int {
    BottomLeft = 0,
    TopLeft = 1,
    BottomRight = 2,
    TopRight = 3,
};

// How well a name/signature is established by the reverse engineering.
enum class Confidence : std::uint8_t {
    Unknown = 0,    // live function whose name had no tracer label
    Inferred = 1,   // name inferred from behaviour
    Recovered = 2,  // name read verbatim from the dbg::symlog entry label
};

}  // namespace lcns
