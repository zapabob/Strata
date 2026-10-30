# Hakua / Strata

基于 Strata 的 Hakua 聊天机器人. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · 30 秒了解安装

下载本分支的 Windows 安装程序，运行后选择并加载兼容模型。通过侧栏 Hakua memory 打开记忆聊天。操作步骤约需 30 秒；下载、安装及加载模型的等待时间另计。

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Strata_0.3.3-preview.20261030.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/SHA256SUMS.txt)

7z 中包含相同的安装程序。请先解压，再运行安装 EXE。

## 本分支的独有功能

Hakua 只有获得本次请求的同意后才读取记忆或保存对话摘要。两项权限相互独立，每次请求后重置。加载受支持的原生模型后，桌面应用会自动创建本地记忆配置。打开 Hakua memory，复制对话框中的专用密钥，在本地页面勾选记忆选项，然后将密钥粘贴到 About → Settings。源码服务器的配置方法也见[记忆指南](serve/MEMORY_HARNESS.md)。

Hermes 工具支持同步已批准的 SOUL.md / MEMORY.md、Ebbinghaus 记忆、语义图、Obsidian 导出及 sleep 整理。这些管理工具独立于聊天页面；基础安装包不含可选 RAG 和嵌入依赖。

使用本地 PQ2_0 GGUF 时，在模型高级设置的 llama-server 后端中选择 `PrismML`。使用普通 GGUF 的 TurboQuant 缓存时，选择 `TurboQuant`，将 K 缓存设为 `FP16`，V 设为 `TURBO2`、`TURBO3` 或 `TURBO4`。本版本禁用 TurboQuant K 格式，因为实测出现回复损坏。更换后端后请重新加载模型。各后端使用独立的内置程序和库；PQ2_0 与 TurboQuant 是两条独立路径。请查看[配置与限制](docs/LOCAL_LLAMA_BACKENDS.md)。

Spin(8)/Triality、Query-v3 与 Bonsai 实验功能需要明确选择兼容配置。不承诺在所有环境下提高速度或质量。

自带专用 Node、Python、固定版本 Hakua-memory 0.3.5 和本分支构建的 CUDA 引擎。启动模型时不安装 Python 包或编译代码。

## 兼容性与更新

此 Windows 包面向 NVIDIA RTX 50 系列，CUDA sm_120。其他显卡、Linux 和 macOS 需要各自兼容的包。上游安装程序不包含本分支修改。模型权重单独下载，可能需要数十至数百 GB。优先选择兼容且能容纳的 ISTA-DASLab，其次 Unsloth，再次 Gyro。

模型与个人记忆保存在应用目录之外。安装包不含个人记忆、密钥或模型权重。更新前关闭应用；回退时保留数据备份并安装较早的本分支版本。

[Models](docs/MODELS.md) · [Install](docs/HAKUA_INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## 版本与验证

| | |
| --- | --- |
| GUI / Product | `0.3.3-preview.20261030.1` |
| Engine | `0.3.3` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `870aedd9` · 0.2.8 |

<!-- App version in this preview tree: `0.3.3-preview.20261030.1` -->

此预览未签名，安装前请核对 SHA256SUMS.txt。[发布验证记录](docs/HAKUA_RELEASE.md)列出实际测试结果和限制，构建成功不等于推理正常。 此未签名预览版请通过安装程序手动更新；签名自动更新尚未验证。

## 开发与支持

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

本项目是 MIT 许可的 Strata 分支。Hakua-memory 和模型权重各有许可，并保留原作者与上游的署名。

上游可选的约 480KB 控制向量默认关闭，随附 [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE) 原文。完整推理模型权重需另行下载。
