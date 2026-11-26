// Teacher-force frozen token sequences with the same CPU Expert offload and KV as Mode B.
#include "ggml-backend.h"
#include "llama.h"

#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

constexpr int CONTEXT = 4096;
constexpr int BATCH = 2048;
constexpr int MICROBATCH = 32;
constexpr int THREADS = 6;
constexpr const char * COLD_EXPERTS = R"(blk\.(0|1|2|3|4|5|22|23)\.ffn_.*_exps)";

static std::vector<llama_token> read_ids(const char * path, int vocab) {
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    const auto bytes = in.tellg();
    if (!in || bytes <= 0 || bytes % sizeof(llama_token) != 0 || bytes > CONTEXT * sizeof(llama_token)) {
        throw std::runtime_error(std::string("Invalid token extent: ") + path);
    }
    std::vector<llama_token> ids(static_cast<size_t>(bytes) / sizeof(llama_token));
    in.seekg(0);
    in.read(reinterpret_cast<char *>(ids.data()), bytes);
    const auto valid = [vocab](llama_token id) { return id >= 0 && id < vocab; };
    if (!in || !std::all_of(ids.begin(), ids.end(), valid)) {
        throw std::runtime_error(std::string("Invalid token IDs: ") + path);
    }
    return ids;
}

static void score(llama_context * ctx, llama_batch & batch, int vocab, bool last,
                  const char * input, const char * output) {
    const auto ids = read_ids(input, vocab);
    const int length = static_cast<int>(ids.size());
    const int32_t dimensions[] = {last ? 1 : length, vocab};
    std::ofstream out(output, std::ios::binary | std::ios::trunc);
    if (!out) {
        throw std::runtime_error(std::string("Cannot write logits: ") + output);
    }
    out.write(reinterpret_cast<const char *>(dimensions), sizeof(dimensions));
    llama_memory_clear(llama_get_memory(ctx), true);
    for (int start = 0; start < length; start += BATCH) {
        batch.n_tokens = std::min(length - start, BATCH);
        for (int i = 0; i < batch.n_tokens; ++i) {
            batch.token[i] = ids[start + i];
            batch.pos[i] = start + i;
            batch.n_seq_id[i] = 1;
            batch.seq_id[i][0] = 0;
            batch.logits[i] = !last || start + i == length - 1;
        }
        if (llama_decode(ctx, batch)) {
            throw std::runtime_error(std::string("Decoder failed on ") + input);
        }
        for (int i = 0; i < batch.n_tokens; ++i) {
            if (!batch.logits[i]) {
                continue;
            }
            const float * logits = llama_get_logits_ith(ctx, i);
            if (!logits) {
                throw std::runtime_error("Missing requested logit row");
            }
            out.write(reinterpret_cast<const char *>(logits), std::streamsize(vocab) * sizeof(float));
        }
    }
    out.close();
    if (!out) {
        throw std::runtime_error(std::string("Incomplete logit output: ") + output);
    }
}

int main(int argc, char ** argv) {
    if (argc < 5 || (argc - 2) % 3 != 0) {
        std::cerr << "Usage: modeb-logits MODEL [all|last TOKENS LOGITS]...\n";
        return 2;
    }
    try {
        ggml_backend_load_all();
        llama_backend_init();
        auto mp = llama_model_default_params();
        const llama_model_tensor_buft_override overrides[] = {
            {COLD_EXPERTS, ggml_backend_cpu_buffer_type()}, {nullptr, nullptr}
        };
        mp.tensor_buft_overrides = overrides;
        mp.n_gpu_layers = 99;
        mp.load_mode = LLAMA_LOAD_MODE_NONE;
        const auto model = std::unique_ptr<llama_model, decltype(&llama_model_free)>(
            llama_model_load_from_file(argv[1], mp), llama_model_free);
        if (!model) {
            throw std::runtime_error("Model load failed");
        }
        auto cp = llama_context_default_params();
        cp.n_ctx = CONTEXT;
        cp.n_batch = BATCH;
        cp.n_ubatch = MICROBATCH;
        cp.n_threads = THREADS;
        cp.n_threads_batch = THREADS;
        cp.type_k = cp.type_v = GGML_TYPE_Q8_0;
        cp.flash_attn_type = LLAMA_FLASH_ATTN_TYPE_ENABLED;
        const auto ctx = std::unique_ptr<llama_context, decltype(&llama_free)>(
            llama_init_from_model(model.get(), cp), llama_free);
        if (!ctx) {
            throw std::runtime_error("Context allocation failed");
        }
        auto batch = llama_batch_init(BATCH, 0, 1);
        const int vocab = llama_vocab_n_tokens(llama_model_get_vocab(model.get()));
        try {
            for (int i = 2; i < argc; i += 3) {
                const std::string mode = argv[i];
                if (mode != "all" && mode != "last") {
                    throw std::runtime_error("Expected all or last");
                }
                score(ctx.get(), batch, vocab, mode == "last", argv[i + 1], argv[i + 2]);
            }
        } catch (...) {
            llama_batch_free(batch);
            throw;
        }
        llama_batch_free(batch);
    } catch (const std::exception & error) {
        std::cerr << error.what() << '\n';
        llama_backend_free();
        return 1;
    }
    llama_backend_free();
    return 0;
}
