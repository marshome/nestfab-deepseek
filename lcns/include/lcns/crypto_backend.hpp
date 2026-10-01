// include/lcns/crypto_backend.hpp -- the CryptoPP link capability (goal round 211, T7).
//
// The goal excludes third-party code from reverse engineering and asks instead that the libraries be downloaded
// and referenced directly from the build. third_party/README.md scopes the CryptoPP item to "build the link
// capability only", because the licensing and cloud paths that need it are themselves NotReversed. This header is
// that capability: a thin surface that reports whether the real library is linked and, when it is, computes a
// digest with it.
#pragma once

#include <string>

namespace lcns {
namespace crypto_backend {

// True when the vendored CryptoPP was built and linked in (LCNS_HAS_CRYPTOPP).
bool available();

// The backend actually in use, for reporting.
const char* backendName();

// Lower case hex SHA-1. Uses the real CryptoPP when linked; otherwise returns an empty string and sets
// `unavailable` to true, so the absence is visible rather than silently replaced by a hand written digest.
std::string sha1Hex(const std::string& data, bool* unavailable = nullptr);

}  // namespace crypto_backend
}  // namespace lcns
