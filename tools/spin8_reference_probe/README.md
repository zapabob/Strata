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
uv run --no-project --offline --python <python312> python -m pytest -q tools/test_spin8_reference_compare.py
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

The probe retains the original deterministic numerical cases: chirality,
2pi/4pi, identity, F32/F64 loopback, Hadamard blocks, reduce, matrix multiply,
attention, query identity and finite-difference query gradients. Tolerances are
reported by each acceptance check in the Python source. These checks cover the
small CPU numerical surface, not model inference or release qualification.
