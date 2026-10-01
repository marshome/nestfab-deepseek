// include/lcns/json_backend.hpp -- JsonCpp-backed JSON I/O for the recovered key names (goal round 210).
//
// The goal's download-and-link rule says third-party libraries are referenced directly from the build rather than
// re-implemented. The JSON writer was still the in-house one, so this backend drives the vendored JsonCpp 1.9.5
// for writing and parsing while keeping the recovered key names and the in-house Value as the interface.
#pragma once

#include <string>

#include "lcns/io.hpp"

namespace lcns {
namespace json_backend {

// True when the vendored JsonCpp was found at configure time and is linked in (LCNS_HAS_JSONCPP).
bool available();

// Writes through JsonCpp when available, otherwise through the in-house writer. The key names and value shapes are
// the recovered ones either way.
std::string write(const json::Value& v, bool pretty = false);

// Parses with JsonCpp when available, otherwise with the in-house parser.
json::Value parse(const std::string& text, std::string* error = nullptr);

// The backend actually in use, for reporting and for the recovery registry.
const char* backendName();

}  // namespace json_backend
}  // namespace lcns
