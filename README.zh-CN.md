<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8) 三元性 KV 缓存、TurboQuant CUDA 方言与原生 MoE 推理引擎</h3>

<p align="center">
  <b>基于 <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a> 的深度工程分支</b> · Spin(8) $\mathrm{Cl}(8,0)$ 三元性注意力 · 三视图量化 KV 缓存 · Query-v3 `.prismq3` 旁路适配器 · 完整 GUI 与 CLI 控制
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## 本分支（`zapabob/Strata`）简介

**`zapabob/Strata`** 是基于 [Strata](https://github.com/Niko1221/Strata)（v0.2.2 / 引擎 0.1.47）构建的量化与注意力优化工程分支。除支持在单台 PC 上通过 GPU 显存、系统内存与 SSD 三级协同流畅运行 1250 亿参数混合专家模型（**Qwen3.8-Flash-Next**、**Qwen3.6-35B-A3B**、**Gyro**、**Swift 1.5**、**NVFP4**）外，本分支在 C++/CUDA 引擎、Python 服务器、CLI 与桌面/Web GUI 全栈引入了 **Spin(8) 三元性（Triality）与 TurboQuant KV 缓存架构**：

### 本分支四大核心特性

1. **Spin(8) 三元性与 $\mathrm{Cl}(8,0)$ 正交变换库（[`spin8/`](spin8/README.md)）**
   - 基于实八元数基（$1, e_1, \dots, e_7$）与对称克利福德代数 $\mathrm{Cl}(8,0)$ 生成元（$\Gamma_0, \dots, \Gamma_7$）。
   - 按手征（Chirality）特征空间将 16×16 旋量分解为三个 8 维表示：**向量表示 ($V$)**、**正半旋量表示 ($S_+$)** 与 **负半旋量表示 ($S_-$)**，严格满足交织恒等式 $U \Gamma(v) U^\top = \Gamma(Rv)$。
   - 每个旋转计划在准入前均经过严格数学审计：Frobenius 正交误差 $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$、最大 Gram 矩阵项误差 $\le 10^{-12}$，以及主元 LU 有符号对数行列式校验（$\operatorname{sign}=+1, |\log|\det|| \le 10^{-12}$）。
   - 内置 2 的幂次块（$1 \dots 1024$，含 8 维 Spin(8) 符号掩码与 128 维 Bonsai 块）归一化 Sylvester Hadamard 变换，以及每 1,024 个 token 或 60 秒自动校验不变量的粘性审计调度器（`spin8_monitor`）。

2. **三视图 Triality KV 缓存与异步 TurboQuant CUDA 方言（[`tqcodec/`](tqcodec/README.md)）**
   - **物理 CUDA 三视图缓存（`cache_cuda.cu`）**：每个注意力头维护三个物理独立的旋转 Key 数组（$V, S_+, S_-$）与一个共享量化 Value 数组，通过单遍在线 Softmax 结合单纯形共识权重 $(\alpha_0, \alpha_1, \alpha_2)$ 以及打包符号高斯 **QJL** 残差草图修正进行打分。
   - **精确异步 CUDA 量化方言**：
     - `TQ4_1S`（4.25 bits/weight）
     - `TQ3_0S`（3.3125 bits/weight）
     - `PQ2_0`（2.50 bits/weight）
   - **针对 SM120（RTX 50 系列）的 `audit_kernel` 动态共享内存修复**：将每线程 `float f[128 * 128]`（64 KiB/线程）的局部数组迁移至动态共享内存（`65,536` 字节），消除了 `tqc_cache_cuda_initialize` 时高达 **3.375 GiB（`3,623,878,656 B`）** 的 CUDA 设备栈内存预留（`audit_local=0`, `audit_delta=0`），为专家缓存释放约 3.3 GiB 显存，使 16 GiB GPU / 32 GiB RAM 环境能够稳定运行全部三种视图（`off`、`f32`、`compressed`）的 Q2 实测生成。

3. **版本化 Query-v3 适配器与 `.prismq3` 旁路文件**
   - 基于经审计的 $\mathrm{Cl}(8,0)$ 分块导出 7 个反对称生成元，构建有界有理切空间映射（Rational Tangent Chart），在位置编码（RoPE）之前对归一化后的查询向量 ($Q$) 施加秩 8 控制器。
   - 支持零分配融合 CUDA 核函数（`query_v3_cuda.h`）以及绑定 SHA-256 校验的 `.prismq3` 旁路文件（`--query-v3-sidecar`），支持 **Prism / TheTom (`qwen35-9b-thetom-q2kxl`)** 与 **Hikari / Bonsai (`bonsai-8b-prism-q1_0_g128`)** 等实验模型。

4. **GUI、CLI 与控制平面无缝集成**
   - **桌面与 Web GUI (`apps/host`)**：在 **Settings → GPU & memory** 中原生提供 **K cache type**、**V cache type**（`f16`、`tq3`、`tq3_spin8_hadamard`、`tq3_spin8_native`）、**Spin(8) KV cache mode**（`off`、`f32`、`compressed`）、**Spin(8) native config path** 与 **Spin(8) native config SHA-256** 设置，并集成实时启动前校验（`run-config-check.mjs`）。
   - **CLI 与 Python 服务器 (`strata_cli`, `strata_control`, `serve/server.py`)**：支持通过 `strata launch --set ...` 或 `strata serve` 传递全部 Spin(8) 与 KV 缓存参数，并在启动前自动验证胶囊配置与 SHA-256 摘要。

---

## 最新分支发布版本：`v0.3.0-preview.20261024.2`

- **发布页面**：[GitHub Release `v0.3.0-preview.20261024.2`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2)
- **引擎 + GUI + 控制端完整归档包**：`Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z`
  - **文件大小**：`412,311,508` 字节
  - **归档 SHA-256**：`7639fb8ffb3c8fd13857a59c6b5d9d8b392c8b82a496442f0486a9405fd16e21`
  - **引擎 (`strata.exe`) SHA-256**：`564e23b5bcd2b0670d0a2d82e7cd2c20cd5afedf85ddca7c653bea11403727db`
- **早期 CLI 预览版**：[`v0.3.0-preview.20261024.1`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.1) · [发布验证文档](docs/releases/preview030.md) · [Triality PoC 研究记录](research/triality_poc/README.md)

### `v0.3.0-preview.20261024.2` 已验证矩阵

| 模块 | 状态 | 验证证据 |
| --- | --- | --- |
| **原生 Windows CUDA 引擎 (`sm120`)** | **已验证** | 使用 Q2 (`Qwen3.8-Flash-Next-GSQ-RCO-Q2_0`) 在 `--spin8-mode off`、`f32` 与 `compressed` 全部三种模式下均成功解码 `READY` 并在 EOS 正常退出（`exit 0`, `--vram-reserve-mib 10240`）。 |
| **`tqcodec` CUDA `audit_kernel` 修复** | **已验证** | 动态共享内存（`65,536` 字节）替代 64 KiB 线程局部数组，消除 3.375 GiB CUDA 栈预留；`tqc_cache_cuda_test.exe`（28,068 项检查）与 `strata_spin8_native_owner_test.exe`（17,361 项检查）通过（`exit 0`）。 |
| **Host GUI 与预检逻辑** | **已验证** | `pnpm --dir apps/host typecheck`（0 错误）、`pnpm --dir apps/host build` 构建成功，`node --test` 19 项测试全部通过。 |
| **Control 与终端 CLI** | **已验证** | `pytest tests/terminal/test_profiles.py`（21 项通过）、`strata doctor --json`（`ok: true`），以及 `engine_component.resolve(..., full=True)` 全文件 SHA-256 校验通过。 |

---

## 快速上手（分支特性）

### 1. 在 GUI（桌面 / Web Host）中配置

1. 解压 `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z`（先解压 `.7z` 再解压内部 `.tar`），或直接覆盖安装至 `%LOCALAPPDATA%\Programs\Strata` 与 `%LOCALAPPDATA%\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13`。
2. 打开 **Settings（设置） → GPU & memory**。
3. 配置 KV 缓存与 Spin(8) 选项：
   - **K cache type (`cache_type_k`)**：`f16`（默认）、`tq3`、`tq3_spin8_hadamard` 或 `tq3_spin8_native`
   - **V cache type (`cache_type_v`)**：`f16`（默认）、`tq3`、`tq3_spin8_hadamard` 或 `tq3_spin8_native`
   - **Spin(8) KV cache mode (`spin8_mode`)**：`off`（默认）、`f32` 或 `compressed`
   - **Spin(8) native config path (`spin8_native_config`)**：已验证的 Spin(8) JSON 胶囊文件绝对路径
   - **Spin(8) native config SHA-256 (`spin8_native_sha256`)**：胶囊文件的 64 位十六进制 SHA-256 摘要

### 2. 使用 `strata` CLI 启动

```powershell
# 默认启动（与上游完全一致）
strata launch --model q2_0 --yes --no-tui

# 启用 Hadamard 旋转 TurboQuant 3-bit KV 缓存
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_hadamard \
  --set cache_type_v=tq3_spin8_hadamard \
  --yes --no-tui

# 启用带 SHA-256 校验的 Spin(8) 原生三视图压缩缓存
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_native \
  --set cache_type_v=tq3_spin8_native \
  --set spin8_mode=compressed \
  --set spin8_native_config=C:\path\to\capsule.json \
  --set spin8_native_sha256=<64-hex-sha256> \
  --yes --no-tui
```

### 3. 直接运行原生引擎 (`strata.exe`)

```powershell
.\strata.exe --pack .\models\q2_0\native-pack `
  --native .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf `
  --ple-gguf .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf `
  --tokens-file .\examples\ready-tokens.txt --max-new 32 --max-context 256 `
  --mmap-experts --expert-cache auto --expert-profile .\data\expert-profile.bin `
  --prefill 32 --eos-ids 248044,248046 --spin8-mode compressed `
  --spin8-native-config .\capsules\q2_0-compressed-capsule.json `
  --spin8-native-sha256 <64-hex-sha256> `
  --check-logits --gpu 0 --spec 2 --suffix-draft 0 --lookup-chain 0 --vram-reserve-mib 10240
```

---

## Strata 基础能力与硬件要求

Strata 可在单台电脑上运行 **[Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)**（125B MoE）与 **[Qwen3.6-35B-A3B](docs/QWEN36.md)**，并提供兼容 OpenAI（`/v1/chat/completions`、`/v1/responses`）与 Anthropic（`/v1/messages`）的本地 API，可直接接入 Claude Code、Codex CLI、OpenCode 等智能体工具。

### 硬件要求与模型梯度

**系统内存（RAM）与显卡显存（VRAM）合计至少需要 32 GB**（Mac 或 Ryzen AI Max 为统一内存）。

| 总内存 (RAM + VRAM) | 推荐模型 | 说明 |
| --- | --- | --- |
| **28–32 GB** | **[Gyro-S](docs/GYRO.md)** (27.6 GB) 或 **[Coder](docs/MODELS.md#coder)** | Gyro-S 适合极限内存配置；Coder 裁剪一半专家以专注编程。 |
| **35–40 GB** | **[Swift 1.5](docs/MODELS.md#swift-15)** IQ2_XS (39.2 GB) 或 **Gyro-M** (35 GB) | Swift 1.5 思考更短更快；Gyro-M 显存占用减少约 20%，质量接近 IQ3_XXS。 |
| **48 GB** | **IQ3_XXS** (47.0 GB) | 3-bit 量化，兼顾速度与质量。 |
| **64 GB** | **IQ3_S** (54.8 GB) 或 **Q2_0** | IQ3_S 在公开基准上追平完整模型；Q2_0 解码速度最快（RTX 5070 上达 94 tok/s）。 |
| **96 GB 及以上** | **UD-IQ4_XS** (72 GB) 至 **Q8_0** (136 GB)、**[NVFP4](docs/NVFP4.md)** | 4 至 8 bit 高精度模型，所有专家常驻内存。 |

---

## 从源码构建与测试

```powershell
# 1. 构建并测试 Spin(8) 独立参考库 (CPU)
cmake -S spin8 -B build\spin8-cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF
cmake --build build\spin8-cpu --config Release
ctest --test-dir build\spin8-cpu -C Release --output-on-failure

# 2. 构建并测试 tqcodec (CPU + CUDA + Spin8 集成)
cmake -S tqcodec -B build\tqcodec-cuda -G "Visual Studio 17 2022" -A x64 -DTQCODEC_ENABLE_CUDA=ON -DTQCODEC_SPIN8_TESTS=ON
cmake --build build\tqcodec-cuda --config Release
ctest --test-dir build\tqcodec-cuda -C Release --output-on-failure

# 3. 构建原生 CUDA 引擎 (strata.exe / spin8_verify)
cmake -S . -B build\engine-cuda -G "Visual Studio 17 2022" -A x64 -DSTRATA_CUDA=ON
cmake --build build\engine-cuda --config Release --target strata spin8_verify

# 4. 运行 Host GUI 与终端控制测试
pnpm --dir apps/host typecheck
pnpm --dir apps/host build
node --test apps/host/tests/native-settings.test.mjs apps/host/tests/spin8-backend.test.mjs apps/host/tests/kv-settings.test.mjs apps/host/tests/kv-engine.test.mjs
py -3 -m pytest -p no:randomly tests/terminal/test_profiles.py
```

---

## 致谢与许可证

- **分支研发 (`zapabob/Strata`)**：Spin(8) $\mathrm{Cl}(8,0)$ 三元性 KV 缓存、`tqcodec` CUDA 量化方言、Query-v3 `.prismq3` 旁路适配器、SM120 `audit_kernel` 动态共享内存优化，以及全栈 GUI/CLI 控制集成。
- **上游项目 ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))**：三级 MoE 流式推理引擎、专家缓存、投机解码、桌面应用与终端 CLI。
- **许可证**：基于 [MIT 许可证](LICENSE) 开源。发布包中附带的 CUDA/cuBLAS 与 Microsoft Visual C++ 运行时库保留各自厂商的再分发条款。
