# Quantized attention cache CPU reference (2026-10-23)

This is an engine-independent reference implementation in `tqcodec`. It does not
load a model, replace Strata's attention kernel, implement TheTomturboN's GGUF
layout, or establish throughput or quality improvement. The new API is opt-in.

`tq_cache_create` takes a width of at least eight, bounded row capacity, three
row-major orthogonal matrices, simplex weights, and explicit sorted normalized
codebooks. K views share one 2–6 bit codebook and bit width. V has its own
codebook and bit width. Creation checks maximum and normalized Frobenius FP64
Gram errors against `1e-12`, and pivoted determinant log magnitude against
`d*1e-12`. Both determinant signs are accepted. It then copies all
configuration values. Each append computes three
independent rotated K vectors, quantizes them into three physical packed K
buffers with separate FP64 norms, and quantizes V once in common coordinates.
No raw K or V row is retained.

For a query, each transform also acts on Q. A row's scalar score is the simplex
weighted sum of the three compressed K dot products, multiplied by the positive
caller supplied scale. One online softmax spans the allowed rows. Decoded V
enters the running weighted sum. The implementation holds O(width) query
scratch; it does not build an attention matrix. An empty cache or an all-masked
query is rejected. A nonfinite input or intermediate is rejected before an
append commits or the query output is written. There is no QJL term. The
reference API has no persistence or on-disk dialect.

The byte ledger reports `sizeof(cache)` split into fixed and alpha bytes,
allocated vector capacities for three transform matrices, two codebooks, three
K payload arrays, three K norm arrays, and one V payload and norm array. It
uses physical bytes, including reserved row slots and packing tails. Standard
allocator metadata, alignment overhead, temporary scratch, and any external
controller are outside this ledger. The caller can clone state, clear it, or
copy a physical packed row to inspect the three distinct K views and single V.

The focused test uses a width-nine representable fixture to compare with dense
attention, then checks a lossy fixture against independently expanded physical
K rows. It also checks masking, capacity, clear, clone independence,
configuration snapshots, separate V payload sizing, null and short inputs,
no-write errors, extreme positive and negative scores, nonfinite inputs, and a rejected non-orthogonal
transform. These CPU checks do not establish backend/model compatibility.

Validation performed on Windows with MSVC 19.44.35224.0 and the Visual Studio
2022 CMake generator: `cmake -S tqcodec -B "$env:TEMP\strata-tqcache-20261023"
-G "Visual Studio 17 2022" -A x64`, then `cmake --build
"$env:TEMP\strata-tqcache-20261023" --config Release --parallel 1`, then
`ctest --test-dir "$env:TEMP\strata-tqcache-20261023" -C Release
--output-on-failure`. The final build succeeded and both `tqcodec_cpu` and
`tqcodec_cache` passed. An earlier build found an MSVC `uint8_t` conversion
warning and a test lambda capture error; both were repaired before this final
run. The build directory is under `%TEMP%`; MSBuild warns that incremental
builds there may be unreliable. No GPU backend or model runtime was tested.
