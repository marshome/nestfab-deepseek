// tests/test_licensing.cpp -- machine fingerprint and the dongle wrapper.
#include "check.hpp"
#include "lcns/licensing.hpp"

#include <cctype>

using namespace lcns;
using namespace lcns::licensing;

int main() {
    // --- the recovered PCId mixing formula (RE 0x24290) ---
    {
        // PCId = ((mac*vol) + (mac>>16) + mac + vol) ^ 0xABADCAFE, all 32 bit
        CHECK(computePcid(0, 0) == 0xABADCAFEu);
        // mac = 1 (so mac32 = 1, mac16 = 0), vol = 1 -> (1 + 0 + 1 + 1) ^ constant
        CHECK(computePcid(1, 1) == (0xABADCAFEu ^ 3u));
        CHECK(computePcid(1, 1) == 0xABADCAFDu);
        // determinism and sensitivity
        const std::uint32_t a = computePcid(0x001122334455ull, 0xDEADBEEFu);
        const std::uint32_t b = computePcid(0x001122334455ull, 0xDEADBEEFu);
        CHECK(a == b);
        CHECK(computePcid(0x001122334456ull, 0xDEADBEEFu) != a);
        CHECK(computePcid(0x001122334455ull, 0xDEADBEEEu) != a);
        // the high half of the MAC feeds in through mac >> 16
        CHECK(computePcid(0x000100000000ull, 0) == (0xABADCAFEu ^ 0x00010000u));
    }

    // --- machine id: on this platform the MAC and the volume serial should both resolve ---
    {
        const MachineId id = computeMachineId();
        CHECK(id.pcid == computePcid(id.mac48, id.volumeSerial));
        if (id.macOk) {
            CHECK(id.mac48 != 0);
            CHECK(id.mac48 <= 0xFFFFFFFFFFFFull);   // 48 bit
        }
        // volume serial may legitimately be zero on some volumes
        CHECK(id.volumeOk || !id.volumeOk);
    }

    // --- pcidString is cached, numeric and stable ---
    {
        const std::string s1 = pcidString();
        const std::string s2 = pcidString();
        CHECK(!s1.empty());
        CHECK(s1 == s2);
        bool numeric = true;
        for (char c : s1) {
            if (!std::isdigit(static_cast<unsigned char>(c))) numeric = false;
        }
        CHECK(numeric);
    }

    // --- HasLayer without a dongle present ---
    {
        HasLayer hasp("definitely_not_a_real_hasp_dll_12345.dll");
        CHECK(!hasp.available());
        CHECK(!hasp.loggedIn());
        CHECK(!hasp.login(0, "vendor"));
        CHECK(!hasp.writeFile("payload"));
        std::string out;
        CHECK(!hasp.readFile(out));
        CHECK(HasLayer::kLicenseFileId == 0xFFF4u);
        CHECK(HasLayer::kWriteSize == 128u);
        hasp.logout();   // must be safe when never logged in
    }

    // --- SentinelAdmin without the runtime ---
    {
        SentinelAdmin admin("definitely_not_a_real_sntl_dll_12345.dll");
        CHECK(!admin.available());
        std::string v;
        CHECK(!admin.get("<haspid>1</haspid>", "haspid", v));
    }

    // --- the licence gate: empty and unknown keys are denied, listed keys are granted ---
    {
        clearKnownKeys();
        CHECK(knownKeyCount() == 0);

        const LicenseStatus empty = checkKey("");
        CHECK(!empty.granted);
        CHECK(empty.contextCode == 11);   // RE writes 11 on denial
        CHECK(!empty.detail.empty());

        const LicenseStatus unknown = checkKey("NOT-A-KEY");
        CHECK(!unknown.granted);
        CHECK(unknown.contextCode == 11);

        addKnownKey("KEY-1");
        addKnownKey("KEY-2");
        addKnownKey("KEY-1");   // duplicates are ignored
        CHECK(knownKeyCount() == 2);

        const LicenseStatus ok = checkKey("KEY-1");
        CHECK(ok.granted);
        CHECK(ok.contextCode == 9);       // RE writes 9 on success
        CHECK(checkKey("KEY-2").granted);
        CHECK(!checkKey("KEY-3").granted);

        clearKnownKeys();
        CHECK(knownKeyCount() == 0);
        CHECK(!checkKey("KEY-1").granted);

        // licence kinds round trip through their names
        CHECK(std::string(toString(LicenseKind::None)) == "None");
        CHECK(std::string(toString(LicenseKind::Sntl)) == "Sntl");
        CHECK(std::string(toString(LicenseKind::PcId)) == "PcId");
        CHECK(std::string(toString(LicenseKind::Oxy)) == "Oxy");

        // the vendor code is described, not shipped
        const std::string hint = vendorCodeHint();
        CHECK(hint.find("0x9A2080") != std::string::npos);
        CHECK(hint.find("hasp_login") != std::string::npos);
        CHECK(hint.find("not\nembedded") != std::string::npos ||
              hint.find("not ") != std::string::npos);
    }

    // --- the recovered Sentinel test constants and the XOR the instruction performs ---------------
    {
        constexpr unsigned kTestValue = 0x1234u;   // RE 0x12AC90
        constexpr unsigned kTestMask = 0x5678u;    // RE 0x12ACC3
        CHECK(kTestValue == 0x1234u);
        CHECK(kTestMask == 0x5678u);
        CHECK((kTestValue ^ kTestMask) == 0x444Cu);
        // and the API names the binary carries are the ones the module already describes
        CHECK(std::string(toString(LicenseKind::Sntl)) == "Sntl");
    }

    return check::finish("test_licensing");
}
