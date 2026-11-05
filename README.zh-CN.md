# Strata · Hakua

在本机运行模型、聊天和工具，并可选用 Hakua 记忆。这是 [zapabob](https://github.com/zapabob/Strata) 维护的 [Niko1221/Strata](https://github.com/Niko1221/Strata) 分支。

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Windows 预览版

产品版本为 **0.4.1-beta.1**，需要手动更新，没有 Windows 代码签名。[发布页面](https://github.com/zapabob/Strata/releases/tag/v0.4.1-beta.1) · [安装说明](docs/HAKUA_INSTALL.md) · [验证结果与限制](docs/HAKUA_RELEASE.md)。

1. 下载[安装程序](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/Strata_0.4.1-beta.1_x64-setup.exe)，并与 [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/SHA256SUMS.txt) 核对校验值。
2. 退出 Strata，包括托盘程序，然后运行安装程序。模型和个人数据应保存在应用目录之外。
3. 从此测试版的发布页面下载 `strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz`，然后在准备页面导入。latest 更新源仍保留旧引擎。
4. 选择适合本机的模型，或通过 **Use a local GGUF** 使用已有文件。安装包自带 Node 和 Python，不需要系统解释器或编译器。

版本遵循 [SemVer 2.0.0](https://semver.org/)：应用为 `0.4.1-beta.1`，原生引擎／Control 为 `0.4.1`；未变更的 PrismML／TurboQuant 运行时保留 `0.4.0`。应用通常安装在 C 盘的 `%LOCALAPPDATA%\Programs\Strata`，与模型目录分开。已有安装可能沿用其他位置。

## 使用已有模型文件

对于分片 GGUF，只需选择其中一片，Strata 会检查完整文件组。导入的权重仍保留在原位置。元数据中的 `Hf` 等通用名称会以文件名显示；用户自定义的名称会在重新检查和重启后保留。

准备目录中的模型之前，Strata 会在所选模型文件夹及其子文件夹中进行有界搜索。发现唯一有效的匹配文件组时直接复用；存在多个匹配时要求明确选文件。常规下载仍保留完整性校验和断点续传。引擎和可选的草稿模型层单独处理，不等同于重新下载主模型。

原生 Qwen/Swift 模型可能需要一次 pack 转换。转换器提供进度时，界面显示已完成的层数。恢复低内存转换时，空间检查会计入临时文件已经实际占用的磁盘空间。支持的 Hikari/PQ2_0 GGUF 通过 **Load with Strata** 使用 PrismML，无需原生 Q2_0 转换。普通兼容 GGUF 可选择 TurboQuant 的 K=`FP16`、V=`TURBO2/3/4`，然后重新加载。参见[本地后端](docs/LOCAL_LLAMA_BACKENDS.md)。

## 私有会话缓存与记忆

新的 Qwen3.6 路径会在同一个已认证会话内保留缓存，供后续请求复用。其他会话或其他用户不能继承该缓存。切换会话、取消、发生错误或空闲五分钟后，会清除私有缓存。没有会话标识的请求不复用缓存。

此路径要求匹配且经过验证的引擎文件，并要求引擎在启动时确认支持该能力。旧引擎仍被拒绝。初期仅支持一次处理一个请求，共享提示词缓存和共享会话缓存继续关闭。mapped expert pack 仍为可选设置。实测结果和未完成的检查见[发布记录](docs/HAKUA_RELEASE.md)。

加载支持的模型后，可从侧边栏打开 **Hakua memory**。每轮分别选择是否允许读取和保存记忆。PrismML/TurboQuant 会为此重启其所属服务器，启用认证和私有缓存；请先结束正在运行的请求。参见[记忆说明](serve/MEMORY_HARNESS.md)。

## 组件与限制

桌面应用/Host：`0.4.1-beta.1`；原生引擎/Control：`0.4.0`；Node：`24.22.2`；CPython：`3.12.15`；Hakua-memory：`0.3.5`。上游源码参考：`ffa80d73` / `0.2.10`。

已签名的 CUDA/PrismML/TurboQuant 组件仍来自 [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1)。独立的实验性 Qwen3.6 组件未签名。应用安装包不包含 CUDA 引擎，应用的签名自动更新尚未完成验证。

Windows x64 检查基于 RTX 5060 Ti、CUDA sm_120 和 32 GB 内存，不代表其他 GPU、操作系统、原生图像输入或独立原生 DeepSeek 引擎已经通过验证。Qwen3.6 的旧式主机内存分配可能需要约 18.7 GiB 加预留空间，32 GB 总内存并不保证能够启动。设置 131,072 token 上下文后成功生成短回复，不等于完整窗口生成或质量验证。TurboQuant 的 K 模式在实模型质量测试失败后仍保持禁用。Spin(8)、Triality、Query-v3 和 Bonsai 均为可选实验。速度和资源需求取决于模型与计算机。

## 开发

[模型参考](docs/AI_REFERENCE.md) · [构建](packaging/README.md) · [贡献](CONTRIBUTING.md) · [安全](SECURITY.md)

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

Strata 使用 MIT 许可证。模型权重、Hakua-memory 和依赖保留各自的许可证与声明。可选的小型控制向量默认关闭，适用 [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE)。
