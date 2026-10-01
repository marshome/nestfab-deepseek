// include/lcns/text_tags.hpp -- the geometry type vocabulary read out of rodata (goal round 198).
//
// The two addresses 0x70C480 hands to 0x978010 resolve to 0x9DF0F5 (a NUL) and 0x9DF0F6 (a single space), so its
// coordinate printer writes x, " ", y. Immediately around them sits a contiguous table of type tags, recovered
// here with the rva each one was found at. This is the project's own text form for its geometry types.
#pragma once

#include "lcns/recovery.hpp"

namespace lcns {

// RE the contiguous tag table, each at the rva noted.
inline constexpr const char* kTagPoint        = "POINT";         // RE rva 0x9DF0ED
inline constexpr const char* kTagVector       = "VECTOR(";       // RE rva 0x9DF0F8
inline constexpr const char* kTagMultiPoint   = "MULTIPOINT(";   // RE rva 0x9DF103
inline constexpr const char* kTagMultiVector  = "MULTIVECTOR(";  // RE rva 0x9DF10F
inline constexpr const char* kTagAngle        = "Angle(";        // RE rva 0x9DF11C
inline constexpr const char* kTagDegreeSuffix = " deg)";         // RE rva 0x9DF123
inline constexpr const char* kTagBoxEmpty     = "BOX(empty)";    // RE rva 0x9DF129
inline constexpr const char* kTagBox          = "BOX(";          // RE rva 0x9DF134
inline constexpr const char* kTagSegment      = "SEGMENT(";      // RE rva 0x9DF140
inline constexpr const char* kTagOrientation  = "ORIENTATION(";  // RE rva 0x9DF155
inline constexpr const char* kTagIn           = "' in (";        // RE rva 0x9DF0E4

// RE 0x7D3581: the message this project reports when the tiling time is up. It is domain text like the type
// table of round 198, recovered in round 217 from 0x7D3530.
inline constexpr const char* kTagTilingCancelled = "Tiling time cancelled !";

// RE 0x9DF0F6, the address loaded at 0x70C4C1 and passed as the format: a single space between coordinates.
inline constexpr const char* kCoordinateSeparator = " ";

// RE 0x9DF139, the separator between elements of a multi-geometry.
inline constexpr const char* kElementSeparator = "), ";

// RE 0x9DF0ED..0x9DF155: the table is contiguous, so these are one enumeration of the modelled types.
inline constexpr int kGeometryTagCount = 10;

}  // namespace lcns
LCNS_STRUCTURAL(io.text_vocabulary);   // type tags, the comma, the cancellation message

// RE 0x77F2F7: the error text an encoder/decoder formatter builds (round 252).
inline constexpr const char* kTagBerDecodeError = "BER decode error";
