#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>

namespace strata::inkling2 {

// Recover a row in the model's original coordinates. The GGUF contract specifies the
// symmetric normalised Sylvester transform, so (scale * codes) H is its physical row.
template <class DecodeHalf>
inline void pq2_h128_row(const uint8_t* src, float* dst, size_t cols, DecodeHalf decode_half) noexcept {
    constexpr float inv_sqrt_128 = 0.08838834764831844f;
    for (size_t col = 0; col < cols; col += 128, src += 34) {
        uint16_t h;
        std::memcpy(&h, src, sizeof(h));
        float* row = dst + col;
        for (unsigned j = 0; j < 128; ++j) {
            row[j] = float(int((src[2 + j / 4] >> (2 * (j % 4))) & 3u) - 1);
        }
        for (unsigned step = 1; step < 128; step *= 2) {
            for (unsigned i = 0; i < 128; i += 2 * step) {
                for (unsigned j = i; j < i + step; ++j) {
                    const float left = row[j], right = row[j + step];
                    row[j] = left + right;
                    row[j + step] = left - right;
                }
            }
        }
        const float scale = decode_half(h) * inv_sqrt_128;
        for (unsigned j = 0; j < 128; ++j) row[j] *= scale;
    }
}

}  // namespace strata::inkling2
