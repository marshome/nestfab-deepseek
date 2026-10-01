// lcns/crypto_bridge.cpp -- the CryptoPP link capability (goal round 211, T7).
//
// Compiles to a reporting stub when the library is absent, so the build never depends on it and the absence is
// stated instead of hidden.
#include "lcns/crypto_backend.hpp"

#ifdef LCNS_HAS_CRYPTOPP
#include <hex.h>
#include <sha.h>
#endif

namespace lcns {
namespace crypto_backend {

bool available() {
#ifdef LCNS_HAS_CRYPTOPP
    return true;
#else
    return false;
#endif
}

const char* backendName() {
#ifdef LCNS_HAS_CRYPTOPP
    return "CryptoPP 8.9.0";
#else
    return "none";
#endif
}

std::string sha1Hex(const std::string& data, bool* unavailable) {
#ifdef LCNS_HAS_CRYPTOPP
    if (unavailable != nullptr) {
        *unavailable = false;
    }
    CryptoPP::SHA1 hash;
    std::string digest;
    CryptoPP::StringSource source(
        data, true,
        new CryptoPP::HashFilter(hash, new CryptoPP::HexEncoder(new CryptoPP::StringSink(digest), false)));
    (void)source;
    return digest;
#else
    if (unavailable != nullptr) {
        *unavailable = true;
    }
    (void)data;
    return std::string();
#endif
}

}  // namespace crypto_backend
}  // namespace lcns
