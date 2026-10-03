// lcns/api.hpp -- access layer for the recovered liblcns.dll export surface.
//
// Reverse-engineering facts this header encodes (see ../re/REPORT.md):
//   * The real DLL exports as `liblcns.dll`, NumberOfNames == 0 (all names stripped),
//     NumberOfFunctions == 343 with 336 non-zero entries -> 168 unique functions,
//     each listed TWICE under two adjacent ordinals.
//   * Therefore runtime binding MUST be ordinal based. byName() maps a recovered name
//     back to its ordinal and then resolves it.
//   * The sample this project was derived from (libcns_dump_64.dll) is a memory dump whose
//     IAT holds stale absolute addresses and whose OriginalFirstThunk is zero, so Windows
//     cannot load it. diagnoseFile() reports exactly that.
//
// TWO LAYERS:
//   raw   -- byOrdinal()/byName(); authoritative, makes no signature claims.
//   typed -- `Api`; signatures are INFERRED from call-site argument analysis, not from
//            symbols. Treat every typed entry as a convenience cast, not as ground truth.
//
// Everything here lives in `lcns::dll` so that the model types (lcns::Part, lcns::Sheet,
// ...) in model.hpp do not collide with the DLL's opaque handles.
#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

#include "lcns/enums.hpp"

namespace lcns {
namespace dll {

using lcns::Confidence;
using lcns::NestingOrigin;
using lcns::Objective;

// ---------------------------------------------------------------------------
// Opaque handles. The real objects are internal C++ classes; only their field
// offsets were recovered (documented in re/REPORT.md section 3.2).
// ---------------------------------------------------------------------------
#define LCNS_OPAQUE(name)      \
    struct name##_t;           \
    using name = name##_t*
// **`Order` IS THE REAL CLASS IN lcns/model.hpp, SO THE HANDLE IS NAMED `OrderHandle`.** A handle that shares its name with the class it points at is
// two declarations of one name: `using Order = Order_t*` beside `struct Order`, which makes a signature saying `Order*` mean `Order_t**`.
struct Order_t;
using OrderHandle = Order_t*;   // LaunchingOrder   (NewLaunchingOrder)
LCNS_OPAQUE(Part);         // a part to nest
LCNS_OPAQUE(Sheet);        // a sheet/plate
LCNS_OPAQUE(Nesting);      // one nesting inside a solution
LCNS_OPAQUE(NestedPart);   // a placed part
// **`Solution` IS THE REAL CLASS IN lcns/model.hpp, SO THE HANDLE IS NAMED `SolutionHandle`** -- the same rename `Order` needed, and for the same
// reason: `using Solution = Solution_t*` beside `struct Solution` is two declarations of one name.
struct Solution_t;
using SolutionHandle = Solution_t*;   // SolveResult
LCNS_OPAQUE(NoFitContext); // NoFitContext (0xF0 bytes in the original)
LCNS_OPAQUE(NoFitNesting);
LCNS_OPAQUE(NoFitGeometry);
#undef LCNS_OPAQUE

// ---------------------------------------------------------------------------
// Export directory metadata (generated from re/exports_table.json).
// ---------------------------------------------------------------------------
struct ExportInfo {
    const char* name;         // recovered name (or "sub_XXXXX" if unknown)
    int ordinal0;             // first of the two adjacent ordinals
    int ordinal1;             // second (-1 if the pair was split by a hollowed slot)
    std::uint32_t rva;        // RVA in the dumped image
    std::uint32_t size;       // function size from .pdata, bytes
    const char* label;        // the tracer label literal, verbatim (may start with "// ")
    const char* cAlias;       // public C alias used in assert text (e.g. "CNS_GetSheet")
    Confidence confidence;
};

const ExportInfo* exportTable();
std::size_t exportCount();
const ExportInfo* findExport(std::string_view name);

// Human readable dump of the whole recovered surface (for reports/CLI).
std::string formatExportTable(bool onlyNamed = false);

// ---------------------------------------------------------------------------
// Static diagnosis of a candidate DLL file: is it loadable at all?
// ---------------------------------------------------------------------------
struct Diagnostic {
    bool isPe = false;
    bool isPe64 = false;
    bool hasExportDirectory = false;
    bool hasNames = false;
    bool originalFirstThunkZero = true;  // true => import table was destroyed
    bool iatLooksLikeStaleAddresses = false;
    std::uint32_t exportDirectoryRva = 0;
    std::uint32_t numberOfFunctions = 0;
    std::uint32_t numberOfNames = 0;
    std::vector<std::string> problems;   // why it will not load
    std::vector<std::string> notes;
};

Diagnostic diagnoseFile(const std::string& path);

// ---------------------------------------------------------------------------
// Ordinal based loader.
// ---------------------------------------------------------------------------
class Library {
public:
    Library();
    ~Library();
    Library(const Library&) = delete;
    Library& operator=(const Library&) = delete;
    Library(Library&&) noexcept;
    Library& operator=(Library&&) noexcept;

    // Loads `path` and keeps it for the lifetime of the object. On failure returns
    // false and, if `error` is given, fills it with the reason plus (when the file
    // looks like a dump) the diagnosis from diagnoseFile().
    bool load(const std::string& path, std::string* error = nullptr);
    void close();
    bool loaded() const;
    const std::string& path() const;

    // Raw resolution. Prefer byName(); byOrdinal() is what actually works on the
    // original DLL because its export names are gone.
    void* byOrdinal(int ordinal) const;
    void* byName(std::string_view name) const;

    // Number of ordinals successfully quarried from the loaded module.
    std::size_t ordinalCount() const;

private:
    struct Impl;
    Impl* impl_;
};

// ---------------------------------------------------------------------------
// Typed layer. INFERRED signatures -- see the warning at the top of this file.
// ---------------------------------------------------------------------------
struct Api {
#define LCNS_TYPED(ret, name, params) using fn_##name = ret (*) params; fn_##name name = nullptr;
#include "lcns/detail/api_typed.inc"
#undef LCNS_TYPED

    // Resolves every typed entry; missing ones are left null. Returns how many bound.
    std::size_t bind(const Library& lib);
};

}  // namespace dll
}  // namespace lcns
