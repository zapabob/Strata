<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="340">
  </picture>
</p>

<h3 align="center">在你自己的电脑上运行强大的 AI。</h3>
<p align="center">本地聊天、写代码、处理图片。</p>

<p align="center">
  <a href="#模型">模型</a> · <a href="#安装"><b>安装</b></a> ·
  <a href="#硬件">硬件</a> · <a href="#工具">工具</a> ·
  <a href="#分支说明">分支说明</a> · <a href="#帮助">帮助</a> · <a href="#支持-strata">支持</a>
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/latest"><img src="https://img.shields.io/github/v/release/zapabob/Strata?label=fork%20release&color=0ab887" alt="下载本分支"></a>
  <a href="https://github.com/Niko1221/Strata/releases/latest"><img src="https://img.shields.io/github/v/release/Niko1221/Strata?label=upstream&color=555" alt="上游 Strata"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Niko1221/Strata" alt="MIT 许可证"></a>
  <a href="https://buymeacoffee.com/strataengine"><img src="https://img.shields.io/badge/Buy_me_a_coffee-FFDD00?logo=buymeacoffee&logoColor=000" alt="在 Buy Me a Coffee 上支持 Strata"></a>
</p>

<p align="center"><sub><a href="README.md">English</a> · <b>简体中文</b> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a> · <a href="README.pl.md">Polski</a></sub></p>

**免费、开源。**

这是 **[zapabob/Strata](https://github.com/zapabob/Strata)** — [Niko1221/Strata](https://github.com/Niko1221/Strata) 的 Hakua 分支。保留 Hakua 同意式记忆聊天（侧栏 **Hakua**），并在 Windows 包中附带 `host/hakua-chatbot.enabled`，安装后仍默认开启 Hakua。还将 Hermes Agent 的 `SOUL.md` / `MEMORY.md` 接入 Hakua 记忆栈（Ebbinghaus、RAG + 语义图、Obsidian、`hakua sleep`）。同时保留 Spin(8)/Triality、Query-v3、TurboQuant、Bonsai、Hermes 与 Windows `-hakua` 打包，并跟进上游功能、安全与缺陷修复。

| 版本种类 | 值 |
| --- | --- |
| **产品**（应用 / 安装包 / `VERSION`） | **`0.3.2-preview.20261029.2`** |
| **引擎**（CUDA/HIP/SYCL；Metal 另计） | **0.1.53**（Metal **0.1.52-metal**） |
| 模型/硬件说明所跟踪的上游 | **v0.2.7.1**（`46c152a1`，2026-10-28 同步） |

产品版是安装程序与 About 显示的编号。引擎版是应用为显卡下载的 C++ 推理二进制编号。二者按不同节奏更新，请勿混为一谈。

站点: [zapabob.github.io/Strata](https://zapabob.github.io/Strata/) · 详情: [分支说明](#分支说明)


## 模型

我们**首先推荐 ISTA-DASLab**，其次是 **Unsloth** 和其他提供方，前提是有内存放得下的兼容模型。

<details>
<summary><img src="docs/media/models/qwen.svg" width="22" alt="" align="middle"> &nbsp;<b>Qwen3.8-Flash-Next</b></summary>

| 提供方 | 可选项 |
| --- | --- |
| **ISTA-DASLab · 推荐** | Q2\_0, IQ2\_XS, IQ3\_XXS, IQ3\_S。[Coder：IQ1\_M](docs/MODELS.md#coder)，适合写代码。 |
| **Unsloth** | UD-IQ4\_XS, UD-Q4\_K\_XL, UD-Q5\_K\_XL, UD-Q6\_K\_XL, Q8\_0 |
| **Gyro · agentionai** | [Gyro-S, Gyro-M](https://huggingface.co/agentionai/Qwen3.8-Flash-Next-Gyro-GGUF)。占用内存更少，但速度更慢。 |
| **其他选项** | [Swift 1.5](docs/MODELS.md#swift-15), [NVFP4](docs/NVFP4.md), [OrcaRouter](docs/ORCA.md) |

[比较大小、内存需求和兼容性](docs/MODELS.md)。

</details>

<details>
<summary><img src="docs/media/models/qwen.svg" width="22" alt="" align="middle"> &nbsp;<b>Qwen3.6-35B-A3B</b></summary>

**Unsloth:** UD-Q4_K_XL, UD-Q6_K_XL, Q8_0。这些是目前文档中收录的该模型的版本。

[模型指南和兼容性](docs/QWEN36.md)。

</details>

<details>
<summary><img src="docs/media/models/deepseek.svg" width="22" alt="" align="middle"> &nbsp;<b>DeepSeekV4.1-Flash-1017</b></summary>

可在**桌面应用**和**终端**中使用。内存放不下的部分会从 SSD 读取，所以需要大量空闲磁盘空间。

| 版本（IST-DAS） | 下载大小 | 所需空闲磁盘 |
| --- | ---: | ---: |
| 1.75 bpw | 239 GB | 约245 GB |
| 2.00 bpw | 257 GB | 约265 GB |
| 2.25 bpw | 274 GB | 约280 GB |

支持 NVIDIA RTX 30、40 和 50 系列（Windows 和 Linux），以及 AMD Radeon AI PRO R9700（Linux）。安装程序会下载模型文件和 DeepSeek 引擎，然后启动模型。

```sh
strata launch --family deepseek41 --model ist-das-2.00bpw --plan
```

以下为 Strata 0.2.5 上 2.00 bpw 版本的实测结果。“输出”是回答的速度，“提示词”是 Strata 读取你输入内容的速度。

| 硬件 | 输出 | 提示词 |
| --- | ---: | ---: |
| RTX 5070 12 GB, 64 GB 内存 | 4 到 6 tokens/s | 约 110 tokens/s（4K） |
| RTX 3060 12 GB, 46 GB 内存 | 9 到 11 tokens/s | 约 155 tokens/s（4K） |
| 1x Radeon AI PRO R9700, 251 GB 内存 | 21 到 25 tokens/s | 320 到 360 tokens/s (8K) |
| 4x Radeon AI PRO R9700 | 74 到 77 tokens/s | 400 到 450 tokens/s (8K) |

[内存、磁盘和详细信息](docs/DEEPSEEK41.md) · [发行说明](https://github.com/Niko1221/Strata/releases)

</details>

<a id="the-other-sizes"></a>

不确定哪个放得下？[为你的电脑选择模型](docs/MODELS.md#pick-by-memory)。

## 安装

<a id="option-a-the-strata-app"></a>

### 桌面应用（本分支）

**[Windows NSIS（未签名预览）→](https://github.com/zapabob/Strata/releases/download/v0.3.2-preview.20261029.2/Strata_0.3.2-preview.20261029.2_x64-setup.exe)**  
标签: [v0.3.2-preview.20261029.2](https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261029.2) · 更早源码同步: [v0.3.2-preview.20261028.1](https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261028.1) · [本分支全部发行](https://github.com/zapabob/Strata/releases) · [上游发行](https://github.com/Niko1221/Strata/releases/latest)

标签上传资产后的计划文件名：

`Strata_0.3.2-preview.20261029.2_x64-setup.exe`

若下载返回 404，说明 NSIS 构建或 GitHub Release 尚未就绪——请到 [Releases](https://github.com/zapabob/Strata/releases) 取最新已上传的 setup，或等待父任务完成。SHA-256 会在文件发布后写在发行说明中。

安装或覆盖安装（可用 `/S` 静默覆盖），选择模型后即可聊天。默认路径：`%LOCALAPPDATA%\Programs\Strata`。首次启动会下载对应显卡的**引擎**（**0.1.53** 线）。升级时请保留模型文件夹。包内含 `host/hakua-chatbot.enabled`。本预览为**未签名**构建。[安装程序帮助](docs/INSTALL.md#the-app)。

<sub>如有 7z 一并提供。Linux / macOS 也可看上游 Niko1221/Strata。</sub>

<p align="center">
  <img src="docs/media/app-chat.png" width="900" alt="Strata 桌面应用，聊天和实时代码预览并排显示">
  <br><sub>聊天、文件和实时预览都在一个窗口里。</sub>
</p>

<a id="option-b-the-terminal-one-line"></a>

### 终端应用

更喜欢终端？安装 Strata，然后运行 **`strata launch`**。

<details open>
<summary><b>安装命令</b></summary>

**Linux / Mac**

```sh
curl -fsSL https://github.com/Niko1221/Strata/releases/latest/download/install.sh -o install.sh && sh install.sh
```

**Windows PowerShell**

```powershell
irm https://github.com/Niko1221/Strata/releases/latest/download/install.ps1 | iex
```

在 Windows 上，安装后请打开一个新的终端。然后运行：

```sh
strata launch
```

按提示下载并启动模型。[终端指南](docs/TERMINAL_LAUNCH.md)。

</details>

<p align="center">
  <img src="docs/media/terminal-monitor.png" width="900" alt="Strata 终端应用，显示模型活动、速度、内存和最近的请求">
  <br><sub>模型运行时，随时查看模型和硬件状态。</sub>
</p>

<a id="build-from-source"></a>

[从源码构建](docs/SOURCE_INSTALL.md) · [Docker](docs/DOCKER.md) · [完整安装指南](docs/INSTALL.md)

<a id="what-you-need"></a>

## 硬件

| 支持的硬件 | 指南 |
| --- | --- |
| **NVIDIA GeForce RTX 20 / 30 / 40 / 50 系列** | [NVIDIA 安装](docs/INSTALL.md#what-you-need) |
| **AMD Radeon RX 7700 / 7800 / 7900、RX 9060 / 9070、AI PRO R9700** | [AMD 安装](docs/AMD_HIP.md) |
| **AMD Radeon RX 6800 / 6900 · 实验性** | [RX 6000 安装](docs/AMD_HIP.md#rdna2-gfx1030) |
| **Intel Arc · Linux** | [Intel 安装](docs/INTEL_ARC.md) |
| **Apple Silicon · M1 或更新** | [Mac 安装](docs/MAC.md) |
| **AMD Ryzen AI Max · Strix Halo** | [Strix Halo 安装](docs/STRIX_HALO.md) |

<a id="using-it"></a>

## 工具

**Claude Code · Codex CLI · OpenCode · oh-my-pi · pi.dev · Hermes Agent · OpenClaw**，也可以通过兼容 OpenAI 和 Anthropic 的 API 使用更多工具。

运行 **`strata connect`**，查看你所用工具的设置方法。[连接指南](docs/TERMINAL_LAUNCH.md#connect-your-apps-strata-connect)。

<a id="guides"></a>
<a id="how-fast-is-it"></a>
<a id="how-does-it-work"></a>
<a id="something-went-wrong"></a>

## 帮助

[全部指南](docs) · [故障排查](docs/TROUBLESHOOTING.md) · [向本分支报告问题](https://github.com/zapabob/Strata/issues/new/choose) ·
[基准测试](docs/COMMUNITY_BENCHMARKS.md) · [工作原理](docs/HOW_IT_WORKS.md) · [参与贡献](CONTRIBUTING.md)

## 支持 Strata

**帮助本地 AI 保持开放。** 一杯咖啡能帮助我们在更多硬件上开发和测试。

<a href="https://buymeacoffee.com/strataengine"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee：支持 Strata" height="48"></a>

[MIT 许可证](LICENSE) · [致谢和模型许可证](docs/HOW_IT_WORKS.md#credits) · [隐私](docs/SAFETY.md)

<a id="option-c-let-your-ai-set-it-up"></a>

<sub>面向 AI 工具和自动阅读器： <a href="AGENTS.md">技术参考</a> · <a href="docs/AI_SETUP.md">安装说明</a></sub>

**赞助、硬件合作或其他合作：** [niko.veit@outlook.com](mailto:niko.veit@outlook.com).

<a id="分支说明"></a>
<a id="fork-notes"></a>

## 分支说明

| 项目 | 值 |
| --- | --- |
| 仓库 | [zapabob/Strata](https://github.com/zapabob/Strata) |
| 跟踪上游 | [Niko1221/Strata](https://github.com/Niko1221/Strata) **v0.2.7.1**（`46c152a1`） |
| 产品版 | `0.3.2-preview.20261029.2` |
| 引擎版 | `0.1.53`（Metal `0.1.52-metal`） |
| 落地页 | https://zapabob.github.io/Strata/ |
| Windows 安装包（计划标签） | [v0.3.2-preview.20261029.2](https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261029.2) → `Strata_0.3.2-preview.20261029.2_x64-setup.exe`（未签名 NSIS） |
| 上游同步标签 | [v0.3.2-preview.20261028.1](https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261028.1) |
| 记忆 pip pin | `hakua-memory==0.3.5`（`requirements.txt`；可选 `[obsidian,rag]`） |

**刻意保留：** Hakua 同意式记忆聊天、同梱标记 `host/hakua-chatbot.enabled`、`hakua_harness` / run-config 密钥、加载取消所有权（`stopCancelledLoad`）、F01–F11（Spin8 / Query-v3 / TurboQuant 等）、Hermes、`-hakua` 打包。产品 SemVer 由根目录 `VERSION` 与 `tools/bump_hakua_product_version.py` 统一。

### Hakua 记忆栈（本分支）

面向 Hakua / Hermes 操作者的同意式长期记忆。读写保持 opt-in（`strata_memory` + principal 密钥）。仓库内不含密钥。

| 部件 | 作用 |
| --- | --- |
| Hermes `SOUL.md` / `MEMORY.md` | 同步到 Hakua 配置目录（`~/.hakua-memory/profiles/hermes/`），供 `hakua_harness` 的 `persona_sha256` 审批（普通拷贝，无符号链接）。 |
| Ebbinghaus | 遗忘曲线与 sleep 强化（`hakua_memory.ebbinghaus`）。 |
| RAG + 语义图 | `rag.db` / `semantic.db`（`CompositeMemory`）。 |
| Obsidian | 导出/导入到 `OBSIDIAN_VAULT_PATH`（或当前打开库）下的 `Hakua/`。 |
| Sleep / consolidate | `py -3 tools/hakua_hermes_memory_stack.py sleep`（或 `strata_memory_mcp.py --cli sleep`）。 |
| 侧栏启用 | 包内 `host/hakua-chatbot.enabled` 使安装后仍可使用 **Hakua**。 |
| Python 包 | `pip install hakua-memory==0.3.5`（可选 extras：`pip install "hakua-memory[obsidian,rag]==0.3.5"`）。 |

模板：`serve/examples/hakua_hermes_harness.example.json`。CLI：`tools/hakua_hermes_memory_stack.py`。MCP/Host：`tools/strata_memory_mcp.py`。详情：`_docs/2026-10-29_hakua-hermes-soul-memory-wire{Cursor}.md`。

**此处不声称：** `docs/` 与 `_docs/` 之外的新速度或质量数字。完整 131k 认证仍开放。签名更新 feed 需要 release 机器上的密钥。`hakua_harness` 的多用户 native cache 切换仍为原型级。
