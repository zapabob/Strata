// Load a fixture through the selected runtime's real C API, with CPU metadata-only allocation.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "llama.h"
#include "ggml-backend.h"
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <stdexcept>

struct library {
    HMODULE handle;
    explicit library(const std::filesystem::path & path) : handle(LoadLibraryExW(path.c_str(), nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_DEFAULT_DIRS)) {
        if (!handle) { throw std::runtime_error("cannot load runtime library"); }
    }
    ~library() { FreeLibrary(handle); }
    library(const library &) = delete;
    library & operator=(const library &) = delete;
    template<class T> T api(const char * name) const {
        const FARPROC address = GetProcAddress(handle, name);
        if (!address) { throw std::runtime_error(name); }
        T result;
        static_assert(sizeof(result) == sizeof(address));
        std::memcpy(&result, &address, sizeof(result));
        return result;
    }
};

int wmain(int argc, wchar_t ** argv) {
    if (argc != 4) {
        std::fprintf(stderr, "usage: probe <runtime-directory> <gguf> <load-mtp:0|1>\n");
        return 2;
    }
    try {
        const std::filesystem::path runtime(argv[1]), model_path(argv[2]);
        if (!runtime.is_absolute() || !model_path.is_absolute() || (std::wcscmp(argv[3], L"0") != 0 && std::wcscmp(argv[3], L"1") != 0)) {
            throw std::runtime_error("absolute paths and explicit MTP mode required");
        }
        library ggml(runtime / L"ggml.dll"), llama(runtime / L"llama.dll");
        const auto find_device = ggml.api<decltype(&ggml_backend_dev_by_type)>("ggml_backend_dev_by_type");
        const auto cpu = find_device(GGML_BACKEND_DEVICE_TYPE_CPU);
        if (!cpu) { throw std::runtime_error("CPU backend unavailable"); }
        const auto defaults = llama.api<decltype(&llama_model_default_params)>("llama_model_default_params");
        const auto load = llama.api<decltype(&llama_model_load_from_file)>("llama_model_load_from_file");
        const auto release = llama.api<decltype(&llama_model_free)>("llama_model_free");
        const auto layers = llama.api<decltype(&llama_model_n_layer)>("llama_model_n_layer");
        const auto mtp_layers = llama.api<decltype(&llama_model_n_layer_nextn)>("llama_model_n_layer_nextn");
        auto params = defaults();
        ggml_backend_dev_t devices[] = {nullptr};
        params.devices = devices;
        params.n_gpu_layers = 0;
        params.load_mode = LLAMA_LOAD_MODE_NONE;
        params.no_alloc = true;
        params.load_mtp = std::wcscmp(argv[3], L"1") == 0;
        llama_model * model = load(model_path.u8string().c_str(), params);
        std::printf("{\"loaded\":%s,\"trunkLayers\":%d,\"mtpLayers\":%d,\"noAlloc\":true,\"cpuOnly\":true}\n",
                    model ? "true" : "false", model ? layers(model) : -1, model ? mtp_layers(model) : -1);
        if (model) { release(model); }
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "probe: %s (Windows error %lu)\n", error.what(), GetLastError());
        return 2;
    }
}
