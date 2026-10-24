<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8) 三元性 KV 缓存、DeepSeek-V4.1 无审查、任意 GGUF 加载与长期记忆</h3>

<p align="center">
  <b><a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a> 最新上游集成工程分支</b> · Spin(8) $\mathrm{Cl}(8,0)$ 三元性注意力 · DeepSeek-V4.1-Flash MLA 无审查衍生 · 任意 GGUF 内容验证加载 · Hermes & Hakua 长期记忆 · 32GB RAM 深度优化
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## 本分支（`zapabob/Strata`）简介

**`zapabob/Strata`** 是与最新上游 Strata（v0.2.4.2 / 引擎 0.1.49.2）完全同步的深度工程分支。除支持在单台 PC 上通过 GPU 显存、系统内存与 SSD 三级协同流畅运行 1250 亿参数混合专家模型（**Qwen3.8-Flash-Next**、**Qwen3.6-35B-A3B**、**Gyro**、**Swift 1.5**、**NVFP4**）外，本分支在 C++/CUDA 引擎、Python 服务器、CLI 与桌面/Web GUI 全栈引入了 **Spin(8) 三元性 KV 缓存**、**DeepSeek-V4.1 无审查衍生支持**、**任意 GGUF 内容安全加载** 以及 **Hermes / 白亚（Hakua）长期记忆系统**：

1. **Spin(8) 三元性与 $\mathrm{Cl}(8,0)$ 正交变换库（[`spin8/`](spin8/README.md)）**
   - 基于实八元数基（$1, e_1, \dots, e_7$）与对称克利福德代数 $\mathrm{Cl}(8,0)$ 生成元（$\Gamma_0, \dots, \Gamma_7$）。
   - 按手征特征空间将 16×16 旋量分解为三个 8 维表示：**向量表示 ($V$)**、**正半旋量表示 ($S_+$)** 与 **负半旋量表示 ($S_-$)**，严格满足交织恒等式 $U \Gamma(v) U^\top = \Gamma(Rv)$。
   - 每个旋转计划在准入前均经过严格数学审计：Frobenius 正交误差 $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$、最大 Gram 矩阵项误差 $\le 10^{-12}$，以及主元 LU 有符号对数行列式校验（$\operatorname{sign}=+1, |\log|\det|| \le 10^{-12}$）。
   - 内置归一化 Sylvester Hadamard 变换与每 1,024 个 token 或 60 秒自动校验不变量的粘性审计调度器（`spin8_monitor`）。

2. **三视图 Triality KV 缓存与异步 TurboQuant CUDA 方言（[`tqcodec/`](tqcodec/README.md)）**
   - **物理 CUDA 三视图缓存（`cache_cuda.cu`）**：每个注意力头维护三个物理独立的旋转 Key 数组（$V, S_+, S_-$）与一个共享量化 Value 数组，通过单遍在线 Softmax 结合单纯形共识权重 $(\alpha_0, \alpha_1, \alpha_2)$ 以及打包符号高斯 **QJL** 残差草图修正进行打分。
   - **精确异步 CUDA 量化方言**：`TQ4_1S`（4.25 bpw）、`TQ3_0S`（3.3125 bpw）、`PQ2_0`（2.50 bpw）。
   - **SM120（RTX 50 系列）动态共享内存优化**：将局部数组迁移至动态共享内存（`65,536` 字节），消除了 3.375 GiB 的 CUDA 设备栈内存预留，为专家缓存释放约 3.3 GiB 显存。

3. **DeepSeek-V4.1-Flash-1017 无审查衍生模型与 MLA 专用后端（[`strata_control/backends/dsv41.py`](strata_control/backends/dsv41.py)）**
   - 通过专用 `strata-dsv41` 后端原生支持多头潜在注意力（MLA）投影矩阵。
   - 预验证候选模型：ISTA 基线模型、Kiwimaker Maya-S abliterated 分块替换配方，以及 AtomicChat 独立无审查模型。
   - 对已去除审查特征的模型自动旁路拒绝方向引导向量（Refusal Steering），避免二次消融造成回答失真，同时严格杜绝 Qwen 引导向量与 DeepSeek 潜在空间混淆。

4. **任意内容寻址 ModelBundle 检验与确定性本地路由器（[`strata_control/model_bundle.py`](strata_control/model_bundle.py)）**
   - 有界头解析器（$\le 16$ MiB）与张量维度溢出防护（$\operatorname{rank} \le 4, \operatorname{dim} \le 2^{30}$，防御 GHSA-vgg9-87g3-85w8）。
   - 流式 SHA-256 摘要与文件篡改检测。
   - 确定性本地路由（`strata-dsv41`、`strata-native`、`prism`、`llama-cpp`），**严禁任何形式的云端回退**（100% 离线隐私保证）。

5. **Hermes Agent 与白亚（Hakua）长期记忆系统（[`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py)）**
   - 标准 MCP stdio 服务与 CLI：
     - `SOUL.md`：核心人设与白亚亲情对齐指令的读取、更新与自动备份。
     - `MEMORY.md`：基于 `§ [category] YYYY-MM-DD: Title` 格式的情景工作记忆管理。
     - Hermes Agent SQLite 记忆库（`~/.hermes/ebbinghaus_memory.db`，连接约 5,000 条记忆）。
     - Hakua Composite Memory（`~/.hakua-memory`）。
   - 通过 `apps/host/server/memory.mjs` 与 `getEffectiveSystemPrompt()` 在对话时自动注入。

6. **32GB RAM / 16GB VRAM 零显存草稿模型生命周期**
   - 在 Windows 11 + 32 GB RAM + NVIDIA GeForce RTX 5060 Ti 16 GB（`sm_120`）实机通过受入准入测试。
   - 严格遵守计划主机内存 $\le 24.0$ GiB、操作系统保留 $\ge 4.0$ GiB、显存预算 $\le 14.0$ GiB。
   - 在主机内存承压时自动卸载投机采样草稿模型，将草稿模型显存安全清零而不中断主推理进程。

---

## 发布与上游集成状态：`v0.3.0` Upstream Integrated Edition

- **已合并最新上游**：`7dd5cf18e68c639a8773e096c5c79f971ea2a9f5` (v0.2.4.2 / 引擎 0.1.49.2)
- **GUI 安全补丁**：`c487c875d05075113965bc61d822b27179f70639` (配置保存 TOCTOU 修复)
- **分支保留契约**：`ddc8f9e19cafb981ed91caaab0992ca814e6eca9` (F01〜F11 全部保持)
- **准入与验证文档**：
  - 模型准入记录：[_docs/qa/model-acceptance.json](_docs/qa/model-acceptance.json)
  - 基准报告：[bench/custom-gguf/report.md](bench/custom-gguf/report.md)
  - 发布资格证明：[_docs/releases/custom-gguf-qualification.md](_docs/releases/custom-gguf-qualification.md)

### 验证证据概览

| 目标组件 | 状态 | 验证证据 |
| --- | --- | --- |
| **原生 Windows CUDA 引擎 (`sm120`)** | **已验证** | 端口 18501 上的 Q2_0 基线服务（6.7 tok/s，61.7% GPU 命中率）在全测试期间稳定运行未受干扰。 |
| **`tqcodec` 动态共享内存** | **已验证** | 消除 64 KiB/线程栈数组，在 RTX 5060 Ti 16GB 上释放 3.375 GiB 显存。 |
| **任意 GGUF 与 DeepSeek 路由** | **已验证** | ISTA 基线、Maya-S 替换配方及 AtomicChat 独立模型全部通过四层准入测试。 |
| **长期记忆 MCP 与 GUI** | **已验证** | `tests/test_strata_memory.py`（5/5 全通过），验证对话生成时 `SOUL.md` 自动注入。 |
| **回归测试套件** | **已验证** | **Python 测试 71 项全通过**（`pytest -p no:randomly`），**Node.js 测试 13 项全通过**（`apps/host`）。 |

---

## 快速上手（本分支特色功能）

### 1. 使用图形界面（桌面 / Web）

1. 打开 **Settings → GPU & memory**。
2. 配置 KV 缓存与 Spin(8) 参数：
   - **K cache type (`cache_type_k`)**：`f16`（默认）、`tq3`、`tq3_spin8_hadamard`、`tq3_spin8_native`
   - **V cache type (`cache_type_v`)**：`f16`（默认）、`tq3`、`tq3_spin8_hadamard`、`tq3_spin8_native`
   - **Spin(8) KV cache mode (`spin8_mode`)**：`off`（默认）、`f32`、`compressed`
   - **Spin(8) native config path (`spin8_native_config`)**：已审计胶囊 JSON 的绝对路径
   - **Spin(8) native config SHA-256 (`spin8_native_sha256`)**：胶囊文件的 64 位十六进制哈希
3. 进入 **Models** 页面预览并加载任意 GGUF 或 DeepSeek 衍生模型。

### 2. 使用 CLI 与模型资格化工具

```powershell
# 默认启动
py -3 strata.py launch --model q2_0 --yes --no-tui

# 带有 Hadamard 旋转 TurboQuant 3-bit KV 缓存启动
py -3 strata.py launch --model q2_0 `
  --set cache_type_k=tq3_spin8_hadamard `
  --set cache_type_v=tq3_spin8_hadamard `
  --yes --no-tui

# 32GB RAM 约束下任意 GGUF 资格化检查
py -3 tools/qualify_model_bundle.py --manifest path\to\model.gguf --architecture dsv41 --dialect standard

# 检查并锁定上游集成一致性
py -3 tools/check_upstream_cut.py
```

### 3. 使用长期记忆系统

```powershell
# 查看记忆系统状态
py -3 tools/strata_memory_mcp.py status

# 语义检索相关记忆
py -3 tools/strata_memory_mcp.py recall --query "Strata 优化"

# 存入一条情景记忆
py -3 tools/strata_memory_mcp.py remember --text "采用动态共享内存消除 audit_kernel 显存栈占用" --category tech

# 显示当前 SOUL.md 人设指令
py -3 tools/strata_memory_mcp.py soul
```

---

## 硬件要求

Strata 支持在单台普通 PC 上本地运行 **[Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)**（125B MoE）、**[DeepSeek-V4.1-Flash](docs/DEEPSEEK41.md)** 与 **[Qwen3.6-35B-A3B](docs/QWEN36.md)**，并提供 OpenAI / Anthropic 兼容接口。

**至少需要 32 GB 系统内存 + 显存总和。**

| 硬件配置 | 说明 |
| --- | --- |
| **NVIDIA** GeForce RTX 20, 30, 40, 50 系列 (12 GB+ 显存) | 主要 CUDA 目标平台（已在 RTX 5060 Ti 16 GB 与 RTX 5090 32 GB 上实测 `sm120`）。 |
| **AMD** Radeon RX 6800+, RX 7000, RX 9000, Radeon AI PRO R9700 | [AMD HIP 指南](docs/AMD_HIP.md) |
| **Intel** Arc | [Intel Arc](docs/INTEL_ARC.md), [SYCL 引擎](docs/INTEL.md) |
| **Apple Silicon Mac** (M1 或更新, macOS 15+) | [Mac Metal 指南](docs/MAC.md) |
| **AMD Ryzen AI Max (Strix Halo)** | [Strix Halo 指南](docs/STRIX_HALO.md) |

---

## 源码构建与测试

```powershell
# 1. 运行全部 Python 回归测试
$env:PYTHONPATH="."
py -3 -m pytest tests/terminal/test_custom_model_cli.py tests/contracts tests/security tests/models tests/backends tests/resources tests/dsv41 tests/runtime tests/steering tests/mutations tests/packaging tests/test_strata_memory.py -v -p no:randomly

# 2. 运行 Node.js 测试
$env:NODE_OPTIONS=""
Push-Location apps/host
node tests/custom-gguf.test.mjs
node tests/run-config-check.test.mjs
Pop-Location

# 3. 校验上游 Cut 锁定
py -3 tools/check_upstream_cut.py
```

---

## 鸣谢与开源协议

- **工程扩展 (`zapabob/Strata`)**：Spin(8) $\mathrm{Cl}(8,0)$ 三元性缓存、`tqcodec` CUDA 方言、DeepSeek-V4.1 无审查集成、任意 GGUF 内容安全加载、Hermes/白亚 长期记忆基盘、全栈 GUI/CLI 调度。
- **上游 Strata ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))**：三级 MoE 流式引擎、专家缓存、投机解码、桌面应用与终端 CLI。
- **开源协议**：本项目基于 [MIT License](LICENSE) 开源。
