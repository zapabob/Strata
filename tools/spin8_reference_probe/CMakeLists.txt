cmake_minimum_required(VERSION 3.24)
project(spin8_reference_probe LANGUAGES C CXX)

# Build the small CPU library from the same source tree as this probe. No
# pre-existing binary or machine-specific path is trusted implicitly.
set(SPIN8_ENABLE_CUDA OFF CACHE BOOL "CPU-only reference probe" FORCE)
set(SPIN8_BUILD_TESTS ON CACHE BOOL "Build the complete CPU reference suite" FORCE)
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../../spin8" spin8)
enable_testing()
add_executable(spin8_reference_probe probe_spin8.cpp)
target_link_libraries(spin8_reference_probe PRIVATE spin8)
target_compile_features(spin8_reference_probe PRIVATE cxx_std_17)
if(MSVC)
  target_compile_definitions(spin8_reference_probe PRIVATE _CRT_SECURE_NO_WARNINGS)
  target_compile_options(spin8_reference_probe PRIVATE /W4 /WX /fp:strict /EHsc)
else()
  target_compile_options(spin8_reference_probe PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
