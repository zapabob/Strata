# Long context on a 16 GB Windows GPU

This record concerns the RTX 5060 Ti 16 GB, Ryzen 5 4500 and 32 GB RAM
machine used for the 0.4.1-beta.1 checks. Model files were on an SSD.
It is not a guarantee for every model or another computer.

The model editor offers 96K (98,304 tokens) and 128K (131,072 tokens).
These are total context capacities: reserve room for the generated answer.
Choose a model whose own context limit supports the requested capacity.
The checks below keep the requested length and cache precision and require
the complete input to be evaluated.

## Measured full-window checks

Each check uses a synthetic archive with three different lookup codes at
separated positions. A pass requires the engine to evaluate the full input
without truncation and return all three codes. This is a retrieval smoke test,
not a comprehensive long-context quality benchmark.

| Model and runtime | Capacity | Actual prompt | Result |
| --- | ---: | ---: | --- |
| Qwen3.6-35B-A3B UD-Q4_K_XL, PrismML | 131,072 | 130,792 | Passed: all three codes, 47 output tokens, no truncation |
| Hikari-LoRA-fixed-scale-PQ2_0, PrismML | 131,072 | 130,792 | Passed: all three codes, 47 output tokens, no truncation |
| Swift Qwen3.8-Flash-Next IQ2_XS, native Strata | 98,304 | 98,016 | Not qualified: the original access violation was repaired; a rerun reached 96,256 prompt tokens before the PC became unresponsive and the user restarted it |

The Swift repair passed two short native regressions. Its full rerun did not
produce a completion or answer. Earlier samples recorded about 350 MiB of
available system RAM and heavy disk activity. The restart record contains no
bugcheck code, so the cause of the unresponsive PC is not established. This
configuration must not be presented as a working 98K profile. Further native
long-window checks need continuously recorded RAM/commit headroom and a tested
stop mechanism before another high-load run. Model files remain intact.

The Qwen3.6 check used the unchanged PrismML 0.4.0 executable with SHA256
`90428627933e0c4120fe0bcaa6a3cc7803dd5fe5846102eeacf4cf1298807a8d`.
The request took 1,750,601 ms: prompt processing 1,724,307 ms
(75.85 tokens/second), then 47 output tokens in 26,094 ms
(the engine reported 1.76 tokens/second). Whole-GPU peak used memory was
11,586 MiB, including other applications. Startup took 445,517 ms.
Compilation and packaging ran on the same computer, and disk cache warmth
was uncontrolled. These are observations from one run, not a speedup claim.

The Hikari check used the same PrismML executable, with all layers on the GPU,
Q8_0 K/V, six threads, batch 1,024 and microbatch 256. Startup took 20,237 ms.
The full request took 259,023 ms: prompt processing 257,130 ms (508.66
tokens/second), then 47 output tokens in 1,803 ms (reported 25.51
tokens/second). Whole-GPU peak used memory was 12,740 MiB. This is also a
single retrieval run, not a general performance or quality guarantee.

## Qwen3.6 settings that completed 131K

Open the local model and choose the llama-server / PrismML path. Select 128K,
then set MoE layers in CPU memory to 28 in Expert mode. Use Q8_0 for both K
and V, six CPU threads and a batch of 1,024 (the app derives a microbatch
of 256). Flash
attention is on and parallel requests are limited to one. The measured
command used `--fit off` and `--no-context-shift`, so the successful result
did not depend on automatic resizing or discarding earlier tokens.

CPU MoE placement keeps the selected layers' experts in system memory.
It preserves the weight format but increases CPU work. A model's number of
active parameters is not its total storage requirement. GPU weights, KV
cache, compute buffers and desktop use must all fit in dedicated VRAM;
host weights and the application's other processes must also fit in RAM.
The editor leaves an unknown split-memory estimate unestimated rather than
treating all weights as GPU-resident.

The native Qwen3.6 path is a separate runtime. Its private-cache and
131K-capacity checks do not inherit this PrismML full-window result.
See the [release record](HAKUA_RELEASE.md) for the native executable's tests.

## Caches and long requests

Keep downloaded GGUF files and completed expert packs. Unloading a model
does not delete either. An existing native pack can be reused; choosing
another context capacity should not download the original model again.

Native Qwen3.6 can reuse completed state inside the same authenticated
conversation. Changed or absent ownership, cancellation, errors and five
idle minutes clear that private state. These operations do not remove
model files. The measured PrismML path disabled shared prompt reuse.

Reading a full 131K prompt can take more than five minutes on this machine.
Host completion forwarding now uses a cancellable loopback connection with
a one-hour deadline. Stop still cancels the request. A long wait is not
evidence of a hang when prompt progress continues; the measured Qwen3.6
request took about 29 minutes including its answer.

Windows application files normally belong in
`%LOCALAPPDATA%\Programs\Strata`. Keep large model files at their existing
location. See [installation](HAKUA_INSTALL.md) for the separate signed CUDA
component and [release qualification](HAKUA_RELEASE.md) for exact limits.
