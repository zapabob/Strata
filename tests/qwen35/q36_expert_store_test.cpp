#define _CRT_SECURE_NO_WARNINGS
#include "strata/qwen35/expert_store.hpp"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace fs = std::filesystem;
using strata::qwen35::ExpertBlobLayout;
using strata::qwen35::ExpertSource;
using strata::qwen35::PackBuildRequest;
using strata::qwen35::PackLayer;
using strata::qwen35::expert_pack_last_scratch_bytes;
using strata::qwen35::expert_pack_sha256_file;
using strata::qwen35::expert_pack_verify;
using strata::qwen35::kExpertPackMagic;
using strata::qwen35::kExpertPackPayloadOffsetField;
using strata::qwen35::kExpertPackPrefixBytes;
using strata::qwen35::kExpertPackRecordBytes;
using strata::qwen35::kExpertPackVersionField;
using strata::qwen35::kQ36ExpertTail;
using strata::qwen35::open_or_build_expert_pack;
using strata::qwen35::pack_expert_blob;

namespace {

int g_fails = 0;

void check(bool ok, const char* text, int line) {
    if (ok) return;
    std::fprintf(stderr, "FAIL %s:%d %s\n", "q36_expert_store_test.cpp", line, text);
    ++g_fails;
}

#define CHECK(cond) check((cond), #cond, __LINE__)

std::string temp_dir() {
#if defined(_WIN32)
    const char* root = std::getenv("TEMP");
    const unsigned long id = GetCurrentProcessId();
#else
    const char* root = std::getenv("TMPDIR");
    if (!root) root = "/tmp";
    const unsigned long id = (unsigned long) ::getpid();
#endif
    fs::path dir = fs::path(root ? root : ".") / ("q36epk-" + std::to_string(id));
    fs::create_directories(dir);
    return dir.string();
}

void write_bytes(const fs::path& path, const void* data, size_t n) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out.write(static_cast<const char*>(data), (std::streamsize) n);
}

PackLayer make_layer(const std::vector<uint8_t>& gate, const std::vector<uint8_t>& up, const std::vector<uint8_t>& down,
                     uint32_t n_expert, uint64_t src_gsz, uint64_t src_dsz) {
    PackLayer layer;
    layer.layout.gu_type = 12;
    layer.layout.d_type = 8;
    layer.layout.n_embd = 32;
    layer.layout.n_ff = 16;
    layer.layout.n_expert = n_expert;
    layer.layout.gu_row = 1;
    layer.layout.d_row = 1;
    layer.layout.up_off = 16;
    layer.layout.down_off = 32;
    layer.layout.blob_bytes = 48;
    layer.layout.stride = 64;
    layer.source.gate = gate.data();
    layer.source.up = up.data();
    layer.source.down = down.data();
    layer.source.src_gsz = src_gsz;
    layer.source.src_dsz = src_dsz;
    return layer;
}

std::vector<uint8_t> expected_layer(const PackLayer& layer) {
    const uint64_t bytes = layer.layout.stride * layer.layout.n_expert + kQ36ExpertTail;
    std::vector<uint8_t> out((size_t) bytes, 0x5a);
    std::memset(out.data(), 0, out.size());
    for (uint32_t e = 0; e < layer.layout.n_expert; ++e) {
        uint8_t* dst = out.data() + (size_t) e * (size_t) layer.layout.stride;
        std::memcpy(dst, layer.source.gate + (size_t) e * (size_t) layer.source.src_gsz, (size_t) layer.source.src_gsz);
        std::memcpy(dst + layer.layout.up_off, layer.source.up + (size_t) e * (size_t) layer.source.src_gsz,
                    (size_t) layer.source.src_gsz);
        std::memcpy(dst + layer.layout.down_off, layer.source.down + (size_t) e * (size_t) layer.source.src_dsz,
                    (size_t) layer.source.src_dsz);
    }
    return out;
}

void fill_pattern(std::vector<uint8_t>& buf, uint8_t mark) {
    for (size_t i = 0; i < buf.size(); ++i) buf[i] = (uint8_t) (mark + i);
}

}  // namespace

int main() {
    const fs::path dir = temp_dir();
    const fs::path model = dir / "model.gguf";
    const char abc[] = "abc";
    write_bytes(model, abc, 3);
    std::string err;
    const fs::path empty_file = dir / "empty.bin";
    write_bytes(empty_file, "", 0);
    CHECK(expert_pack_sha256_file(empty_file.string(), err) ==
          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    CHECK(expert_pack_sha256_file(model.string(), err) ==
          "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");

    constexpr uint32_t n_expert = 4;
    constexpr uint64_t src_gsz = 8;
    constexpr uint64_t src_dsz = 6;
    std::vector<uint8_t> gate(n_expert * src_gsz), up(n_expert * src_gsz), down(n_expert * src_dsz);
    fill_pattern(gate, 0x11);
    fill_pattern(up, 0x41);
    fill_pattern(down, 0x81);
    const PackLayer layer = make_layer(gate, up, down, n_expert, src_gsz, src_dsz);
    uint8_t one[64];
    CHECK(pack_expert_blob(layer.layout, layer.source, 1, one));
    const std::vector<uint8_t> expect = expected_layer(layer);
    CHECK(std::memcmp(one, expect.data() + 64, 64) == 0);
    CHECK(one[8] == 0 && one[15] == 0);
    CHECK(one[24] == 0 && one[31] == 0);
    CHECK(one[38] == 0 && one[63] == 0);
    CHECK(std::memcmp(one, layer.source.gate + src_gsz, (size_t) src_gsz) == 0);

    ExpertBlobLayout overlap = layer.layout;
    overlap.up_off = 4;
    CHECK(!pack_expert_blob(overlap, layer.source, 0, one));

    PackBuildRequest req;
    req.model_path = model.string();
    req.layers = {layer, layer};
    auto pack = open_or_build_expert_pack(req, err);
    CHECK(pack != nullptr);
    if (!pack) std::fprintf(stderr, "build: %s\n", err.c_str());
    CHECK(expert_pack_last_scratch_bytes() == layer.layout.stride);
    CHECK(expert_pack_last_scratch_bytes() != layer.layout.stride * n_expert);
    if (pack) {
        CHECK(pack->layer_count() == 2);
        CHECK(pack->layer_bytes(0) == expect.size());
        CHECK(std::memcmp(pack->layer_data(0), expect.data(), expect.size()) == 0);
        CHECK(std::memcmp(pack->layer_data(1), expect.data(), expect.size()) == 0);
        const uint64_t payload_at = (kExpertPackPrefixBytes + 2 * kExpertPackRecordBytes + 4095ull) & ~4095ull;
        CHECK(payload_at == 4096);
        std::ifstream file(pack->path(), std::ios::binary);
        file.seekg((std::streamoff) payload_at);
        std::vector<char> got(expect.size());
        file.read(got.data(), (std::streamsize) got.size());
        CHECK(std::memcmp(got.data(), expect.data(), expect.size()) == 0);
        CHECK(!fs::exists(fs::path(pack->path() + ".partial")));
    }

    PackLayer reread = layer;
    reread.source.gate = nullptr;
    reread.source.up = nullptr;
    reread.source.down = nullptr;
    PackBuildRequest again = req;
    again.layers = {reread, reread};
    err.clear();
    auto reused = open_or_build_expert_pack(again, err);
    CHECK(reused != nullptr);
    CHECK(expert_pack_last_scratch_bytes() == 0);
    if (reused) CHECK(std::memcmp(reused->layer_data(0), expect.data(), expect.size()) == 0);

    if (pack) {
        std::fstream bad(pack->path(), std::ios::binary | std::ios::in | std::ios::out);
        bad.seekg((std::streamoff) kExpertPackPayloadOffsetField);
        uint64_t payload_at = 0;
        bad.read(reinterpret_cast<char*>(&payload_at), 8);
        bad.seekp((std::streamoff) payload_at);
        char flip = 0;
        bad.seekg((std::streamoff) payload_at);
        bad.read(&flip, 1);
        flip ^= 0x01;
        bad.seekp((std::streamoff) payload_at);
        bad.write(&flip, 1);
        bad.close();
        const std::string mismatch = expert_pack_verify(pack->path(), model.string(), &req.layers, kQ36ExpertTail);
        CHECK(mismatch.find("hash") != std::string::npos);
    }
    pack.reset();
    reused.reset();
    err.clear();
    auto rebuilt = open_or_build_expert_pack(req, err);
    CHECK(rebuilt != nullptr);
    if (rebuilt) {
        CHECK(std::memcmp(rebuilt->layer_data(0), expect.data(), expect.size()) == 0);
        CHECK(fs::exists(fs::path(rebuilt->path() + ".rejected")));
    }

    const fs::path other = dir / "other.gguf";
    write_bytes(other, "other-model", 11);
    std::vector<uint8_t> fake(kExpertPackPrefixBytes, 0);
    std::memcpy(fake.data(), kExpertPackMagic, 8);
    fake[kExpertPackVersionField] = 99;
    write_bytes(fs::path(other.string() + ".q36epk"), fake.data(), fake.size());
    CHECK(expert_pack_verify(other.string() + ".q36epk", other.string(), nullptr, kQ36ExpertTail).find("version") !=
          std::string::npos);
    PackBuildRequest second = req;
    second.model_path = other.string();
    err.clear();
    auto replaced = open_or_build_expert_pack(second, err);
    CHECK(replaced != nullptr);
    if (!replaced) std::fprintf(stderr, "replace: %s\n", err.c_str());

    const fs::path locked = dir / "locked.gguf";
    write_bytes(locked, "locked-model", 12);
    const std::string lock_path = locked.string() + ".q36epk.lock";
#if defined(_WIN32)
    const uint32_t pid = GetCurrentProcessId();
#else
    const uint32_t pid = (uint32_t) ::getpid();
#endif
    uint8_t pid_bytes[4] = {(uint8_t) pid, (uint8_t) (pid >> 8), (uint8_t) (pid >> 16), (uint8_t) (pid >> 24)};
    write_bytes(lock_path, pid_bytes, 4);
    PackBuildRequest held = req;
    held.model_path = locked.string();
    err.clear();
    auto blocked = open_or_build_expert_pack(held, err);
    CHECK(blocked == nullptr);
    CHECK(err.find("lock") != std::string::npos);
    CHECK(!fs::exists(fs::path(locked.string() + ".q36epk")));
    fs::remove(lock_path);

    const fs::path partial_model = dir / "partial.gguf";
    write_bytes(partial_model, "partial-model", 13);
    write_bytes(fs::path(partial_model.string() + ".q36epk.partial"), "NOPE", 4);
    PackBuildRequest partial_req = req;
    partial_req.model_path = partial_model.string();
    err.clear();
    auto published = open_or_build_expert_pack(partial_req, err);
    CHECK(published != nullptr);
    if (published) CHECK(!fs::exists(fs::path(published->path() + ".partial")));

    PackBuildRequest bad_layout = req;
    bad_layout.model_path = (dir / "overlap.gguf").string();
    write_bytes(bad_layout.model_path, "overlap", 7);
    bad_layout.layers[0].layout.up_off = 4;
    bad_layout.layers[1].layout.up_off = 4;
    err.clear();
    CHECK(open_or_build_expert_pack(bad_layout, err) == nullptr);
    CHECK(!fs::exists(bad_layout.model_path + ".q36epk"));

    std::fprintf(stderr, g_fails ? "%d checks failed\n" : "q36 expert store checks passed\n", g_fails);
    return g_fails ? 1 : 0;
}
