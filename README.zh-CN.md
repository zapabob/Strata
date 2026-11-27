# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata 是 [Niko1221/Strata](https://github.com/Niko1221/Strata) 面向 Windows 的分支，可使用本地模型聊天、编写代码和执行智能体任务。对于兼容的混合专家模型，原生引擎可将专家权重分配到显存、系统内存和 SSD。

## 开始使用

从 [Hakua 发布页](https://github.com/zapabob/Strata/releases)下载按用户安装的 Windows 安装程序。CUDA 引擎单独分发。在应用的「模型」页选择与已安装权重对应的型号。Inkling 2 Mini SC117 提供独立的 SQ-10、SQ-15 和 SQ-20 配置。请按可用内存选择上下文长度。[Windows 安装指南](docs/HAKUA_INSTALL.md)与[模型文档](docs/MODELS.md)列出了适用条件。

## 复用智能体工作流程

在「设置 → 工具」启用按需查找技能，智能体便可以搜索并打开需要的技能，完整目录不会发送给模型。「技能」页可以分别开启从已完成任务学习和自动应用。保存的流程是可编辑的 `SKILL.md`。自动应用检查名称、触发短语和工作区。技能、辅助智能体、文件操作和 `/goal` 有各自的开关。[工作流程指南](docs/WORKFLOW_SKILLS.md)

## 实机测量与限制

在 RTX 5060 Ti 16 GB 上，SC117 SQ-10 通过 Strata 的 `/goal` 写出了单文件 Pagoda Bench 场景，并根据诊断自行修复渲染器。Chrome 缩小后显示五层屋顶。场景报告 7,079 个体素。初始视图裁掉了顶部，尚未测量官方得分。[0.8.5 引擎测试](_docs/2026-11-27_v085-release-notes.md)是在所列上下文容量下使用短输入进行的。

组件兼容性、安装程序签名和验证范围见[发布记录](docs/HAKUA_RELEASE.md)。Hakua 采用 [MIT 许可证](LICENSE)。模型和随附组件适用各自的条款。
