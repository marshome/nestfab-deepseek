// tests/test_crypto_backend.cpp -- the CryptoPP link capability (goal round 211, T7).
//
// The point of this test is not cryptography: it is that a REAL CryptoPP symbol is callable from this project,
// which is what the goal's download-and-link rule asks for. The expected digest is the published SHA-1 of the
// empty string and of "abc", i.e. values from the algorithm's own definition rather than from memory of this
// repository.
#include "check.hpp"
#include "lcns/crypto_backend.hpp"

#include <string>

int main() {
#ifdef LCNS_HAS_CRYPTOPP
    CHECK(lcns::crypto_backend::available());
    CHECK(std::string(lcns::crypto_backend::backendName()) == "CryptoPP 8.9.0");

    bool unavailable = true;
    const std::string empty = lcns::crypto_backend::sha1Hex("", &unavailable);
    CHECK(!unavailable);
    CHECK(empty == "da39a3ee5e6b4b0d3255bfef95601890afd80709");

    const std::string abc = lcns::crypto_backend::sha1Hex("abc", &unavailable);
    CHECK(!unavailable);
    CHECK(abc == "a9993e364706816aba3e25717850c26c9cd0d89d");

    // longer than one block, so the padding path is exercised too
    const std::string longInput(1000, 'a');
    const std::string longDigest = lcns::crypto_backend::sha1Hex(longInput, &unavailable);
    CHECK(longDigest.size() == 40);
    CHECK(longDigest != abc);
#else
    CHECK(!lcns::crypto_backend::available());
    bool unavailable = false;
    const std::string none = lcns::crypto_backend::sha1Hex("abc", &unavailable);
    CHECK(unavailable);
    CHECK(none.empty());
#endif

    return check::finish("test_crypto_backend");
}
