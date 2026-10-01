cmake_minimum_required(VERSION 3.20)
project(lcns LANGUAGES CXX VERSION 0.1.0)

# ---------------------------------------------------------------------------
# Reconstruction of the liblcns.dll (Optalog CNS nesting engine) surface and of
# the algorithm core recovered by reverse engineering.
# See ../re/REPORT.md and docs/MAPPING.md.
# ---------------------------------------------------------------------------

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE RelWithDebInfo CACHE STRING "" FORCE)
endif()

option(LCNS_BUILD_TESTS "Build unit tests" ON)
option(LCNS_BUILD_APPS  "Build demo/probe applications" ON)
option(LCNS_WERROR      "Treat warnings as errors" OFF)

add_library(lcns_flags INTERFACE)
target_include_directories(lcns_flags INTERFACE "${CMAKE_CURRENT_SOURCE_DIR}/include")
if(MSVC)
  target_compile_options(lcns_flags INTERFACE /W4 /permissive- /utf-8 /EHsc)
  if(LCNS_WERROR)
    target_compile_options(lcns_flags INTERFACE /WX)
  endif()
else()
  target_compile_options(lcns_flags INTERFACE -Wall -Wextra -Wpedantic)
  if(LCNS_WERROR)
    target_compile_options(lcns_flags INTERFACE -Werror)
  endif()
endif()

# --- exact geometry kernel  (mirrors ..\exact\* and ..\geom\* of the original) ---
add_library(lcns_geom STATIC src/geom.cpp src/boolean.cpp)
target_link_libraries(lcns_geom PUBLIC lcns_flags)

# --- problem model + NFP map + tiling patterns + row distance/squeeze ---
add_library(lcns_model STATIC src/model.cpp src/nfp.cpp src/tiling.cpp src/row.cpp)
target_link_libraries(lcns_model PUBLIC lcns_geom)

# --- search / strategies / engine / reporting ---
add_library(lcns_nest STATIC src/nester.cpp src/engine.cpp src/io.cpp src/cloud.cpp
                             src/licensing.cpp src/lp.cpp src/lp_column_generation.cpp
                             src/lp_nesting.cpp)
target_link_libraries(lcns_nest PUBLIC lcns_model)
if(WIN32)
  target_link_libraries(lcns_nest PUBLIC ws2_32 iphlpapi)
endif()

# --- ordinal loader for a real liblcns.dll (Windows only) ---
add_library(lcns_api STATIC src/api.cpp)
target_link_libraries(lcns_api PUBLIC lcns_flags)
if(WIN32)
  target_link_libraries(lcns_api PUBLIC kernel32)
  set_target_properties(lcns_api PROPERTIES OUTPUT_NAME lcns_api)
endif()

if(LCNS_BUILD_APPS)
  add_executable(nest_demo apps/demo/main.cpp)
  target_link_libraries(nest_demo PRIVATE lcns_nest)

  add_executable(lcns_probe apps/probe/main.cpp)
  target_link_libraries(lcns_probe PRIVATE lcns_api)

  # benchmark runner: solve a problem.json and print machine readable statistics
  add_executable(nest_eval apps/eval/main.cpp)
  target_link_libraries(nest_eval PRIVATE lcns_nest)
endif()

if(LCNS_BUILD_TESTS)
  enable_testing()
  foreach(t exact conv boolean offset nofit nester model tiling io lp linear_program cloud
            licensing row recovered)
    add_executable(test_${t} tests/test_${t}.cpp)
    target_link_libraries(test_${t} PRIVATE lcns_nest lcns_api)
    add_test(NAME ${t} COMMAND test_${t})
  endforeach()
endif()

# --- code generation of the export table from the reverse-engineering data ---
find_package(Python3 COMPONENTS Interpreter QUIET)
if(Python3_Interpreter_FOUND)
  add_custom_target(gen_api
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/gen_api.py"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    COMMENT "Regenerating include/lcns/detail/api_table.inc from ../re/exports_table.json")
endif()
