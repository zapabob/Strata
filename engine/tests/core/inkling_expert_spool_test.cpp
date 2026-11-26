// Verify the same scratch writer and cold-reader sharing used by Inkling CUDA.
#include "../../src/inkling2/ink_cold_store.hpp"
#include "../../src/inkling2/ink_expert_spool.hpp"

#include <algorithm>
#include <cstdio>
#include <filesystem>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    const auto root = argc == 2 ? std::filesystem::u8path(argv[1]) : std::filesystem::temp_directory_path();
    bool passed = false;
    std::string error;
    std::filesystem::path scratch;
    {
        ink2::InkExpertSpool spool;
        const std::vector<uint8_t> a(6120, 0xa9);
        const std::vector<uint8_t> b(4097, 0x37);
        const auto a_extent = ink2::InkExpertSpool::padded(a.size());
        const auto total = a_extent + ink2::InkExpertSpool::padded(b.size());
        if (!spool.open(root, total, error) || !spool.append(a.data(), a.size(), error) ||
            !spool.append(b.data(), b.size(), error) || !spool.seal(error)) {
            std::fprintf(stderr, "%s\n", error.c_str());
            return 1;
        }
        scratch = spool.path();
        if (std::filesystem::file_size(scratch) != total) return 2;
        ink2::InkColdStore reader;
        std::vector<ink2::InkColdExpertDesc> descs{{0, 6120, 2048, 0, 0}, {a_extent, 4097, 2048, 0, 0}};
        if (!reader.open(scratch.string(), std::move(descs), a.size(), 1u << 20, 1, error, nullptr, nullptr, true) ||
            !spool.reader_attached(error)) {
            std::fprintf(stderr, "%s\n", error.c_str());
            return 3;
        }
        int slot = -1;
        const auto* cold = reader.demand_wait(1, 0, 1, slot);
        passed = cold && std::equal(b.begin(), b.end(), cold) && reader.scheduler_stats().bytes_read > 0;
        if (slot >= 0) reader.unpin_slot(slot);
    }
    if (!passed || std::filesystem::exists(scratch) || std::filesystem::exists(scratch.parent_path())) return 4;
    std::puts("Inkling scratch extent, cold-read bytes and handle cleanup passed");
}
