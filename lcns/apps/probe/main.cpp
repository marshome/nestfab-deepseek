// apps/probe/main.cpp -- inspect a candidate liblcns.dll and bind the recovered API by ordinal.
//
// Usage:
//   lcns_probe [path-to-dll] [--all]
//
// Default path is the sample this project was reverse engineered from.
#include "lcns/api.hpp"

#include <cstdio>
#include <cstring>
#include <string>

namespace {

void printDiagnosis(const lcns::dll::Diagnostic& d) {
    std::printf("--- static diagnosis ---\n");
    std::printf("MZ/PE                 : %s\n", d.isPe ? "yes" : "no");
    std::printf("PE32+ (AMD64)         : %s\n", d.isPe64 ? "yes" : "no");
    std::printf("export directory      : %s (rva 0x%X)\n", d.hasExportDirectory ? "present" : "absent",
                d.exportDirectoryRva);
    std::printf("NumberOfFunctions     : %u\n", d.numberOfFunctions);
    std::printf("NumberOfNames         : %u%s\n", d.numberOfNames,
                d.hasNames ? "" : "   <- name table stripped, exports are ordinal-only");
    std::printf("stale absolute addrs  : %s\n", d.iatLooksLikeStaleAddresses ? "yes (memory dump)" : "no");
    if (!d.problems.empty()) {
        std::printf("problems:\n");
        for (const auto& p : d.problems) std::printf("  - %s\n", p.c_str());
    }
    if (!d.notes.empty()) {
        std::printf("notes:\n");
        for (const auto& p : d.notes) std::printf("  - %s\n", p.c_str());
    }
}

}  // namespace

int main(int argc, char** argv) {
    std::string path = "D:\\Nesting\\nestfab\\libcns_dump_64.dll";
    bool all = false;
    bool doLoad = false;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--all") == 0) {
            all = true;
        } else if (std::strcmp(argv[i], "--load") == 0) {
            doLoad = true;
        } else {
            path = argv[i];
        }
    }

    std::printf("probing %s\n\n", path.c_str());
    printDiagnosis(lcns::dll::diagnoseFile(path));

    std::printf("\n--- recovered export surface (%zu unique functions) ---\n", lcns::dll::exportCount());
    std::size_t rec = 0, inf = 0, unk = 0;
    for (std::size_t i = 0; i < lcns::dll::exportCount(); ++i) {
        switch (lcns::dll::exportTable()[i].confidence) {
            case lcns::dll::Confidence::Recovered: ++rec; break;
            case lcns::dll::Confidence::Inferred: ++inf; break;
            default: ++unk; break;
        }
    }
    std::printf("names recovered from tracer labels : %zu\n", rec);
    std::printf("names inferred from behaviour      : %zu\n", inf);
    std::printf("unnamed (reachable by ordinal only): %zu\n", unk);
    if (all) {
        std::printf("%s", lcns::dll::formatExportTable(false).c_str());
    } else {
        std::printf("%s", lcns::dll::formatExportTable(true).c_str());
    }

    std::printf("\n--- dynamic load attempt ---\n");
    std::fflush(stdout);
    if (!doLoad) {
        std::printf("skipped. Pass --load to try LoadLibraryA anyway.\n");
        std::printf("WARNING: on the published dump this maps a corrupt image and can raise an\n"
                    "         access violation inside the loader (the IAT holds stale absolute\n"
                    "         addresses). Use a real liblcns.dll instead.\n");
        return 0;
    }

    lcns::dll::Library lib;
    std::string err;
    if (!lib.load(path, &err)) {
        std::printf("load FAILED\n%s", err.c_str());
        std::printf("\nThe published sample is a memory dump and is not loadable by design.\n"
                    "Use a real liblcns.dll with the same ABI, or nest_demo for the\n"
                    "standalone reconstruction.\n");
        return 2;
    }
    std::printf("load OK: %zu non-zero ordinals\n", lib.ordinalCount());

    lcns::dll::Api api;
    const std::size_t bound = api.bind(lib);
    std::printf("typed entries bound: %zu\n", bound);
    if (api.GetMajorVersion) std::printf("GetMajorVersion() = %d\n", api.GetMajorVersion());
    if (api.GetBuildVersion) std::printf("GetBuildVersion() = %s\n", api.GetBuildVersion());
    if (api.GetBuildDate) std::printf("GetBuildDate()    = %s\n", api.GetBuildDate());
    if (api.GetPCId) std::printf("GetPCId()         = %s\n", api.GetPCId());
    return 0;
}
