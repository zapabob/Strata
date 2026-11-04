# Hakua / Strata

基于 Strata 的 Hakua 聊天机器人。本分支提供带 Hakua memory、GPU 运行时单独分发的 Windows 预览包。[zapabob/Strata](https://github.com/zapabob/Strata) · 上游 [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## 安装（Windows 预览）

1. 下载 [setup EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.6/Strata_0.4.0-preview.20261103.6_x64-setup.exe)。
2. 运行前与 [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.6/SHA256SUMS.txt) 核对。安装程序无 Windows 代码签名。setup EXE 的 SHA-256 为 `784d4f992443a43076e7de8dbcdc624b35d95e97e13b716ea9de0e13a1baeac9`（113,075,186 bytes）。
3. 若已安装，请从托盘选择退出 Strata 后再运行 EXE。
4. 安装程序只更新应用，不含 CUDA 引擎。本标签的 Qwen3.6 包另行发布，没有图像读取器，且未做 Ed25519 签名（`signature` 为 null）。PrismML 与 TurboQuant 仍在 [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1) 的已签名组件中（digest `b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1`，未改动）。本发布不替换这些文件。

点击步骤很短；下载、激活引擎与加载模型更久，并需要磁盘与显存。详见 [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md)。实测范围见 [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md)。

## 安装包内容

| 应用安装程序 | 单独分发 |
| --- | --- |
| GUI / Host、专用 Node 24.22.2、Control / CPython 3.12.15、Hakua-memory 0.3.5、Harness | CUDA 引擎另行提供。本标签 Qwen3.6 包未签名。PrismML/TurboQuant 仍在 `v0.4.0-preview.20261101.1` 已签名组件中（`b5e4d525…`） |
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
| GUI / Product | `0.4.0-preview.20261103.6` |
| Engine / Control | `0.4.0`（CUDA sm_120） |
| Hakua-memory | `0.3.5` |
| 上游冻结 | `ffa80d73` · 0.2.10 |

App version in this preview tree: `0.4.0-preview.20261103.7`

发布页：[v0.4.0-preview.20261103.6](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.6)。本标签的安装程序和 Qwen3.6 引擎包没有签名。`v0.4.0-preview.20261101.1` 的 Ed25519 更新源和已签名引擎没有被替换。应用本体的签名自动更新尚未验证，请用本安装程序更新。安装程序只更新应用，不含 CUDA 引擎。本标签的 Qwen3.6 包另行发布，没有图像读取器，`signature` 为 null。PrismML 与 TurboQuant 仍在已签名组件中（digest `b5e4d525…`，未改动）。主线仍是 Qwen3.6-35B-A3B UD-Q4_K_XL、context 65536、FP32 KV、MTP 2、prefill auto。新路径为 opt-in。引擎不应用的设置会在启动前拒绝。private-cache 请求也会拒绝，不会为了启动而删掉。mapped expert pack 仅在启动明确要求且引擎 SHA-256 为 `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`, `6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29`、`dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5`、或 `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046` 时启用。旧摘要仍然允许。默认仍是原来的 host arena。T04 采用状态为 NOT_DECIDED。成对速度检查 T06/T07/T08 未运行。本次构建的启动时间和 token 速度未测量。CUDA spill guard 未通过已登记的 baseline。32GB 内存的电脑可能在空闲物理内存放不下 legacy 18.75 GiB expert arena 加 reserve 时，于启动前拒绝 UD-Q4_K_XL。这不是“已装进 16GB VRAM”的测量。

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
