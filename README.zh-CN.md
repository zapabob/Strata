# Hakua / Strata

基于 Strata 的 Hakua 聊天机器人。本分支提供带 Hakua memory、GPU 运行时单独分发的 Windows 预览包。[zapabob/Strata](https://github.com/zapabob/Strata) · 上游 [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## 安装（Windows 预览）

1. 下载 [setup EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe)（或含相同 EXE 的 [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z)）。
2. 运行前与 [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt) 核对。安装程序无 Windows 代码签名。该标签的摘要已于 2026-11-02 更新，请勿使用旧 SUMS。
3. 若已安装，请从托盘选择退出 Strata 后再运行 EXE。
4. 首次启动时，在准备界面安装签名引擎，或导入同版本的 `.tar.gz`，然后选择模型目录并加载。

点击步骤很短；下载、激活引擎与加载模型更久，并需要磁盘与显存。详见 [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md)。实测范围见 [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md)。

## 安装包内容

| 应用安装程序 | 单独分发 |
| --- | --- |
| GUI / Host、专用 Node 24.22.2、Control / CPython 3.12.15、Hakua-memory 0.3.5、Harness | 签名 CUDA 引擎（约 1.4 GB）：原生 Strata + PrismML + TurboQuant |
| 通过本 EXE 手动更新应用 | 模型权重（数十至数百 GB） |

运行发布版无需系统 Node / Python / pip / 编译器。上游 Niko1221 安装程序不含本分支改动。

## 加载本地模型

- **原生 Strata 包**（受支持的 Qwen 系文本）：使用应用的原生准备 / 加载。
- **Hikari / PQ2_0 GGUF**：使用 **Load with Strata**（PrismML）。不要对 PQ2_0 使用原生准备。
- **普通 GGUF + TurboQuant 缓存**：后端 `TurboQuant`，K=`FP16`，V=`TURBO2` / `TURBO3` / `TURBO4`，然后重新加载。K 侧 TurboQuant 因实测回复损坏而关闭。

PrismML 与 TurboQuant 是引擎内的独立可执行文件。[LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md)。按显存选择：ISTA-DASLab → Unsloth → Gyro。

当模型经 Strata / supervisor 路径运行时，Agent 可通过该本地实例使用模型支持的工具（例如 web search）。仅原生会话不会走同一路径。

## Hakua memory

加载受支持模型后，打开侧栏 **Hakua memory**。读取与保存同意相互独立，每轮重置。

- 原生：将对话框密钥粘贴到 About → Settings，并在记忆页勾选。
- PrismML / TurboQuant：应用自动使用本地密钥；首次打开前请结束进行中的请求（会以认证、私有缓存重启自有服务器）。

说明：[MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md)。Hermes SOUL/MEMORY 运维工具独立于聊天，基础使用非必需。

## 版本

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine / Control | `0.4.0`（CUDA sm_120） |
| Hakua-memory | `0.3.5` |
| 上游冻结 | `c62d5e3a` · 0.2.9 |

发布页：[v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1)。引擎与更新源带 Ed25519 签名并由应用校验。应用本体的签名自动更新尚未验证，请用本安装程序更新。

## 限制（已测预览）

Windows x64、NVIDIA RTX 50 系 / CUDA sm_120，在 RTX 5060 Ti 上检查。含原生文本；不含原生图像输入与独立 DeepSeek 原生引擎。其他 GPU / OS 需各自的包。模型与个人记忆放在应用目录外。发行包不含个人记忆、密钥或完整权重。

Spin(8) / Triality / Query-v3 / Bonsai 为显式实验功能，不承诺整体速度或质量提升。

## 开发

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Models](docs/MODELS.md) · [Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

MIT 许可的 Strata 分支。Hakua-memory 与模型权重另有许可，保留原作者与上游署名。约 480 KB 控制向量默认关闭，遵循 [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE)。
