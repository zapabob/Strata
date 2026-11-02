#pragma once
// One stderr line per Qwen3.6 startup stage. stdout stays the serve protocol.
// elapsed_ms and stage_elapsed_ms are steady-clock milliseconds for the stage
// that just finished. They are not a clock since process start.
#include <cstdio>

namespace strata::qwen35 {
inline void q36_startup(const char* stage, const char* state, long long elapsed_ms, long long stage_elapsed_ms,
                        const char* error_code) {
    std::fprintf(stderr,
                 "Q36_STARTUP schema=1 stage=%s state=%s elapsed_ms=%lld stage_elapsed_ms=%lld error_code=%s\n",
                 stage ? stage : "unknown", state ? state : "unknown", elapsed_ms, stage_elapsed_ms,
                 error_code && error_code[0] ? error_code : "null");
}
}  // namespace strata::qwen35
