// lcns/api.cpp -- export table, PE diagnosis and ordinal based loader.
#include "lcns/api.hpp"
#include "lcns/recovery.hpp"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <sstream>

#if defined(_WIN32)
#  ifndef WIN32_LEAN_AND_MEAN
#    define WIN32_LEAN_AND_MEAN
#  endif
#  ifndef NOMINMAX
#    define NOMINMAX
#  endif
#  include <windows.h>
#endif

LCNS_RECOVERED(module.api);
namespace lcns {
namespace dll {
namespace {

// --------------------------------------------------------------------------
// generated table
// --------------------------------------------------------------------------
const ExportInfo kExports[] = {
#define LCNS_EXPORT_ROW(name, o0, o1, rva, size, label, alias, conf) \
    {#name, o0, o1, rva, size, label, alias, static_cast<Confidence>(conf)},
#include "lcns/detail/api_table.inc"
#undef LCNS_EXPORT_ROW
};

// --------------------------------------------------------------------------
// minimal PE reader (enough to explain why the dumped sample will not load)
// --------------------------------------------------------------------------
template <typename T>
bool readAt(std::istream& in, std::uint64_t off, T& out) {
    in.seekg(static_cast<std::streamoff>(off), std::ios::beg);
    in.read(reinterpret_cast<char*>(&out), sizeof(T));
    return in.good();
}

bool looksLikeStaleAddress(std::uint64_t v) {
    // dumps carry addresses of the process that was dumping, e.g. 0x00007FF9xxxxxxxx
    return v >= 0x0000700000000000ull && v <= 0x0000800000000000ull;
}

}  // namespace

const ExportInfo* exportTable() { return kExports; }

std::size_t exportCount() { return sizeof(kExports) / sizeof(kExports[0]); }

const ExportInfo* findExport(std::string_view name) {
    for (const auto& e : kExports) {
        if (name == e.name) return &e;
    }
    return nullptr;
}

LCNS_RECOVERED(api.ordinal_loader);
std::string formatExportTable(bool onlyNamed) {
    std::ostringstream os;
    os << "ordinals      RVA      size  conf  name\n";
    for (const auto& e : kExports) {
        if (onlyNamed && e.confidence == Confidence::Unknown) continue;
        char buf[160];
        char ords[24];
        if (e.ordinal1 > 0) {
            std::snprintf(ords, sizeof(ords), "%d,%d", e.ordinal0, e.ordinal1);
        } else {
            std::snprintf(ords, sizeof(ords), "%d", e.ordinal0);
        }
        std::snprintf(buf, sizeof(buf), "%-13s 0x%05X %6u  %s  %s\n", ords, e.rva, e.size,
                      e.confidence == Confidence::Recovered  ? "R"
                      : e.confidence == Confidence::Inferred ? "i"
                                                             : "?",
                      e.name);
        os << buf;
    }
    return os.str();
}

Diagnostic diagnoseFile(const std::string& path) {
    Diagnostic d;
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        d.problems.push_back("cannot open file");
        return d;
    }

    std::uint16_t mz = 0;
    if (!readAt(in, 0, mz) || mz != 0x5A4D) {
        d.problems.push_back("not an MZ/PE file");
        return d;
    }
    d.isPe = true;

    std::uint32_t e_lfanew = 0;
    readAt(in, 0x3C, e_lfanew);
    std::uint32_t sig = 0;
    if (!readAt(in, e_lfanew, sig) || sig != 0x00004550) {
        d.problems.push_back("missing PE signature");
        return d;
    }

    std::uint16_t machine = 0, nsect = 0, optSize = 0;
    readAt(in, e_lfanew + 4, machine);
    readAt(in, e_lfanew + 6, nsect);
    readAt(in, e_lfanew + 20, optSize);
    d.isPe64 = (machine == 0x8664);
    if (!d.isPe64) d.notes.push_back("machine is not AMD64");

    const std::uint64_t opt = static_cast<std::uint64_t>(e_lfanew) + 24;
    std::uint16_t magic = 0;
    readAt(in, opt, magic);
    const std::uint64_t dd = opt + (magic == 0x20B ? 112 : 96);

    std::uint32_t expRva = 0, expSize = 0;
    readAt(in, dd + 0, expRva);
    readAt(in, dd + 4, expSize);
    d.exportDirectoryRva = expRva;
    d.hasExportDirectory = (expRva != 0 && expSize != 0);

    if (d.hasExportDirectory) {
        // translate the export dir RVA to a file offset using the section table
        const std::uint64_t secTab = opt + optSize;
        std::uint64_t expOff = 0;
        for (std::uint16_t i = 0; i < nsect; ++i) {
            const std::uint64_t s = secTab + i * 40ull;
            std::uint32_t vsize = 0, vaddr = 0, rawsize = 0, rawptr = 0;
            readAt(in, s + 8, vsize);
            readAt(in, s + 12, vaddr);
            readAt(in, s + 16, rawsize);
            readAt(in, s + 20, rawptr);
            const std::uint32_t span = vsize > rawsize ? vsize : rawsize;
            if (expRva >= vaddr && expRva < vaddr + span) {
                expOff = static_cast<std::uint64_t>(rawptr) + (expRva - vaddr);
                break;
            }
        }
        if (expOff) {
            std::uint32_t nfunc = 0, nnames = 0, aof = 0;
            readAt(in, expOff + 20, nfunc);
            readAt(in, expOff + 24, nnames);
            readAt(in, expOff + 28, aof);
            d.numberOfFunctions = nfunc;
            d.numberOfNames = nnames;
            d.hasNames = nnames > 0;
        }
    }

    // import descriptor walk
    std::uint32_t impRva = 0, impSize = 0;
    readAt(in, dd + 8, impRva);
    readAt(in, dd + 12, impSize);
    if (impRva == 0 || impSize == 0) {
        d.notes.push_back("no import directory");
    }

    if (!d.hasNames && d.numberOfFunctions > 0) {
        d.problems.push_back(
            "export name table is EMPTY (NumberOfNames == 0): every export is ordinal-only");
    }
    d.notes.push_back("exports are ordinal-only; bind through lcns::Library::byOrdinal()/byName()");

    // Heuristic on the file: does it contain a pointer table full of 0x00007FF9.. values?
    in.clear();
    in.seekg(0, std::ios::end);
    const std::uint64_t size = static_cast<std::uint64_t>(in.tellg());
    in.seekg(0, std::ios::beg);
    std::vector<char> blob(static_cast<std::size_t>(std::min<std::uint64_t>(size, 1u << 24)));
    in.read(blob.data(), static_cast<std::streamsize>(blob.size()));
    std::size_t hits = 0;
    for (std::size_t i = 0; i + 8 <= blob.size(); i += 8) {
        std::uint64_t v = 0;
        std::memcpy(&v, blob.data() + i, 8);
        if (looksLikeStaleAddress(v) && ++hits > 8) break;
    }
    d.iatLooksLikeStaleAddresses = hits > 8;
    if (d.iatLooksLikeStaleAddresses) {
        d.problems.push_back(
            "contains absolute addresses of the process that produced the dump "
            "(stale IAT) -- this is a memory dump, not a loadable image");
    }
    if (d.originalFirstThunkZero) {
        d.notes.push_back(
            "IMAGE_IMPORT_DESCRIPTOR.OriginalFirstThunk is zero in the dumped sample, "
            "so the loader would interpret FirstThunk as the name table");
    }
    return d;
}

// --------------------------------------------------------------------------
// Library
// --------------------------------------------------------------------------
struct Library::Impl {
    std::string path;
#if defined(_WIN32)
    HMODULE handle = nullptr;
#endif
    std::size_t ordinals = 0;
};

Library::Library() : impl_(new Impl) {}
Library::~Library() {
    close();
    delete impl_;
}
Library::Library(Library&& o) noexcept : impl_(o.impl_) { o.impl_ = new Impl; }
Library& Library::operator=(Library&& o) noexcept {
    if (this != &o) {
        close();
        delete impl_;
        impl_ = o.impl_;
        o.impl_ = new Impl;
    }
    return *this;
}

void Library::close() {
#if defined(_WIN32)
    if (impl_->handle) {
        FreeLibrary(impl_->handle);
        impl_->handle = nullptr;
    }
#endif
    impl_->ordinals = 0;
    impl_->path.clear();
}

bool Library::load(const std::string& path, std::string* error) {
    close();
#if defined(_WIN32)
    HMODULE h = ::LoadLibraryA(path.c_str());
    if (!h) {
        const DWORD err = ::GetLastError();
        if (error) {
            std::ostringstream os;
            os << "LoadLibraryA failed, GetLastError()=" << err << "\n";
            const Diagnostic d = diagnoseFile(path);
            if (!d.problems.empty()) {
                os << "diagnosis of " << path << ":\n";
                for (const auto& p : d.problems) os << "  - " << p << "\n";
            }
            os << "  hint: the published libcns_dump_64.dll cannot be loaded; use a real\n"
                  "        liblcns.dll (same ABI) or the standalone reimplementation\n"
                  "        in lcns/nest (target nest_demo).\n";
            *error = os.str();
        }
        return false;
    }
    impl_->handle = h;
    impl_->path = path;

    // count non-zero ordinals straight from the loaded module's export directory
    const auto* base = reinterpret_cast<const unsigned char*>(h);
    const auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(base);
    const auto* nt = reinterpret_cast<const IMAGE_NT_HEADERS*>(base + dos->e_lfanew);
    const IMAGE_DATA_DIRECTORY& dir = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];
    if (dir.VirtualAddress && dir.Size) {
        const auto* exp = reinterpret_cast<const IMAGE_EXPORT_DIRECTORY*>(base + dir.VirtualAddress);
        const auto* funcs = reinterpret_cast<const DWORD*>(base + exp->AddressOfFunctions);
        for (DWORD i = 0; i < exp->NumberOfFunctions; ++i) {
            if (funcs[i] != 0) ++impl_->ordinals;
        }
    }
    return true;
#else
    (void)path;
    if (error) *error = "dynamic loading is only implemented for Windows targets";
    return false;
#endif
}

bool Library::loaded() const {
#if defined(_WIN32)
    return impl_->handle != nullptr;
#else
    return false;
#endif
}

const std::string& Library::path() const { return impl_->path; }

std::size_t Library::ordinalCount() const { return impl_->ordinals; }

void* Library::byOrdinal(int ordinal) const {
#if defined(_WIN32)
    if (!impl_->handle || ordinal <= 0) return nullptr;
    return reinterpret_cast<void*>(
        ::GetProcAddress(impl_->handle, reinterpret_cast<LPCSTR>(static_cast<ULONG_PTR>(ordinal))));
#else
    (void)ordinal;
    return nullptr;
#endif
}

void* Library::byName(std::string_view name) const {
    const ExportInfo* e = findExport(name);
    if (!e) return nullptr;
    if (void* p = byOrdinal(e->ordinal0)) return p;
    return e->ordinal1 > 0 ? byOrdinal(e->ordinal1) : nullptr;
}

std::size_t Api::bind(const Library& lib) {
    std::size_t n = 0;
#define LCNS_TYPED(ret, name, params)                       \
    name = reinterpret_cast<fn_##name>(lib.byName(#name));  \
    if (name) ++n;
#include "lcns/detail/api_typed.inc"
#undef LCNS_TYPED
    return n;
}

}  // namespace dll
}  // namespace lcns
