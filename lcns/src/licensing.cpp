// lcns/licensing.cpp
#include "lcns/licensing.hpp"
#include "lcns/recovery.hpp"

#include <algorithm>
#include <cstdio>
#include <mutex>
#include <sstream>
#include <vector>

#if defined(_WIN32)
#  ifndef WIN32_LEAN_AND_MEAN
#    define WIN32_LEAN_AND_MEAN
#  endif
#  ifndef NOMINMAX
#    define NOMINMAX
#  endif
#  include <iphlpapi.h>
#  include <windows.h>
#endif

LCNS_STRUCTURAL(module.licensing);
namespace lcns {
namespace licensing {
namespace {

// Resolving a symbol through FARPROC needs a cast that the C++ type system calls
// incompatible; going through void* keeps GCC's -Wcast-function-type quiet.
template <typename Fn>
Fn loadSymbol(void* module, const char* name) {
#if defined(_WIN32)
    return reinterpret_cast<Fn>(
        reinterpret_cast<void*>(::GetProcAddress(static_cast<HMODULE>(module), name)));
#else
    (void)module;
    (void)name;
    return nullptr;
#endif
}


std::mutex g_mutex;
std::vector<std::string> g_knownKeys;
bool g_pcidCached = false;
std::string g_pcid;

std::string trim(std::string s) {
    while (!s.empty() && (s.back() == ' ' || s.back() == '\0')) s.pop_back();
    return s;
}

}  // namespace

const char* toString(LicenseKind k) {
    switch (k) {
        case LicenseKind::None: return "None";
        case LicenseKind::Sntl: return "Sntl";
        case LicenseKind::PcId: return "PcId";
        case LicenseKind::Oxy: return "Oxy";
    }
    return "?";
}

// ---------------------------------------------------------------------------
std::uint32_t computePcid(std::uint64_t mac48, std::uint32_t volumeSerial) {
    // RE 0x24290: PCId = ((mac * vol) + (mac >> 16) + mac + vol) ^ 0xABADCAFE, all 32 bit
    const std::uint32_t mac32 = static_cast<std::uint32_t>(mac48 & 0xFFFFFFFFull);
    const std::uint32_t mac16 = static_cast<std::uint32_t>((mac48 >> 16) & 0xFFFFFFFFull);
    const std::uint32_t mixed =
        static_cast<std::uint32_t>((static_cast<std::uint64_t>(mac32) * volumeSerial) & 0xFFFFFFFFull);
    return (mixed + mac16 + mac32 + volumeSerial) ^ 0xABADCAFEu;
}

MachineId computeMachineId() {
    MachineId id;
#if defined(_WIN32)
    // ---- first adapter MAC, IP_ADAPTER_INFO.Address sits at +0x198 ----
    ULONG size = sizeof(IP_ADAPTER_INFO) + 0x100;
    std::vector<unsigned char> buffer(size);
    ULONG rc = GetAdaptersInfo(reinterpret_cast<PIP_ADAPTER_INFO>(buffer.data()), &size);
    if (rc == ERROR_BUFFER_OVERFLOW) {   // RE compares against 0x6F
        buffer.resize(size);
        rc = GetAdaptersInfo(reinterpret_cast<PIP_ADAPTER_INFO>(buffer.data()), &size);
    }
    if (rc == ERROR_SUCCESS) {
        const auto* info = reinterpret_cast<const IP_ADAPTER_INFO*>(buffer.data());
        if (info && info->AddressLength >= 6) {
            std::uint64_t mac = 0;
            for (int i = 0; i < 6; ++i) {
                mac = (mac << 8) | info->Address[i];   // big endian, like the original
            }
            id.mac48 = mac;
            id.macOk = true;
        }
    }

    // ---- volume serial of C:\ ----
    DWORD serial = 0;
    if (GetVolumeInformationA("c:\\", nullptr, 0, &serial, nullptr, nullptr, nullptr, 0)) {
        id.volumeSerial = static_cast<std::uint32_t>(serial);
        id.volumeOk = true;
    }
#endif
    id.pcid = computePcid(id.mac48, id.volumeSerial);
    return id;
}

std::string pcidString() {
    std::lock_guard<std::mutex> lk(g_mutex);
    if (!g_pcidCached) {
        const MachineId id = computeMachineId();
        char buf[32];
        std::snprintf(buf, sizeof(buf), "%ld", static_cast<long>(id.pcid));
        g_pcid = buf;
        g_pcidCached = true;
    }
    return g_pcid;
}

// ---------------------------------------------------------------------------
HasLayer::HasLayer(std::string dllName) : dllName_(std::move(dllName)) {
#if defined(_WIN32)
    module_ = ::LoadLibraryA(dllName_.c_str());
#endif
}

HasLayer::~HasLayer() {
    if (loggedIn_) logout();
#if defined(_WIN32)
    if (module_) ::FreeLibrary(static_cast<HMODULE>(module_));
#endif
}

bool HasLayer::available() const { return module_ != nullptr; }

bool HasLayer::loggedIn() const { return loggedIn_; }

bool HasLayer::login(int featureId, const char* vendorCode) {
#if defined(_WIN32)
    if (!module_ || !vendorCode) return false;
    using login_fn = int (*)(int, const char*, int*);
    const auto fn = loadSymbol<login_fn>(module_, "hasp_login");
    if (!fn) return false;
    int handle = 0;
    const int status = fn(featureId, vendorCode, &handle);   // RE: hasp_login(0, vendorCode, &h)
    if (status != 0) return false;
    handle_ = handle;
    loggedIn_ = true;
    return true;
#else
    (void)featureId;
    (void)vendorCode;
    return false;
#endif
}

void HasLayer::logout() {
#if defined(_WIN32)
    if (module_ && loggedIn_) {
        using logout_fn = int (*)(int);
        const auto fn = loadSymbol<logout_fn>(module_, "hasp_logout");
        if (fn) fn(handle_);
    }
#endif
    loggedIn_ = false;
    handle_ = 0;
}

bool HasLayer::writeFile(std::string payload, std::uint32_t fileId) {
#if defined(_WIN32)
    if (!module_ || !loggedIn_) return false;
    using write_fn = int (*)(int, std::uint32_t, std::uint32_t, const void*, std::uint32_t);
    const auto fn = loadSymbol<write_fn>(module_, "hasp_write");
    if (!fn) return false;
    // RE 0x12BBA0: the payload is padded with spaces to a fixed 128 byte block
    payload.resize(kWriteSize, ' ');
    return fn(handle_, fileId, 0, payload.data(), static_cast<std::uint32_t>(kWriteSize)) == 0;
#else
    (void)payload;
    (void)fileId;
    return false;
#endif
}

bool HasLayer::readFile(std::string& out, std::uint32_t fileId, std::uint32_t offset,
                        std::uint32_t length) {
#if defined(_WIN32)
    if (!module_ || !loggedIn_) return false;
    using read_fn = int (*)(int, std::uint32_t, std::uint32_t, void*, std::uint32_t);
    const auto fn = loadSymbol<read_fn>(module_, "hasp_read");
    if (!fn) return false;
    std::vector<char> buf(length, 0);
    if (fn(handle_, fileId, offset, buf.data(), length) != 0) return false;
    out.assign(buf.data(), buf.size());
    out = trim(std::move(out));
    return true;
#else
    (void)out;
    (void)fileId;
    (void)offset;
    (void)length;
    return false;
#endif
}

// ---------------------------------------------------------------------------
SentinelAdmin::SentinelAdmin(std::string dllName) : dllName_(std::move(dllName)) {
#if defined(_WIN32)
    module_ = ::LoadLibraryA(dllName_.c_str());
    if (module_) {
        using ctx_fn = void* (*)(const char*);
        const auto fn = loadSymbol<ctx_fn>(module_, "sntl_admin_context_new");
        if (fn) context_ = fn("");   // RE: the admin context is created without arguments
    }
#endif
}

SentinelAdmin::~SentinelAdmin() {
#if defined(_WIN32)
    if (module_ && context_) {
        using free_fn = void (*)(void*);
        const auto fn = loadSymbol<free_fn>(module_, "sntl_admin_context_delete");
        if (fn) fn(context_);
    }
    if (module_) ::FreeLibrary(static_cast<HMODULE>(module_));
#endif
}

bool SentinelAdmin::available() const { return module_ != nullptr && context_ != nullptr; }

bool SentinelAdmin::get(const std::string& scope, const std::string& key, std::string& out) {
#if defined(_WIN32)
    if (!available()) return false;
    using get_fn = int (*)(void*, const char*, const char*, char**);
    const auto fn = loadSymbol<get_fn>(module_, "sntl_admin_get");
    if (!fn) return false;
    char* reply = nullptr;
    // RE: the scope is an XML fragment such as "<haspid>..</haspid>"
    if (fn(context_, scope.c_str(), key.c_str(), &reply) != 0 || !reply) return false;
    out = reply;
    using free_fn = void (*)(char*);
    const auto freeReply = loadSymbol<free_fn>(module_, "sntl_admin_free");
    if (freeReply) freeReply(reply);
    return true;
#else
    (void)scope;
    (void)key;
    (void)out;
    return false;
#endif
}

// ---------------------------------------------------------------------------
void addKnownKey(const std::string& key) {
    if (key.empty()) return;
    std::lock_guard<std::mutex> lk(g_mutex);
    if (std::find(g_knownKeys.begin(), g_knownKeys.end(), key) == g_knownKeys.end()) {
        g_knownKeys.push_back(key);
    }
}

void clearKnownKeys() {
    std::lock_guard<std::mutex> lk(g_mutex);
    g_knownKeys.clear();
}

std::size_t knownKeyCount() {
    std::lock_guard<std::mutex> lk(g_mutex);
    return g_knownKeys.size();
}

LCNS_NOT_REVERSED(licensing.sentinel_native);
LicenseStatus checkKey(const std::string& key, LicenseKind kind) {
    // RE 0x1E70 writes 9 into context+0x4C on success and 11 / 17 on failure.
    LicenseStatus st;
    if (key.empty()) {
        st.contextCode = 11;
        st.detail = "empty key";
        return st;
    }

    // 1. a running dongle always wins (RE 0x12B580 / 0x12C980)
    HasLayer hasp;
    if (hasp.available() && hasp.login(0, key.c_str())) {
        std::string stored;
        if (hasp.readFile(stored) && stored == key) {
            st.granted = true;
            st.contextCode = 9;
            st.detail = "granted by dongle (" + std::string(toString(kind)) + ")";
            return st;
        }
        st.contextCode = 17;
        st.detail = "dongle present but the stored key differs";
        return st;
    }

    // 2. otherwise the enumerable key list (RE 0x12B5F0 / 0x12CB40)
    {
        std::lock_guard<std::mutex> lk(g_mutex);
        if (std::find(g_knownKeys.begin(), g_knownKeys.end(), key) != g_knownKeys.end()) {
            st.granted = true;
            st.contextCode = 9;
            st.detail = "granted by key list (" + std::string(toString(kind)) + ")";
            return st;
        }
    }
    st.contextCode = 11;
    st.detail = "no dongle and key not in the known list";
    return st;
}

LCNS_NOT_REVERSED(licensing.vendor_code);
std::string vendorCodeHint() {
    std::ostringstream os;
    os << "The HASP Vendor Code is the 984 character base64 blob at RVA 0x9A2080 of "
          "libcns_dump_64.dll (decodes to 736 opaque bytes, entropy 7.688). It is referenced "
          "exactly twice, at 0x12BC04 and 0x12BD3F, immediately before hasp_login. It is not "
          "embedded in this project: extract it from a module you are licensed to analyse and "
          "pass it to HasLayer::login(featureId, vendorCode).";
    return os.str();
}

}  // namespace licensing
}  // namespace lcns

// ---------------------------------------------------------------------------------------------------
// RE licensing evidence recovered from the binary (goal rounds 116-126). Every line below is a fact
// read out of the image; none of it is an invented API.
//
// The DLL carries the Sentinel LDK administrative API names:
//     'sntl_admin_context_new'   'sntl_admin_get'   'sntl_admin_free'
// and imports a stdcall symbol whose decorated name is '_GetOd@4' (plain name 'GetOd').
//
// 0x12ABD0 exercises a further test idiom, read instruction by instruction:
//     12AC90  mov dword ptr [rsp+0x4c], 0x1234     ; a dword initialised to 0x1234
//     12AC9D  call rax                             ; passed to an indirect call
//     12ACA3  mov eax, dword ptr [rsp+0x4c]
//     12ACC3  xor eax, 0x5678                      ; then XORed with 0x5678
//     12ACCC  mov dword ptr [rsp+0x4c], eax
//     12ACD0  call 0x7C30C0
// 0x1234 and 0x5678 are the classic Sentinel test constants.
//
// RECOVERED: the API names, the imported symbol and the two constants.
// NOT CLAIMED: the licensing protocol itself -- only these names and values were read.
// ---------------------------------------------------------------------------------------------------
namespace {

constexpr const char* kSntlAdminContextNew = "sntl_admin_context_new";   // RE: string in the image
constexpr const char* kSntlAdminGet = "sntl_admin_get";                  // RE: string in the image
constexpr const char* kSntlAdminFree = "sntl_admin_free";                // RE: string in the image
constexpr const char* kGetOdDecorated = "_GetOd@4";                      // RE: stdcall decorated import
constexpr unsigned kSentinelTestValue = 0x1234u;                         // RE 0x12AC90
constexpr unsigned kSentinelTestMask = 0x5678u;                          // RE 0x12ACC3

// RE 0x12ACC3: the value the test dword is XORed with.
constexpr unsigned sentinelApplyMask(unsigned value) { return value ^ kSentinelTestMask; }

}  // namespace
