// lcns/licensing.hpp -- machine binding and dongle access.
//
// Recovered behaviour (re/findings_cloud_lic.md):
//   * GetPCId (0xC010) returns the c_str() of a function-local static std::string built with
//     "%ld". Its worker 0x24290 calls GetAdaptersInfo for the first adapter's MAC
//     (IP_ADAPTER_INFO.Address at +0x198, 6 bytes; retry when the call returns 0x6F) and
//     GetVolumeInformationA("c:\\", ..., &serial, ...), then mixes them:
//         PCId = ((mac48 * serial) + (mac48 >> 16) + mac48 + serial) ^ 0xABADCAFE
//   * UnLockLaunchingOrder (0xD430) writes a mode into LaunchingOrder+0x244.
//     UnLockLaunchingOrderSntl / Oxy / PCId (0xE180 / 0xE1F0 / 0xE260) are byte identical and
//     store two licence key strings at +0x248 and +0x268.
//   * The real gate is the internal function 0x1E70; it validates the keys against a dongle
//     key list and writes a status code into context+0x4C (9 = ok, 11/17 = denied).
//   * Verification is delegated to Sentinel LDK: hasp_windows_x64.dll (hasp_login, hasp_read,
//     hasp_write) and sntl_adminapi_windows_x64.dll. CryptoPP has no call sites in that path.
//
// NOTE ON THE VENDOR CODE: the 984 character base64 blob at RVA 0x9A2080 is the HASP Vendor
// Code. It is deliberately NOT embedded here -- this project ships the mechanism, not the
// product's key material. Pass it in (or read it from the analysed module) when you actually
// need to talk to a dongle; see vendorCodeHint().
#pragma once

#include <cstdint>
#include <string>

namespace lcns {
namespace licensing {

// License types the original distinguishes (the recovered UnLock* entry points).
enum class LicenseKind { None = 0, Sntl = 1, PcId = 2, Oxy = 3 };

const char* toString(LicenseKind k);

// ---------------------------------------------------------------------------
// machine fingerprint
// ---------------------------------------------------------------------------
struct MachineId {
    std::uint64_t mac48 = 0;        // first network adapter, big endian, 6 bytes
    std::uint32_t volumeSerial = 0; // serial of the volume that holds the system drive
    std::uint32_t pcid = 0;         // the mixed value
    bool macOk = false;
    bool volumeOk = false;
};

// RE 0x24290
MachineId computeMachineId();
std::uint32_t computePcid(std::uint64_t mac48, std::uint32_t volumeSerial);
// RE GetPCId 0xC010: cached, formatted with "%ld"
std::string pcidString();

// ---------------------------------------------------------------------------
// Sentinel LDK wrapper (LoadLibrary + GetProcAddress, exactly like 0x12BBA0 / 0x12BCC0)
// ---------------------------------------------------------------------------
class HasLayer {
public:
    explicit HasLayer(std::string dllName = "hasp_windows_x64.dll");
    ~HasLayer();
    HasLayer(const HasLayer&) = delete;
    HasLayer& operator=(const HasLayer&) = delete;

    bool available() const;
    const std::string& dllName() const { return dllName_; }

    // RE: hasp_login(featureId, vendorCode, &handle)
    bool login(int featureId, const char* vendorCode);
    void logout();
    bool loggedIn() const;

    // RE 0x12BBA0: 128 bytes, space padded, written to file id 0xFFF4
    bool writeFile(std::string payload, std::uint32_t fileId = kLicenseFileId);
    // RE 0x12BCC0: hasp_read(h, 0xFFF4, 0x10, buf, 0x80)
    bool readFile(std::string& out, std::uint32_t fileId = kLicenseFileId,
                  std::uint32_t offset = 0x10, std::uint32_t length = 0x80);

    static constexpr std::uint32_t kLicenseFileId = 0xFFF4;
    static constexpr std::size_t kWriteSize = 128;

private:
    std::string dllName_;
    void* module_ = nullptr;
    int handle_ = 0;
    bool loggedIn_ = false;
};

// sntl_adminapi_windows_x64.dll (RE: sntl_admin_context_new / sntl_admin_get / ...)
class SentinelAdmin {
public:
    explicit SentinelAdmin(std::string dllName = "sntl_adminapi_windows_x64.dll");
    ~SentinelAdmin();
    bool available() const;
    // RE: builds a "<haspid>..</haspid>" XML query and reads a value out of the reply
    bool get(const std::string& scope, const std::string& key, std::string& out);

private:
    std::string dllName_;
    void* module_ = nullptr;
    void* context_ = nullptr;
};

// ---------------------------------------------------------------------------
// key validation (RE 0x1E70 + 0x12B580 / 0x12C980 single key, 0x12B5F0 / 0x12CB40 lists)
// ---------------------------------------------------------------------------
struct LicenseStatus {
    bool granted = false;
    int contextCode = 0;      // RE writes 9 when granted, 11 or 17 when denied
    std::string detail;
};

// Checks a key against the running dongle (through HasLayer) and, when no dongle is present,
// against the enumerable key list. Without a dongle and without a key list this always denies,
// which is the behaviour of the shipped gate.
LicenseStatus checkKey(const std::string& key, LicenseKind kind = LicenseKind::Sntl);

// Adds a key to the in-process list used when no dongle is available (used by tests and by
// integrators that hold their own key store).
void addKnownKey(const std::string& key);
void clearKnownKeys();
std::size_t knownKeyCount();

// Explains where the vendor code comes from; the blob itself is intentionally not shipped.
std::string vendorCodeHint();

}  // namespace licensing
}  // namespace lcns
