#pragma once

#include <array>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <random>
#include <string>
#include <utility>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <fcntl.h>
#include <io.h>
#else
#include <unistd.h>
#endif

namespace ink2 {

// Owns only the scratch file created for this model instance. The cold reader
// must be closed before this object is released.
class InkExpertSpool {
public:
    static constexpr uint64_t alignment = 4096;
    static constexpr uint64_t disk_reserve = 5ull << 30;

    InkExpertSpool() = default;
    InkExpertSpool(const InkExpertSpool&) = delete;
    InkExpertSpool& operator=(const InkExpertSpool&) = delete;

    ~InkExpertSpool() {
        if (file_) std::fclose(file_);
        if (directory_.empty()) return;
        std::error_code ec;
        std::filesystem::remove(path_, ec);
        if (!ec) std::filesystem::remove(directory_, ec);
        if (ec) std::fprintf(stderr, "[InkCUDA] expert scratch cleanup: %s\n", ec.message().c_str());
    }

    static constexpr uint64_t padded(uint64_t bytes) noexcept {
        return (bytes + alignment - 1) & ~(alignment - 1);
    }

    const std::filesystem::path& path() const noexcept { return path_; }
    uint64_t size() const noexcept { return written_; }

    bool open(const std::filesystem::path& root, uint64_t bytes, std::string& err) {
        std::error_code ec;
        const auto free = std::filesystem::space(root, ec).available;
        if (ec || free < disk_reserve || bytes > free - disk_reserve) {
            err = "Expert scratch volume cannot fit " + std::to_string(bytes) + " bytes plus its 5 GiB reserve";
            return false;
        }
        const auto suffix = std::chrono::steady_clock::now().time_since_epoch().count();
        auto candidate = root / ("inkling-experts-" + std::to_string(suffix) + "-" +
                                 std::to_string(std::random_device{}()));
        if (!std::filesystem::create_directory(candidate, ec)) {
            err = "Cannot create private Expert scratch directory: " + ec.message();
            return false;
        }
        directory_ = std::move(candidate);
        path_ = directory_ / "experts.bin";
        expected_ = bytes;
#ifdef _WIN32
        HANDLE handle = CreateFileW(path_.c_str(), GENERIC_READ | GENERIC_WRITE | DELETE,
                                    FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr,
                                    CREATE_NEW, FILE_ATTRIBUTE_NORMAL | FILE_FLAG_DELETE_ON_CLOSE, nullptr);
        if (handle == INVALID_HANDLE_VALUE) {
            err = "Cannot create Expert scratch file, Windows error " + std::to_string(GetLastError());
            return false;
        }
        const int fd = _open_osfhandle(reinterpret_cast<intptr_t>(handle), _O_RDWR | _O_BINARY);
        if (fd < 0) CloseHandle(handle);
        else {
            file_ = _fdopen(fd, "w+b");
            if (!file_) _close(fd);
        }
#else
        file_ = std::fopen(path_.c_str(), "wbx");
#endif
        if (file_) return true;
        err = "Cannot open Expert scratch stream, errno " + std::to_string(errno);
        return false;
    }

    bool append(const uint8_t* data, size_t bytes, std::string& err) {
        const size_t extent = static_cast<size_t>(padded(bytes));
        if (!file_ || !bytes || extent > expected_ - written_) {
            err = "Expert scratch body lies outside its planned extent";
            return false;
        }
        // Sector-aligned padding keeps the last direct I/O request inside the file.
        static constexpr std::array<uint8_t, alignment> zero{};
        const size_t padding = extent - bytes;
        if (std::fwrite(data, 1, bytes, file_) != bytes ||
            std::fwrite(zero.data(), 1, padding, file_) != padding) {
            err = "Expert scratch write failed at byte " + std::to_string(written_);
            return false;
        }
        written_ += extent;
        return true;
    }

    bool seal(std::string& err) {
        if (!file_ || written_ != expected_ || std::fflush(file_) != 0) {
            err = "Expert scratch extent or flush failed";
            return false;
        }
#ifdef _WIN32
        const int committed = _commit(_fileno(file_));
#else
        const int committed = fsync(fileno(file_));
#endif
        if (committed != 0) err = "Expert scratch sync failed";
        return committed == 0;
    }

    bool reader_attached(std::string& err) {
#ifndef _WIN32
        // The reader and writer keep their descriptors after unlink.
        if (unlink(path_.c_str()) != 0) {
            err = "Cannot unlink the opened Expert scratch file, errno " + std::to_string(errno);
            return false;
        }
#else
        (void)err;
#endif
        return true;
    }

private:
    std::filesystem::path directory_;
    std::filesystem::path path_;
    std::FILE* file_ = nullptr;
    uint64_t expected_ = 0;
    uint64_t written_ = 0;
};

}  // namespace ink2
