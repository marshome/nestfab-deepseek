// Forced include for building the 2016-era COIN-OR sources with GCC 13.
//
// Old code relied on standard headers pulling in <cfloat>/<climits>/<cstring> transitively; modern
// libstdc++ no longer does, so e.g. CoinFinite.cpp fails on DBL_MAX. Rather than edit third party
// sources (which must stay pristine so their provenance is verifiable), force this header in.
#pragma once
#include <cfloat>
#include <climits>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <cassert>
#include <algorithm>
#include <string>
#include <vector>
#include <limits>
