# Strata · Hakua

<!-- stable-059 -->
## 正式版 0.5.9

在Windows本地模型加载和生成期间监控可用内存。研究阶段只允许搜索和读取网页，最终回答不使用工具。库存CSV审核使用确定性计算结果；已通过的检查不需要额外证据。

[Windows NSIS](https://github.com/zapabob/Strata/releases/download/v0.5.9/Strata-0.5.9-windows-x64-setup.exe) · [tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.9/Strata-0.5.9-windows-x64.tar.7z) · [SHA256SUMS](https://github.com/zapabob/Strata/releases/download/v0.5.9/SHA256SUMS.txt) · [Verification](_docs/2026-11-13_stable-059-workflow-safety_Codex.md)

应用、Terminal、Control 和原生引擎均为 0.5.9；RustXNG 保持 0.31.1 Full。正式发布、全部 8 项必需 CI 工作流、真实模型工作流、覆盖安装和所有公开下载的校验均记录在上方链接中。通用回答质量、完整上下文推理和 GPU 并发尚未认证（releaseQualified=false）。下方保留旧版记录及对上游项目的致谢。


<!-- stable-058 -->
## 历史正式版 0.5.8

修复长对话、摘要和搜索次数限制的扩展测试。代理子进程接收所选环境，每个测试使用独立配置目录。CI 同时验证翻译完整性、各平台测试以及应用、Control 和引擎的独立版本。

[Windows NSIS](https://github.com/zapabob/Strata/releases/download/v0.5.8/Strata-0.5.8-windows-x64-setup.exe) · [tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.8/Strata-0.5.8-windows-x64.tar.7z) · [SHA256SUMS](https://github.com/zapabob/Strata/releases/download/v0.5.8/SHA256SUMS.txt) · [0.5.8 verification](_docs/2026-11-11_stable-058-context-ci_Codex.md)

RustXNG 0.31.1 Full / app, Terminal, native engine and Control 0.5.8. Native model quality remains unqualified (`releaseQualified=false`). Previous releases and their measurements follow below.


<!-- skills-057 -->
## 正式版 0.5.7

`/btw` 现在将问题交给真正的子代理。独立父会话启动无工具子代理，主对话和停止操作保持分离。技能页面可分别启用从已完成工作学习 SKILL.md，以及在执行流程中自动应用匹配技能。手动编辑、工作区范围和审批设置受到尊重。

[安装程序](https://github.com/zapabob/Strata/releases/download/v0.5.7/Strata-0.5.7-windows-x64-setup.exe) · [tar.7z 完整包](https://github.com/zapabob/Strata/releases/download/v0.5.7/Strata-0.5.7-windows-x64.tar.7z) · [安装与操作](docs/WORKFLOW_SKILLS.md)

RustXNG 0.31.1 Full / native 0.5.5 / Control 0.5.6. [0.5.7 delivery status](_docs/2026-11-11_stable-057-release_Codex.md). Stable / GitHub Latest: 0.5.7.


## 上一预览版 0.5.6-local.1

使用 `/btw <问题>` 可在主对话继续运行时打开独立回答；使用 `/deepresearch <主题>` 可结合多次搜索和页面阅读开展调查，并明确说明证据不足的情况。在设置 → 工具 → 网页搜索中选择 **RustXNG Full**，无需密钥。

[Windows 安装程序](https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/Strata-0.5.6-local.1-windows-x64-setup.exe) · [tar.7z 完整包](https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/Strata-0.5.6-local.1-windows-x64.tar.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/SHA256SUMS.txt)。

原生引擎 0.5.5 和 Control 0.5.6 保持不变。已验证覆盖安装、WebView2 界面和真实 RustXNG 搜索；界面测试中的模型回答来自隔离的测试 API，不能证明真实模型质量或 GPU 并发性能。EXE 没有 Windows 代码签名，稳定版仍为 0.5.1。[当前验证记录](_docs/2026-11-11_btw-deepresearch-rustxng_Codex.md)。下方 0.5.5 和 0.5.1 的安装包与测量数据均属于先前版本。

[快速安装](INSTALL.md) · [网页搜索与浏览器操作](docs/BROWSER_SEARCH.md)

## 0.5.5-local.1 预览版 — 集成官方0.2.13

[Windows安装程序](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64-setup.exe) ·
[tar.7z完整包](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64.tar.7z) ·
[校验值和发布页](https://github.com/zapabob/Strata/releases/tag/v0.5.5-local.1)。
面向Windows x64／CUDA sm_120，在RTX 5060 Ti16 GB／RAM32 GB上验证。
CUDA资源检查以0项违规通过，实际安装的聊天、代理、重启和文件夹批量删除均通过。
更广泛的质量仍未认证：**releaseQualified=false**。旧054的Prism超时及原因未确定的记录保留。
请在准备界面导入本预览版的签名引擎tar.gz，保持压缩状态。
[当前安装说明](docs/HAKUA_INSTALL.md) · [验证范围](docs/HAKUA_RELEASE.md)。

## 稳定版0.5.1 — 旧版说明与测量

以下版本、下载和测量属于0.5.1。GitHub Latest和默认stable源仍选择该稳定版。

0.5.1改为手动加载模型，并修复原生Qwen3.6的启动流程。现有模型和已验证的专家包均予以保留。

在本机运行模型、聊天和工具，并可选用 Hakua 记忆。这是 [zapabob](https://github.com/zapabob/Strata) 维护的 [Niko1221/Strata](https://github.com/Niko1221/Strata) 分支。

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Windows 版本

原生Qwen3.6在4096单元容量配置下用41.250秒达到READY，并通过六项简短的私有缓存测试。尚未验证完整的98K／131K输入及FP16／NVFP4的实际模型质量。请阅读[测试结果与限制](docs/HAKUA_RELEASE.md)。

此版本面向 Windows x64 CUDA sm_120，已在 RTX 5060 Ti（16 GB 显存）和 32 GB 内存的电脑上进行本地检查。安装前请阅读[验证结果与剩余限制](docs/HAKUA_RELEASE.md)。

产品版本为 **0.5.1**，需要手动更新，没有 Windows 代码签名。[发布页面](https://github.com/zapabob/Strata/releases/tag/v0.5.1) · [安装说明](docs/HAKUA_INSTALL.md) · [验证结果与限制](docs/HAKUA_RELEASE.md)。

1. 下载[安装程序](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64-setup.exe)，并与 [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.1/SHA256SUMS.txt) 核对校验值。
2. 退出 Strata，包括托盘程序，然后运行安装程序。模型和个人数据应保存在应用目录之外。
3. 在准备页面通过 latest 更新源或包内的 `strata-engine-0.5.1-windows-x86_64-cuda-cuda13.tar.gz` 安装已签名的 CUDA 组件。
4. 选择适合本机的模型，或通过 **Use a local GGUF** 使用已有文件。安装包自带 Node 和 Python，不需要系统解释器或编译器。

版本遵循 [SemVer 2.0.0](https://semver.org/)：应用为 `0.5.1`，原生引擎为 `0.5.1`，Control 为 `0.5.1`；未变更的 PrismML／TurboQuant 运行时保留 `0.4.0`。应用通常安装在 C 盘的 `%LOCALAPPDATA%\Programs\Strata`，与模型目录分开。已有安装可能沿用其他位置。

[tar.7z 整合包](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64.tar.7z)包含相同的 NSIS 安装程序、已签名的 CUDA 组件、Control、校验值和安装说明，不包含模型权重或个人数据。发布使用 `v0.5.1`、指向同一提交的 `latest` 标签和 GitHub Latest。

## 使用已有模型文件

对于分片 GGUF，只需选择其中一片，Strata 会检查完整文件组。导入的权重仍保留在原位置。元数据中的 `Hf` 等通用名称会以文件名显示；用户自定义的名称会在重新检查和重启后保留。

其他模型列表仍在加载时，也可以打开已注册本地模型的设置。

准备目录中的模型之前，Strata 会在所选模型文件夹及其子文件夹中进行有界搜索。发现唯一有效的匹配文件组时直接复用；存在多个匹配时要求明确选文件。常规下载仍保留完整性校验和断点续传。引擎和可选的草稿模型层单独处理，不等同于重新下载主模型。

原生 Qwen/Swift 模型可能需要一次 pack 转换。转换器提供进度时，界面显示已完成的层数。恢复低内存转换时，空间检查会计入临时文件已经实际占用的磁盘空间。支持的 Hikari/PQ2_0 GGUF 通过 **Load with Strata** 使用 PrismML，无需原生 Q2_0 转换。普通兼容 GGUF 可选择 TurboQuant 的 K=`FP16`、V=`TURBO2/3/4`，然后重新加载。参见[本地后端](docs/LOCAL_LLAMA_BACKENDS.md)。

## 私有会话缓存与记忆

新的 Qwen3.6 路径会在同一个已认证会话内保留缓存，供后续请求复用。其他会话或其他用户不能继承该缓存。切换会话、取消、发生错误或空闲五分钟后，会清除私有缓存。没有会话标识的请求不复用缓存。

已删除 Host 中两处启动前的拒绝分支。服务器通过运行中引擎的 INFO 响应确认私有缓存能力，也支持兼容的本地构建。初期仅支持一次处理一个请求，共享提示词缓存和共享会话缓存继续关闭。mapped expert pack 仍为可选设置。实测结果和未完成的检查见[发布记录](docs/HAKUA_RELEASE.md)。

加载支持的模型后，可从侧边栏打开 **Hakua memory**。每轮分别选择是否允许读取和保存记忆。PrismML/TurboQuant 会为此重启其所属服务器，启用认证和私有缓存；请先结束正在运行的请求。参见[记忆说明](serve/MEMORY_HARNESS.md)。

## 组件与限制

桌面应用/Host：`0.5.1`；原生引擎：`0.5.1`；Control：`0.5.1`；Node：`24.22.2`；CPython：`3.12.15`；Hakua-memory：`0.3.5`。上游源码参考：`5d37280d` / `0.2.11`。

0.5.1 合并官方 0.2.11 及截至 `5d37280d` 的修复，包括按会话保存文件、重新连接正在生成的回复、IME 输入与渲染恢复、新模型列表、流隔离和 Pillow 13。保留 Hakua 记忆、现有 GGUF 复用和 Qwen3.6 私有缓存。新的 CUDA 构建需要单独验证，0.4.1 的历史测量不能证明新默认设置的表现。原生完整上下文生成仍未验证。请参阅[验证与发布状态](docs/HAKUA_RELEASE.md)。

Windows x64 检查基于 RTX 5060 Ti、CUDA sm_120 和 32 GB 内存，不代表其他 GPU、操作系统、原生图像输入或独立原生 DeepSeek 引擎已经通过验证。Qwen3.6 的旧式主机内存分配可能需要约 18.7 GiB 加预留空间，32 GB 总内存并不保证能够启动。设置 131,072 token 上下文后成功生成短回复，不等于完整窗口生成或质量验证。TurboQuant 的 K 模式在实模型质量测试失败后仍保持禁用。Spin(8)、Triality、Query-v3 和 Bonsai 均为可选实验。速度和资源需求取决于模型与计算机。

## 在 16 GB GPU 上使用 96K–128K

界面提供 96K（98,304）和 128K（131,072）。在 RTX 5060 Ti 16 GB、32 GB 内存的实机上，Qwen3.6 UD-Q4_K_XL 使用 PrismML、Q8 K/V 和 28 层 CPU MoE，完整处理了 130,792 个输入 token，并找回了三处相隔较远的代码。这次请求约耗时 29 分钟，不能据此保证其他模型的质量或速度。参见[设置和完整上下文测试结果](docs/WINDOWS_16GB_CONTEXT.md)。

## 开发

[模型参考](docs/AI_REFERENCE.md) · [构建](packaging/README.md) · [贡献](CONTRIBUTING.md) · [安全](SECURITY.md)

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

Strata 使用 MIT 许可证。模型权重、Hakua-memory 和依赖保留各自的许可证与声明。可选的小型控制向量默认关闭，适用 [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE)。

## 官方 Strata 项目的支持者

感谢每一位支持 Strata 的人。

<!-- supporters:start (one line per public supporter, newest last; copy a line and change the GitHub name in all four places) -->
<a href="https://github.com/ryan4yin"><img src="https://github.com/ryan4yin.png?size=96" width="48" height="48" alt="ryan4yin" title="ryan4yin"></a>
<a href="https://github.com/themactep"><img src="https://github.com/themactep.png?size=96" width="48" height="48" alt="themactep" title="themactep"></a>
<a href="https://github.com/macintog"><img src="https://github.com/macintog.png?size=96" width="48" height="48" alt="macintog" title="macintog"></a>
<a href="https://github.com/bisonbet"><img src="https://github.com/bisonbet.png?size=96" width="48" height="48" alt="bisonbet" title="bisonbet"></a>
<a href="https://github.com/vizv"><img src="https://github.com/vizv.png?size=96" width="48" height="48" alt="vizv" title="vizv"></a>
<a href="https://github.com/kod88vn"><img src="https://github.com/kod88vn.png?size=96" width="48" height="48" alt="kod88vn" title="kod88vn"></a>
<a href="https://github.com/seoulworker"><img src="https://github.com/seoulworker.png?size=96" width="48" height="48" alt="seoulworker" title="seoulworker"></a>
<a href="https://github.com/jackyini"><img src="https://github.com/jackyini.png?size=96" width="48" height="48" alt="jackyini" title="jackyini"></a>
<a href="https://github.com/router0mail"><img src="https://github.com/router0mail.png?size=96" width="48" height="48" alt="router0mail" title="router0mail"></a>
<!-- supporters:end -->

## 致谢

感谢 [Strata](https://github.com/Niko1221/Strata) 开发者对本地推理和易用桌面体验的细致打磨。本分支建立在这些扎实的工作之上。

向 [llama.cpp](https://github.com/ggml-org/llama.cpp) 及其贡献者致敬，感谢他们让更多开发者和用户能够使用 C/C++ 模型推理；也感谢 [RustXNG](https://github.com/sahenjp/RustXNG) 为本地 AI 提供实用、开放的搜索与资料获取服务。这些项目的工程实践和持续维护值得赞赏。

本分支独立维护其集成与修改；上述致谢不表示相关项目对本分支的认可或背书。
