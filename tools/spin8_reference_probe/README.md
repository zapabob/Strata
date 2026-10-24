# Independent CPU Spin8 reference

This probe writes library outputs. The Python reference constructs octonion and
Clifford operators independently, checks the supplied rotation samples with
FP64 LU, and checks all 256 signed 8x8 Hadamard determinants with exact integer
subset expansion and construction parity. Its tests use a separate integer
Bareiss oracle. No production audit code is copied into the Python reference.

Use a new output directory with enough room for the build and JSON record. On
Windows, run these commands from the repository root with an existing Python
3.12 environment containing pytest, black and flake8. No packages need updating.
For the sidecar CTest, pass that interpreter as `Python3_EXECUTABLE` if CMake
does not find it automatically.

```powershell
cmake -S tools/spin8_reference_probe -B <output>/cpu -G "Visual Studio 17 2022" -A x64
cmake --build <output>/cpu --config Release --parallel 1
ctest --test-dir <output>/cpu -C Release --output-on-failure -j 1
<output>/cpu/Release/spin8_reference_probe.exe --out <output>/probe.json --trials 5000 --python-check 1000 --seed 20261023
uv run --no-project --offline --python <python312> python tools/spin8_reference_compare.py --probe <output>/probe.json --report <output>/reference.json --input-mode fresh --artifact <output>/cpu/Release/spin8_reference_probe.exe --artifact <output>/cpu/spin8/Release/spin8.lib --artifact <output>/cpu/CMakeCache.txt
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:SPIN8_REFERENCE_TEST_PROBE = '<output>/probe.json'
uv run --no-project --offline --python <python312> python -B -m pytest -q tools/test_spin8_reference_compare.py
```

On single-configuration generators, omit `Release/` from executable and library
paths. This CMake project forces CUDA off. CPU results do not qualify CUDA.

The report records source, script, input and optional artifact SHA-256 hashes,
the Git revision, Python version, numerical maxima and failed checks. Use
`--input-mode replay` for an existing input whose build was not freshly verified.
The mode is an explicit caller declaration, supported by retained build and run
logs. Reports are created exclusively; existing reports are never overwritten.

All supplied rotation matrices receive LU sign checks, including samples beyond
`--python-check`. The first `--python-check` samples also receive the full
independent Clifford construction, group/inverse, Triality and action checks.
The first 100 checked samples retain separate rational sign spot checks. Their
denominator limit of 10**12 approximates the FP64 entries; it is not an exact
certificate for those original floating-point values.

Both spinor blocks are compared coefficient by coefficient for every full
construction sample, with maximum error at most 1e-12. The integration
regressions use the explicit `SPIN8_REFERENCE_TEST_PROBE` fixture path and
negate a later sample's entire plus or minus block. This preserves determinant
and Gram matrix, so only a proper coefficient comparison can reject it.

Every trial, extended-loopback and Hadamard-block forward/inverse output is
checked for finite entries immediately after the transform. NaN/Inf failures
exit with a stage and element index before inverse calls or error reductions.
The separate test-only executable intercepts the real probe's transform calls,
returns SPIN8_OK and injects NaN/Inf into the last output element. Its 44 cases
cover F64/F32, both directions and all four Hadamard block sizes. It contains
the injector; the ordinary probe and library do not. Run it with a new output
directory to retain each failed sample and diagnostic:

```powershell
cmake --build <output>/cpu --config Release --target spin8_reference_probe_fault --parallel 1
uv run --no-project --offline --python <python312> python -B tools/spin8_reference_probe/test_finite_outputs.py --executable <output>/cpu/Release/spin8_reference_probe_fault.exe --output-dir <output>/finite-regressions
```

The probe retains the original deterministic numerical cases: chirality,
2pi/4pi, identity, F32/F64 loopback, Hadamard blocks, reduce, matrix multiply,
attention, query identity and finite-difference query gradients. Tolerances are
reported by each acceptance check in the Python source. These checks cover the
small CPU numerical surface, not model inference or release qualification.
