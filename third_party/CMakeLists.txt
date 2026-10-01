cmake_minimum_required(VERSION 3.20)
project(coinor_minimal CXX)

# Minimal CMake build of the COIN-OR trio that libcns_dump_64.dll links.
#
# WHY NOT AUTOTOOLS: the git trees are autotools only and this box has no autoconf/automake/make
# (only Git's MSYS2 bash, CLion's mingw32-make and CMake/ninja). Running the shipped `configure`
# works, but the generated makefiles insist on re-running config.status --recheck, and libtool's
# probing then breaks on the space in "C:/Program Files/...". So: use configure ONCE (for Clp's
# config_clp.h) and compile the sources directly with CMake.
#
# The config headers come from the *_default.h files that COIN-OR ships for exactly this case,
# except Clp's, where the real configure-generated header is available.

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE OFF)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()
add_compile_options(-w -O2)

# Old COIN-OR code + modern libstdc++: force the standard headers they used to get transitively.
# The third party sources themselves are left untouched.
add_compile_options(-include ${CMAKE_CURRENT_SOURCE_DIR}/compat/coin_compat.h)
# compat/ also supplies a tiny <endian.h> (POSIX header, absent on MinGW); search it first.
include_directories(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/compat)
# ClpConfig.h picks its math header with HAVE_CMATH / HAVE_MATH_H; the configure-generated
# config_clp.h does not carry it, and the MinGW build has <cmath>.
add_compile_definitions(HAVE_CMATH)

set(TP ${CMAKE_CURRENT_SOURCE_DIR})
set(GEN ${TP}/gen)
set(CU_SRC ${TP}/src/coinutils-2.10/CoinUtils/src)
set(OSI_SRC ${TP}/src/osi-0.107/Osi/src/Osi)
set(CLP_SRC ${TP}/src/clp-1.15.3/Clp/src)

file(GLOB CU_CPP ${CU_SRC}/*.cpp)
file(GLOB OSI_CPP ${OSI_SRC}/*.cpp)
file(GLOB CLP_CPP ${CLP_SRC}/*.cpp)
file(GLOB CLP_OSICLP_CPP ${CLP_SRC}/OsiClp/*.cpp)

# BUILD DEVIATION, documented in third_party/README.md section 4.4:
# Clp ships a second, optional simplex ("Abc", accelerated basic columns) whose sources are 2016
# era code that does not compile with GCC 13 (incomplete types, endian assumptions, POSIX-isms).
# lcns reaches Clp through OsiClpSolverInterface -> ClpSimplex and never touches AbcSimplex, so
# those translation units are left out. Everything else of Clp is built.
foreach(f ${CLP_CPP})
  get_filename_component(n ${f} NAME)
  if(n MATCHES "^Abc" OR n MATCHES "^CoinAbc" OR n STREQUAL "ClpMain.cpp")
    list(REMOVE_ITEM CLP_CPP ${f})
  endif()
  # optional Cholesky backends that need external solvers (MUMPS / TAUCS / UFL / WSSMP);
  # the in-house ClpCholeskyBase + ClpCholeskyDense are kept.
  if(n MATCHES "^ClpCholesky(Mumps|Taucs|Ufl|Wssmp|WssmpKKT)\\.cpp$")
    list(REMOVE_ITEM CLP_CPP ${f})
  endif()
endforeach()

message(STATUS "CoinUtils sources: ${CU_CPP}")
list(LENGTH CU_CPP n_cu)
list(LENGTH OSI_CPP n_osi)
list(LENGTH CLP_CPP n_clp)
list(LENGTH CLP_OSICLP_CPP n_osiclp)
message(STATUS "counts: coinutils=${n_cu} osi=${n_osi} clp=${n_clp} osiclp=${n_osiclp}")

add_library(coinutils STATIC ${CU_CPP})
target_include_directories(coinutils PUBLIC ${CU_SRC} ${GEN}/coinutils)
add_library(CoinUtils::CoinUtils ALIAS coinutils)

add_library(osi STATIC ${OSI_CPP})
target_include_directories(osi PUBLIC ${OSI_SRC} ${GEN}/osi)
target_link_libraries(osi PUBLIC coinutils)

add_library(clp STATIC ${CLP_CPP} ${CLP_OSICLP_CPP})
target_include_directories(clp PUBLIC ${CLP_SRC} ${CLP_SRC}/OsiClp ${GEN}/clp)
target_link_libraries(clp PUBLIC osi coinutils)
