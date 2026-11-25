# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

**充分调动 Windows PC 全部硬件资源（GPU、物理核心 + SMT 线程、系统内存与 NVMe/SSD 存储）的本地 AI 推理环境。** Hakua 是 [Niko1221/Strata](https://github.com/Niko1221/Strata) 的独立分支（`zapabob/Strata`），合并了官方上游 **v0.2.21**（`d46f5f268`，引擎/Control `0.1.67`），同时保留全部分支专属运行时、记忆与智能体工作流以及 Blackwell CUDA 13.5 深度优化。

## 0.8.1（引擎 0.7.0）更新亮点

- **四层全机异构推理（GPU + 6P/6SMT CPU + RAM + SSD）**：
  - **Windows 原生 `aux_cpus` CPU Sets 与 SMT I/O 隔离**（`aux_cpus.hpp`、`ssd_stream_scheduler.hpp`、`direct_file.cpp`）：将 GPU 主线程与 AVX2 MoE 计算严格绑定到物理主核心，同时将全部 SMT 辅助线程（6核12线程 CPU 上为 `io_smt=[1,3,5,7,9,11]`）专用于 6 线程异步 Direct I/O 与 `PrefetchVirtualMemory` 预取。
  - **全部 5 个 CUDA 13.5 / SM120 Blackwell 原生引擎全新重编译**（`strata.exe`、`strata-inkling2.exe`、`strata-inkling.exe`、`strata-hy4.exe`、`strata-q38.exe`）：整合 Gen-K/L 零拷贝映射门铃、WDDM 1536 MiB 显存保护（防止静默溢出至共享显存）、遵循 Windows 提交上限的安全内存预算（`hy4_cpu_experts.cpp`、`inkling2_engine.cu`）、Windows 物理核绑核与 `_mm_pause` 自旋等待（`ink_hybrid.cuh`），以及 SM120 Q38 锁页词嵌入缓存与批量 `PrefetchVirtualMemory`（`engine/q38/src/engine.cu`）。
  - **统一全机启动器与预设**：`tools/full_machine_infer.py`（`--list-models`、`--plan`、`--bench`、`--serve`）自动探测 GPU、物理/SMT CPU 拓扑、内存/提交余量与双 SSD，生成三层调度方案与 `configs/` 下的服务配置。
- **官方上游 v0.2.21 三方合并**：引入官方统一四层 GPU+RAM+CPU+SSD MoE、多卡 `--layer-split`、GUI 同步及 Control/引擎 `0.1.67` 修复，并完整保留 `/btw`、`/deepresearch`、RustXNG Full、工作流技能、Q38 稠密运行器、DeepSeek 扩展、Hermes `inkling2` 接入与 kuraneko1（MIT）配置表。

## 实机基准测试

测试平台：**NVIDIA GeForce RTX 5060 Ti 16 GB（SM120, CUDA 13.5）· AMD Ryzen 5 4500（6核12线程）· 32 GB DDR4 · 双 SSD（`C:` Crucial P3 NVMe + `H:` S5-1TB SSD）**（16 token 输入 / 32 token 贪心解码）：

| 模型（大小） | 引擎与上下文 | 启用层级 | 预填充 (`pp`) | 解码 (`tg`) | 一致性 |
|---|---|---|---:|---:|---|
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | GPU 10.85 GiB (2232 专家) + 锁页 RAM 4.34 GiB (840 专家) + 6P/6SMT | **85.08 t/s** | **42.22–42.33 t/s** | **32/32 完全一致** |
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | 三层溢出：GPU 10.85 GiB + RAM 3.60 GiB + **SSD mmap 0.74 GiB (`prefetch=on`)** + 6P/6SMT | 64.80 t/s | 14.24 t/s | **32/32 完全一致** |
| **Inkling-2-Mini UD Q4_K_M** (15.47 GiB) | `strata-inkling2.exe` · 16K (Q8 KV) | GPU 10.42 GiB (2339 专家) + 锁页 RAM 3.34 GiB (733 专家) + 6P/6SMT | **109.64 t/s** | **53.28 t/s** | 正常生成 |
| **Qwen3.8-27B 3.69bpw MTP** (11.73 GiB) | `strata-q38.exe` · 4K (F16 KV) | GPU SM120 权重 (10.44 GiB) + 锁页嵌入传输 + `PrefetchVirtualMemory` | 6.21 s (冷启动) | **29.95 t/s** | 正常生成 |

*CPU 线程策略实测（Ryzen 5 4500 A/B 对比）*：将 6 物理核专用于计算、6 SMT 线程（`1,3,5,7,9,11`）专用于异步 I/O 时达到 **42.22–42.33 t/s**；若将 11 个计算工作线程超配到 SMT 超线程上，因带宽竞争降至 **29.68 t/s**（-21.9%）。

## 版本与下载

当前版本：**0.8.1** — GitHub Latest：[v0.8.1 发布页](https://github.com/zapabob/Strata/releases/tag/v0.8.1)

- **桌面安装程序**：`Strata-0.8.1-windows-x64-setup.exe`（当前用户 Tauri/NSIS 安装，内置 Node 24.22.3、Python、Control 0.6.3 与 RustXNG Full）
- **安装包归档**：`Strata-0.8.1-windows-x64.tar.7z`（安装程序 + `SHA256SUMS.txt`）
- **CUDA 13.5 SM120 引擎组件（可选）**：`strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz`（含全部 5 个重编译 SM120 引擎：`strata.exe`、`strata-inkling2.exe`、`strata-inkling.exe`、`strata-hy4.exe`、`strata-q38.exe`）
- **Hy4-Flash 组件（可选）**：`strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`

请始终从发布页的 **Assets** 列表下载并校验 SHA-256 摘要。组件 ed25519 签名验证已移除（无签名密钥），无 Windows Authenticode 代码签名；**`releaseQualified=false`**。

![Hakua / Strata real-model Japanese chat on Qwen3.8-27B](docs/media/native-qwen38-japanese-chat.png)
*Hakua / Strata 桌面端通过 `strata-q38.exe` 运行 `qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf`（CUDA 13.5 / RTX 5060 Ti 16 GB）。*

## 快速开始（桌面端与全机启动器）

### 桌面端安装或覆盖更新

1. 完成当前请求、卸载模型、备份应用数据，并完全退出 Strata（含系统托盘图标）。
2. 将 `Strata-0.8.1-windows-x64-setup.exe` 覆盖安装到现有目录，即可保留模型、对话、记忆、工具、API 密钥与审批设置。
3. 在应用内通过「我已有文件」导入 `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz`，选择兼容模型或本地 GGUF 后点击加载。详见[安装与回滚](docs/HAKUA_INSTALL.md)。

### 全机推理启动器（`tools/full_machine_infer.py`）

```powershell
# 探测 GPU/CPU/RAM/SSD 层级并列出本地模型与调度方案
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --list-models

# 使用全机配置运行 Sakura Inkling-2-Mini 131K 基准测试
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --bench --model Sakura --max-new 32

# 启动本地 OpenAI/Anthropic 兼容 API 服务（127.0.0.1:8092，带内存整理）
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model Sakura --port 8092 --squeeze
```

## 推荐 GGUF 与分支功能

- **16 GB 显存推荐 Qwen3.8-27B GGUF**：实测使用 [soyaakinohara 发布的 3.69 bpw 混合量化 GGUF](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf)（感谢 **soyaakinohara** 与 **AEON-7**）。建议先以 4,096 上下文运行；文件名中的 `12GB` 不保证可在 12 GB 显存上运行。
- **自研 Q38 稠密运行器（`strata-q38.exe`）**：逐张量支持 11 种混合量化格式（`F32`、`F16`、`BF16`、`Q8_0`、`Q4_K`、`Q5_K`、`Q6_K`、`IQ3_S`、`IQ2_S`、`IQ4_XS`、`PQ2_0`）、Tensor Core 预填充、Spin(8) / TurboQuant KV 模式（`auto`：`f16` → `f16_turbo4` → `spin8_k8v4`）、MTP `K=3` 草稿验证与可选日语输出配置。详见 [QWEN38_DENSE_NATIVE.md](docs/QWEN38_DENSE_NATIVE.md)。
- **智能体与工作流能力**：带独立停止控制的无工具旁路子代理 `/btw`、内置 RustXNG Full 的 `/research` 与 `/deepresearch`（启用时向外部搜索引擎发送查询）、可选私有工作流技能学习与应用、工作区与侧边栏文件操作及作用域记忆。详见 [WORKFLOW_SKILLS.md](docs/WORKFLOW_SKILLS.md) 与 [BROWSER_SEARCH.md](docs/BROWSER_SEARCH.md)。

## 安全下限与限制

保持原有安全保护阈值不变：**可用内存 >= 3 GiB**、**提交余量 >= 4 GiB**、**GPU 预留 >= 768 MiB**（<= 17 GiB 显卡 Inkling-2 默认 WDDM 1536 MiB）、**`C:` 可用 >= 5 GiB**、**`H:` 可用 >= 10 GiB**。通用模型质量、全窗口长上下文推理与多客户端 GPU 并发仍未认证（**`releaseQualified=false`**）。本 Windows 发行包不包含原生图像输入或 Linux/macOS 推理验证。历史测试记录保留在 [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md)。

## 文档与开发

[安装指南](docs/HAKUA_INSTALL.md) · [发布验证](docs/HAKUA_RELEASE.md) · [API 与硬件](docs/AI_REFERENCE.md) · [Terminal](docs/TERMINAL.md) · [源码构建](docs/SOURCE_INSTALL.md) · [打包说明](tools/packaging/README.md) · [贡献指南](.github/CONTRIBUTING.md) · [安全说明](.github/SECURITY.md) · [许可证](LICENSE)

```powershell
pytest tests/test_full_machine_infer.py
python -m pytest terminal/tests/terminal
```

```powershell
cd app/host
pnpm test
pnpm run build
```

[Niko1221/Strata](https://github.com/Niko1221/Strata) · [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [第三方许可声明](third_party/)

## 致谢

衷心感谢 **Niko1221/Strata**、**kuraneko1 (`_ryu15_`)**、**ggml & llama.cpp**、**NousResearch (Hermes Agent)**、**Qwen Team (Alibaba Cloud)**、**NVIDIA**、**RustXNG**、**libstrix**、**Node.js / Python / Tauri**、**Microsoft**、**ISTA-DASLab**、**PrismML**、**TurboQuant**、**Spin(8)**、**soyaakinohara** 以及 **AEON-7** 为本地开源 AI 生态提供的卓越基石与贡献。
