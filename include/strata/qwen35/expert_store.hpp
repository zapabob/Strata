#pragma once
// Opt-in Qwen3.6 expert pack. The engine default stays the legacy host arena.
// This path writes the same bytes as expert_blob() into a file and maps that
// file. It does not cudaHostAlloc or malloc the full expert arena.
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace strata::qwen35 {

inline constexpr char kExpertPackMagic[8] = {'Q', '3', '6', 'E', 'P', 'K', '1', '\0'};
inline constexpr uint32_t kExpertPackVersion = 1;
inline constexpr uint32_t kExpertPackPrefixBytes = 128;
inline constexpr uint32_t kExpertPackRecordBytes = 128;
inline constexpr uint32_t kExpertPackVersionField = 8;
inline constexpr uint32_t kExpertPackPayloadOffsetField = 64;
inline constexpr uint64_t kExpertPackAlign = 4096;
inline constexpr uint64_t kQ36ExpertTail = 4096;

struct ExpertBlobLayout {
    uint32_t gu_type = 0;
    uint32_t d_type = 0;
    uint32_t n_embd = 0;
    uint32_t n_ff = 0;
    uint32_t n_expert = 0;
    uint64_t gu_row = 0;
    uint64_t d_row = 0;
    uint64_t up_off = 0;
    uint64_t down_off = 0;
    uint64_t blob_bytes = 0;
    uint64_t stride = 0;
};

struct ExpertSource {
    const uint8_t* gate = nullptr;
    const uint8_t* up = nullptr;
    const uint8_t* down = nullptr;
    uint64_t src_gsz = 0;
    uint64_t src_dsz = 0;
};

struct PackLayer {
    ExpertBlobLayout layout;
    ExpertSource source;
};

struct PackBuildRequest {
    std::string model_path;
    std::vector<PackLayer> layers;
    uint64_t tail = kQ36ExpertTail;
};

// One expert: gate at 0, up at up_off, down at down_off, everything else in the
// stride zero. Returns false without writing when the copies would overlap or
// run past the stride.
bool pack_expert_blob(const ExpertBlobLayout& layout, const ExpertSource& src, uint32_t expert, uint8_t* dst);

class MappedExpertPack {
public:
    MappedExpertPack();
    ~MappedExpertPack();
    MappedExpertPack(MappedExpertPack&&) noexcept;
    MappedExpertPack& operator=(MappedExpertPack&&) noexcept;
    MappedExpertPack(const MappedExpertPack&) = delete;
    MappedExpertPack& operator=(const MappedExpertPack&) = delete;

    const uint8_t* layer_data(uint32_t layer) const;
    uint64_t layer_bytes(uint32_t layer) const;
    uint32_t layer_count() const;
    const std::string& path() const;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
    friend std::unique_ptr<MappedExpertPack> open_or_build_expert_pack(const PackBuildRequest& req, std::string& err);
};

// Reuses a pack only when the model hash, geometry, and payload hash match.
// A failed build deletes its .partial file and does not fall back to an
// anonymous arena. A bad published file is moved aside as .rejected.
std::unique_ptr<MappedExpertPack> open_or_build_expert_pack(const PackBuildRequest& req, std::string& err);

// Empty string means the file matches the model and, when expected is set, that geometry.
std::string expert_pack_verify(const std::string& pack_path, const std::string& model_path,
                               const std::vector<PackLayer>* expected, uint64_t tail);

std::string expert_pack_sha256_file(const std::string& path, std::string& err);
uint64_t expert_pack_last_scratch_bytes();

}  // namespace strata::qwen35
