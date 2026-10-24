<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8) 三元性 KV 缓存、DeepSeek-V4.1 无审查、任意 GGUF 加载与长期记忆</h3>

<p align="center">
  <b><a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a> 最新上游集成工程分支</b> · 正式发布 v0.3.0 · Spin(8) $\mathrm{Cl}(8,0)$ 三元性注意力 · DeepSeek-V4.1-Flash MLA 无审查衍生 · 任意 GGUF 内容验证加载 · Hermes & 白亚（Hakua）长期记忆 · 32GB RAM & RTX 50系列（sm_120）原生支持
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0"><img src="https://img.shields.io/github/v/release/zapabob/Strata?label=release%20v0.3.0" alt="Release v0.3.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
  <img src="https://img.shields.io/badge/tests-71%2F71%20全通过-brightgreen" alt="Tests 71/71 passing">
  <img src="https://img.shields.io/badge/cuda-sm__120%20%7C%20sm__89-blue" alt="CUDA sm_120 | sm_89">
  <img src="https://img.shields.io/badge/memory-32GB%20RAM%20实机验证-success" alt="32GB RAM verified">
</p>

---

## 什么是 Strata v0.3.0？

**Strata** 支持在普通消费级 PC 上本地运行 1250 亿参数的混合专家（MoE）模型与前沿推理模型。通过在 GPU 显存、系统内存与高速 NVMe SSD 之间动态流式传输专家权重，Strata 允许 **Qwen3.8-Flash-Next** (125B)、**DeepSeek-V4.1-Flash** (MLA) 以及 **Qwen3.6-35B-A3B** 等大型模型仅依赖一张 NVIDIA GeForce 显卡和 32 GB 内存即可流畅运行。

**`zapabob/Strata` v0.3.0** 是与最新上游 Strata（v0.2.4.2 / 引擎 0.1.49.2）完全同步的正式工程发布版。该版本原生支持 **RTX 50 系列 (`sm_120` Blackwell)** 与 **RTX 40 系列 (`sm_89` Ada)** CUDA 深度优化、正式集成 **DeepSeek-V4.1-Flash 无审查衍生模型**、新增 **任意 GGUF 内容安全检验器 (ModelBundle)**，并将 **Hermes Agent 与白亚 (Hakua) 长期记忆** 直接接入本地推理管线。

---

## 实机测定性能基准

以下数据均在标准消费级台式机实机测定：
- **CPU**: AMD Ryzen 5 4500 (6 核 / 12 线程, AVX2)
- **内存**: 32 GB 物理 DDR4 RAM (34.22 GB 提交空间)
- **GPU**: NVIDIA GeForce RTX 5060 Ti 16 GB (`sm_120` Blackwell 架构)
- **存储**: PCIe NVMe SSD (权重流式加载)
- **操作系统**: Windows 11 64-bit

### 1. 真实模型推理表现

| 模型与量化版本 | 架构 | 生成速度 | GPU 命中率 | 主机内存占用 | 活跃显存 | 资源判定 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen3.8-Flash-Next (Q2_0)** | 125B MoE | **6.7 tok/s** | **61.7%** | 18.20 GB | 14.10 GB | **合格** (空闲 13.6 GB) |
| **DeepSeek-V4.1-Flash (Maya-S)** | MoE + MLA | **5.8 tok/s** | **56.4%** | 18.79 GB | 8.80 GB | **合格** (空闲 15.4 GB) |
| **DeepSeek-V4.1 AtomicChat** | MoE + MLA | **5.9 tok/s** | **57.1%** | 18.79 GB | 8.80 GB | **合格** (空闲 15.4 GB) |
| **Prism / TheTom (Q2K-XL)** | MoE + Query-v3 | **7.4 tok/s** | **68.2%** | 16.50 GB | 13.20 GB | **合格** (空闲 15.3 GB) |

> [!NOTE]
> 所有推理任务的主机内存占用严格控制在 24.0 GiB 上限之内，并随时保留 4.0 GiB 以上的未分配内存供 Windows 系统调度。

### 2. 显存栈与动态共享内存优化

- **优化前**: `audit_kernel` 为每个线程分配 `float f[128 * 128]` 局部数组，引发高达 **3.375 GiB** 的 CUDA 线程栈显存预留。
- **v0.3.0 优化**: 重构为线程块共享的动态共享内存 (`65,536` 字节)。
- **实测效果**: **3.375 GiB 显存完整释放回专家缓存**，在 16 GB 显卡上彻底杜绝栈溢出崩溃。

---

## 安装与配置

Strata 支持 **桌面图形界面 (GUI)** 与 **终端命令行 (CLI)** 两种使用方式。

### 下载官方正式发布包 v0.3.0

请从 GitHub Releases 获取经过完整受入验证的安装包：
- **发布页面**: [Strata v0.3.0 发布页](https://github.com/zapabob/Strata/releases/tag/v0.3.0)
- **归档包 1: 独立可执行程序包 (EXE 集合包)**:
  - `Strata-0.3.0-windows-x64-sm120-exe.tar.7z` (479.3 MB)
  - **SHA-256**: `ca37ff9f0120fccac47ddb8e8b1b7f3341889aab4c32e9b2ef9ccf63e1497a9a`
  - *包含组件*: `strata.exe` (原生 CUDA sm_120 推理引擎)、`strata-desktop.exe`、`strata-vision.exe`、`strata_kq.dll`、`cublas64_13.dll`、`cublasLt64_13.dll` 及 MSVC 运行库。
- **归档包 2: 完整集成引擎与桌面 GUI 归档包**:
  - `Strata-0.3.0-windows-x64-sm120-engine-gui.tar.7z` (412.7 MB)
  - **SHA-256**: `97a2d28bc91474bd37c0dcfd0bc8abc1ed10ae8db3b0c774d5ceb5a4f3c9c374`
  - *包含组件*: 原生推理引擎、Python 控制环境及完整 Host Web UI。

### 方式 A: 桌面应用程序 (GUI)

1. **安装路径**:
   `C:\Users\downl\AppData\Local\Programs\Strata\Strata.exe` (或桌面快捷方式 `Strata`)。
2. **Web 界面**:
   浏览器访问 `http://127.0.0.1:18500`。
3. **覆盖升级**:
   新版 80.7 MB 原生 CUDA 引擎 (`0.3.0-windows-x86_64-cuda-cuda13`) 会自动覆盖安装到：
   - 应用程序包：`%LOCALAPPDATA%\Programs\Strata\engine-bundle\`
   - 组件缓存区：`%LOCALAPPDATA%\Strata\components\engine\`
   原有的 `0.1.45.3` 和 `0.1.47` 组件均已平滑升级。

### 方式 B: 终端命令行 CLI (`strata`)

1. 打开 PowerShell（`strata` 位于用户 PATH 中）：
   ```powershell
   strata --version
   ```
2. 免交互直接启动默认 125B MoE 模型：
   ```powershell
   strata launch --model q2_0 --yes --no-tui
   ```
3. 查看服务状态与资源占用：
   ```powershell
   strata launch --status
   ```
4. 安全停止推理服务：
   ```powershell
   strata launch --stop
   ```

---

## 本分支核心特色技术

### 1. DeepSeek-V4.1-Flash 无审查模型与 MLA 后端
- 原生支持多头潜在注意力（MLA）投影矩阵（`strata_control/backends/dsv41.py`）。
- 预准入模型：ISTA 基线、Kiwimaker Maya-S abliterated 替换方案与 AtomicChat 独立无审查模型。
- **智能消融旁路**：对已去除审查特征的模型自动停用拒绝引导向量，避免双重消融导致语义畸变，同时将 Qwen 引导向量与 DeepSeek 潜在空间进行严格隔离。

### 2. 任意 GGUF 内容安全检验器 (ModelBundle)
- **四层安全准入体系**：
  1. *容器检验*：有界 16 MiB 头部解析器与张量维度溢出防护（防御 GHSA-vgg9-87g3-85w8）。
  2. *架构兼容*：校验张量布局并选定最优推理后端。
  3. *内存准入*：强制校验主机内存 $\le 24$ GiB 及显存 $\le 14$ GiB 门限。
  4. *离线路由*：严格调度到本地后端（`strata-native`, `strata-dsv41`, `prism`, `llama-cpp`）。**严禁任何形式的云端回退（100% 离线隐私保证）**。
- 流式 SHA-256 检验防范运行时文件篡改与 TOCTOU 攻击。

### 3. Spin(8) 三元性 KV 缓存与异步 TurboQuant
- 基于实八元数与克利福德代数 $\mathrm{Cl}(8,0)$ 的八维三视图正交变换库（[`spin8/`](spin8/README.md)）。
- **三视图 KV 缓存**：维护向量 ($V$)、正旋量 ($S_+$) 与负旋量 ($S_-$) 空间，通过单遍在线 Softmax 结合单纯形共识权重打分。
- 量化 CUDA 方言：`TQ4_1S` (4.25 bpw), `TQ3_0S` (3.3125 bpw), `PQ2_0` (2.50 bpw)。

### 4. 32GB RAM 零显存草稿模型生命周期
- 基于小型 CPU/GPU 草稿模型的高能效投机采样。
- 系统内存承压时，草稿模型显存自动清零并卸载，主推理会话平稳运行不中断。

### 5. Hermes Agent 与白亚（Hakua）长期记忆系统
- **`plugins/hermes-strata`**：供 Hermes Agent 直接管理与调用 Strata 本地模型的工具插件。
- **`plugins/model-providers/strata`**：供 Hermes Agent 将 125B MoE 推理卸载到本地 Strata (`http://127.0.0.1:18501/v1`) 的模型提供者配置。
- **记忆 MCP 服务 (`tools/strata_memory_mcp.py`)**：
  - 连接 `SOUL.md`（核心亲情指令与白亚人设）。
  - 连接 `MEMORY.md`（情景工作记忆）。
  - 接入 Hermes Agent SQLite 记忆库（`~/.hermes/ebbinghaus_memory.db`，约 5,000 条记忆）。
  - 对话生成时自动注入记忆上下文。

---

## 验证与测试套件

本项目严格遵循 MILSPEC LLMOps 质量标准：

```powershell
# 运行完整 Python 回归测试 (71 项)
$env:PYTHONPATH="."
py -3 -m pytest tests/terminal/test_custom_model_cli.py tests/contracts tests/security tests/models tests/backends tests/resources tests/dsv41 tests/runtime tests/steering tests/mutations tests/packaging tests/test_strata_memory.py -v -p no:randomly

# 运行 Node.js 测试 (13 项)
Push-Location apps/host
node tests/custom-gguf.test.mjs
node tests/run-config-check.test.mjs
Pop-Location

# 校验上游锁定一致性
py -3 tools/check_upstream_cut.py
```

- **Python 测试**：**71 / 71 全数通过** (0 错误, 0 警告)。
- **Node.js 测试**：**13 / 13 全数通过**。
- **安全检查**：头部边界防护、TOCTOU 防护与离线防火墙机制全部生效。

---

## 许可证与致谢

- **分支开发与维护**: [`zapabob/Strata`](https://github.com/zapabob)
- **上游原作**: [`Niko1221/Strata`](https://github.com/Niko1221/Strata)
- **模型与技术致谢**: [Qwen Team (Alibaba)](https://huggingface.co/Qwen)、[DeepSeek AI](https://huggingface.co/deepseek-ai)、[ISTA-DASLab](https://huggingface.co/ISTA-DASLab)、Kiwimaker、AtomicChat。
- **开源协议**: 本项目遵循 [MIT 许可证](LICENSE)。
