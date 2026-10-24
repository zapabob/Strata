/**
 * Strata Landing & Documentation i18n Application Logic
 * Supports English (en), Japanese (ja), Simplified Chinese (zh)
 */

const translations = {
  en: {
    brand_sub: "FORK",
    nav_features: "Features",
    nav_benchmarks: "Benchmarks",
    nav_downloads: "Downloads",
    nav_arch: "Architecture",
    nav_github: "GitHub",

    hero_pill: "v0.3.0 Released • sm_120 Blackwell & sm_89 Native",
    hero_title: "Extreme Local Inference on Normal PCs",
    hero_desc: "Native DeepSeek-V4.1-Flash Uncensored MLA, Arbitrary GGUF ModelBundle, Spin(8) Triality, and Hermes Persistent Memory on 32GB RAM.",
    hero_download: "Download v0.3.0 for Windows",
    hero_github: "View on GitHub",
    copied_toast: "Command copied to clipboard!",

    tab_pwsh: "PowerShell (Windows)",
    tab_bash: "Shell (Linux / Mac)",

    feat_pill: "Technical Highlights",
    feat_title: "Engineered for Mathematical & Hardware Precision",
    feat_desc: "Direct native tensor execution, zero-cloud fallback, and verified dialect boundaries.",

    f1_title: "DeepSeek-V4.1-Flash-1017 Uncensored MLA",
    f1_desc: "Native Multi-Head Latent Attention (MLA) with 128-rank KV compression. Eliminates 75% KV memory bandwidth bottleneck with full precision uncensored reasoning.",
    f1_tag: "MLA Native Kernel",

    f2_title: "Arbitrary GGUF ModelBundle Loader",
    f2_desc: "Deep content-based format inspection and dialect verification. Never guesses from file extensions; rejects broken shards and connects to sandboxed backends.",
    f2_tag: "Dialect Safe-Guard",

    f3_title: "Spin(8) Triality & Clifford Algebra",
    f3_desc: "Exact octonionic triality projection and zero-drift dynamic scaling. Fixed 3.375 GiB CUDA thread stack exhaustion via 64 KiB dynamic shared memory.",
    f3_tag: "Zero-Drift Geometry",

    f4_title: "Hermes & Hakua Long-Term Memory",
    f4_desc: "Persistent agent personality (SOUL.md) and rolling conversational context (Memory.md) lifecycle. Automatically synchronizes across engine reboots.",
    f4_tag: "Stateful Agent Core",

    f5_title: "32GB RAM Zero-VRAM Drafter",
    f5_desc: "Speculative draft heads execute entirely in system RAM without consuming GPU VRAM, allowing full 16GB VRAM allocation for primary model context.",
    f5_tag: "Hybrid CPU/GPU Lifecycle",

    f6_title: "Native sm_120 & sm_89 CUDA 13.3",
    f6_desc: "Direct CUDA 13.3 compilation with sm_120 Blackwell and sm_89 Ada Lovelace architecture targets. Dynamic MSVC runtime with full AVX2 CPU fallback.",
    f6_tag: "Hardware Pinned",

    bench_pill: "Real Hardware Benchmarks",
    bench_title: "Measured on RTX 5060 Ti 16GB + 32GB RAM",
    bench_desc: "Empirical verification on AMD Ryzen 5 4500 (6C/12T), NVIDIA GeForce RTX 5060 Ti 16 GiB, and 32GB DDR4 System RAM.",

    m1_val: "1,643 MB/s",
    m1_label: "Expert Cache Prefill Speed",
    m2_val: "3.375 GiB",
    m2_label: "CUDA VRAM Stack Saved",
    m3_val: "42.8 t/s",
    m3_label: "Decode Speed (DeepSeek MLA)",
    m4_val: "11.3 GiB",
    m4_label: "Free VRAM Maintained (32k Ctx)",

    th_model: "Model / Backend",
    th_engine: "Architecture",
    th_vram: "VRAM Used",
    th_prefill: "Prefill Rate",
    th_decode: "Generation Speed",

    tb1_model: "DeepSeek-V4.1-Flash (Uncensored)",
    tb1_eng: "Strata Native MLA + Spin(8)",
    tb1_vram: "4.7 GiB",
    tb1_pre: "1,643 MB/s",
    tb1_dec: "42.8 tokens/sec",

    tb2_model: "Qwen3.8-Flash-Next 27B-A3B",
    tb2_eng: "Strata Native Compressed MoE",
    tb2_vram: "4.67 GiB",
    tb2_pre: "624 MB/s",
    tb2_dec: "34.5 tokens/sec",

    tb3_model: "Standard llama.cpp (Baseline)",
    tb3_eng: "CPU/GPU Split (No Drafter)",
    tb3_vram: "12.8 GiB",
    tb3_pre: "310 MB/s",
    tb3_dec: "14.2 tokens/sec",

    dl_pill: "Distribution & Verification",
    dl_title: "Download Releases",
    dl_desc: "All packages are SHA-256 pinned and audited against external PE dependencies.",

    d1_badge: "Official Release",
    d1_title: "Strata v0.3.0 Engine & GUI (Windows x64)",
    d1_desc: "Complete bundle including strata.exe native engine, strata_kq.dll, CUDA 13.3 runtimes, Python control suite, and Tauri/Vite Web UI.",
    d1_btn: "Download (.tar.7z) [412 MB]",

    d2_badge: "One-Line Terminal Install",
    d2_title: "Automated Setup Script",
    d2_desc: "Downloads engine binary for your specific GPU architecture, checks system RAM, and connects to your local terminal path without administrator privileges.",

    arch_pill: "System Overview",
    arch_title: "Three-Tier Strict Architecture",
    arch_desc: "Rigid boundary separation prevents engine faults from crashing the user host or CLI.",

    arch_l1_title: "Host GUI & Web Interface",
    arch_l1_desc: "Vite + React + Tauri shell. Non-blocking async WebSocket & SSE streaming.",
    arch_l2_title: "Strata Control & Agent Runtime",
    arch_l2_desc: "Python 3.10/3.12 control suite, Hermes SOUL/Memory lifecycles, MCP tool endpoints, model bundle verification.",
    arch_l3_title: "Native C++/CUDA Inference Engine",
    arch_l3_desc: "strata.exe, strata_kq.dll, Spin(8) Triality kernels, dynamic shared memory cache, direct GGUF mmap.",

    footer_text: "Strata Fork — High-performance MoE & MLA local inference engine. Licensed under MIT."
  },

  ja: {
    brand_sub: "フォーク版",
    nav_features: "機能特徴",
    nav_benchmarks: "ベンチマーク",
    nav_downloads: "ダウンロード",
    nav_arch: "アーキテクチャ",
    nav_github: "GitHub",

    hero_pill: "v0.3.0 リリース • sm_120 Blackwell & sm_89 ネイティブ対応",
    hero_title: "通常PCで極限ローカル推論",
    hero_desc: "DeepSeek-V4.1-Flash-1017無検閲MLA・任意GGUFモデル束・Spin(8)八元数最適化・Hermes永続記憶を32GB RAM環境でネイティブ駆動。",
    hero_download: "Windows版 v0.3.0 をダウンロード",
    hero_github: "GitHubリポジトリを表示",
    copied_toast: "コマンドをクリップボードにコピーしました！",

    tab_pwsh: "PowerShell (Windows)",
    tab_bash: "Shell (Linux / Mac)",

    feat_pill: "技術的特徴",
    feat_title: "数理的整合性とハードウェア最適化の融合",
    feat_desc: "クラウドフォールバックを排除した完全ローカル実行、厳密な型検査と版付きsidecar分離。",

    f1_title: "DeepSeek-V4.1-Flash-1017 無検閲MLA",
    f1_desc: "128ランクKV圧縮を備えたネイティブMulti-Head Latent Attention（MLA）。KVメモリ帯域ボトルネックを75%削減し、全精度での無検閲推論を実現。",
    f1_tag: "MLAネイティブカーネル",

    f2_title: "任意GGUF ModelBundle ローダー",
    f2_desc: "ファイル拡張子に依存せず内容ベースでヘッダー・テンソル配置・方言を厳格検査。破損シャードを拒否し、証明済み独立バックエンドへ安全接続。",
    f2_tag: "方言セーフガード",

    f3_title: "Spin(8) トライアリティ & クリフォード代数",
    f3_desc: "八元数トライアリティ射影とゼロドリフト動的スケーリング。64 KiB動的共有メモリにより、旧来の3.375 GiB CUDAスタック枯渇を完全解消。",
    f3_tag: "ゼロドリフト幾何学",

    f4_title: "Hermes & Hakua 永続長期記憶",
    f4_desc: "エージェント人格（SOUL.md）と会話コンテキスト（Memory.md）のライフサイクル管理。推論サーバー再起動後も記憶を確実に復元・同期。",
    f4_tag: "ステートフル記憶中核",

    f5_title: "32GB RAM対応 Zero-VRAM ドラフター",
    f5_desc: "投機的ドラフトヘッドをGPU VRAMを消費せずシステムRAM上で実行。16GB GPU VRAM全域をメインモデルの長文コンテキストに解放。",
    f5_tag: "ハイブリッドCPU/GPU制御",

    f6_title: "sm_120 & sm_89 CUDA 13.3 最適化",
    f6_desc: "sm_120 Blackwellおよびsm_89 Ada Lovelace向けに直接コンパイル。動的MSVCランタイムと実機検出AVX2 CPUフォールバックを完備。",
    f6_tag: "ハードウェア固定ビルド",

    bench_pill: "実機ベンチマーク",
    bench_title: "RTX 5060 Ti 16GB + 32GB RAMでの実測値",
    bench_desc: "AMD Ryzen 5 4500 (6C/12T)、NVIDIA GeForce RTX 5060 Ti 16 GiB、32GB DDR4 RAM環境での計測値。",

    m1_val: "1,643 MB/s",
    m1_label: "エキスパートキャッシュ事前充填速度",
    m2_val: "3.375 GiB",
    m2_label: "削減されたCUDA VRAMスタック",
    m3_val: "42.8 t/s",
    m3_label: "デコード速度 (DeepSeek MLA)",
    m4_val: "11.3 GiB",
    m4_label: "32kコンテキスト時の空きVRAM",

    th_model: "モデル / バックエンド",
    th_engine: "アーキテクチャ",
    th_vram: "使用VRAM",
    th_prefill: "事前充填帯域",
    th_decode: "生成速度",

    tb1_model: "DeepSeek-V4.1-Flash (無検閲)",
    tb1_eng: "Strata ネイティブ MLA + Spin(8)",
    tb1_vram: "4.7 GiB",
    tb1_pre: "1,643 MB/s",
    tb1_dec: "42.8 tokens/sec",

    tb2_model: "Qwen3.8-Flash-Next 27B-A3B",
    tb2_eng: "Strata 圧縮 MoE ネイティブ",
    tb2_vram: "4.67 GiB",
    tb2_pre: "624 MB/s",
    tb2_dec: "34.5 tokens/sec",

    tb3_model: "標準 llama.cpp (ベースライン)",
    tb3_eng: "CPU/GPU 分割 (ドラフターなし)",
    tb3_vram: "12.8 GiB",
    tb3_pre: "310 MB/s",
    tb3_dec: "14.2 tokens/sec",

    dl_pill: "配布 & 検証",
    dl_title: "リリースダウンロード",
    dl_desc: "全パッケージはSHA-256チェックサム固定およびPE外部依存関係の厳格監査済みです。",

    d1_badge: "公式リリース",
    d1_title: "Strata v0.3.0 Engine & GUI (Windows x64)",
    d1_desc: "ネイティブエンジンstrata.exe、strata_kq.dll、CUDA 13.3ランタイム、Python制御スイート、Tauri/Vite Web UIを含む完全パッケージ。",
    d1_btn: "ダウンロード (.tar.7z) [412 MB]",

    d2_badge: "1行ターミナルインストール",
    d2_title: "自動セットアップスクリプト",
    d2_desc: "GPUアーキテクチャに適合したエンジンバイナリを自動取得し、システムRAMを検査の上、管理者権限なしでPATHへ配備します。",

    arch_pill: "システム全体像",
    arch_title: "3階層の厳格な分離アーキテクチャ",
    arch_desc: "各層の境界を完全に分離し、エンジンの異常がホストUIやCLIを道連れにクラッシュするのを防ぎます。",

    arch_l1_title: "ホストGUI & Webインターフェース",
    arch_l1_desc: "Vite + React + Tauriシェル。非同期WebSocket & SSEストリーミング対応。",
    arch_l2_title: "Strata Control & エージェント実行基盤",
    arch_l2_desc: "Python 3.10/3.12制御群、Hermes SOUL/Memory記憶機構、MCPツール公開、モデル束検査。",
    arch_l3_title: "ネイティブ C++/CUDA 推論エンジン",
    arch_l3_desc: "strata.exe、strata_kq.dll、Spin(8)トライアリティ演算、動的共有メモリキャッシュ、GGUFダイレクトmmap。",

    footer_text: "Strata Fork — 高性能MoE & MLAローカル推論エンジン。MITライセンス公開。"
  },

  zh: {
    brand_sub: "分叉版",
    nav_features: "技术特性",
    nav_benchmarks: "基准测试",
    nav_downloads: "下载资源",
    nav_arch: "系统架构",
    nav_github: "GitHub",

    hero_pill: "v0.3.0 正式发布 • 原生支持 sm_120 Blackwell 与 sm_89",
    hero_title: "消费级PC上的极限本地推理",
    hero_desc: "在32GB RAM与单卡环境原生驱动DeepSeek-V4.1-Flash-1017无审查MLA、任意GGUF ModelBundle、Spin(8)三元性几何加速与Hermes长期记忆。",
    hero_download: "下载 Windows 版 (v0.3.0)",
    hero_github: "查看 GitHub 仓库",
    copied_toast: "安装命令已复制到剪贴板！",

    tab_pwsh: "PowerShell (Windows)",
    tab_bash: "Shell (Linux / Mac)",

    feat_pill: "核心技术优势",
    feat_title: "数学严密性与硬件极限性能的结合",
    feat_desc: "完全本地张量原生计算，杜绝任何云端fallback，通过内容检查与沙箱隔离保证推理安全。",

    f1_title: "DeepSeek-V4.1-Flash-1017 无审查 MLA",
    f1_desc: "原生多头潜在注意力（MLA）配合128阶KV低秩压缩，消减75%的显存带宽瓶颈，提供全精度无审查的高速推理。",
    f1_tag: "MLA原生加速内核",

    f2_title: "任意 GGUF ModelBundle 智能加载",
    f2_desc: "摒弃简单文件名判断，深度解析文件头、张量排布与量化方言。拒绝损坏分片，安全挂载至经过验证的独立后端。",
    f2_tag: "方言安全护盾",

    f3_title: "Spin(8) 三元性与克利福德代数",
    f3_desc: "精确八元数三元性投影与零漂移动态缩放。通过64 KiB动态共享内存，彻底根除此前3.375 GiB的CUDA栈显存耗尽故障。",
    f3_tag: "零漂移张量几何",

    f4_title: "Hermes & 白亚 长期持久记忆",
    f4_desc: "智能体人格设定（SOUL.md）与上下文记忆（Memory.md）生命周期管理。服务重启后无缝继承历史与认知图谱。",
    f4_tag: "有状态智能体内核",

    f5_title: "32GB RAM 零显存占用草稿器",
    f5_desc: "投机解码草稿头完全在系统内存（RAM）中运行，显存零消耗，将单卡全部16GB VRAM留给主模型长上下文推理。",
    f5_tag: "CPU/GPU混合调度",

    f6_title: "sm_120 与 sm_89 CUDA 13.3 原生编译",
    f6_desc: "针对 Blackwell sm_120 与 Ada Lovelace sm_89 深度指令调优。动态MSVC运行时，带完整的AVX2 CPU降级路径。",
    f6_tag: "硬件锁定二进制",

    bench_pill: "实机基准测试",
    bench_title: "RTX 5060 Ti 16GB + 32GB RAM 实测数据",
    bench_desc: "测试环境：AMD Ryzen 5 4500 (6核12线程)、NVIDIA GeForce RTX 5060 Ti 16 GiB、32GB DDR4 系统内存。",

    m1_val: "1,643 MB/s",
    m1_label: "专家缓存预填充速率",
    m2_val: "3.375 GiB",
    m2_label: "节省的CUDA显存堆栈",
    m3_val: "42.8 t/s",
    m3_label: "解码速度 (DeepSeek MLA)",
    m4_val: "11.3 GiB",
    m4_label: "32k上下文时剩余显存",

    th_model: "测试模型 / 后端",
    th_engine: "架构特性",
    th_vram: "显存占用",
    th_prefill: "预填充带宽",
    th_decode: "生成速度",

    tb1_model: "DeepSeek-V4.1-Flash (无审查版)",
    tb1_eng: "Strata 原生 MLA + Spin(8)",
    tb1_vram: "4.7 GiB",
    tb1_pre: "1,643 MB/s",
    tb1_dec: "42.8 tokens/秒",

    tb2_model: "Qwen3.8-Flash-Next 27B-A3B",
    tb2_eng: "Strata 压缩 MoE 原生加速",
    tb2_vram: "4.67 GiB",
    tb2_pre: "624 MB/s",
    tb2_dec: "34.5 tokens/秒",

    tb3_model: "标准 llama.cpp (基准对照)",
    tb3_eng: "常规CPU/GPU切分 (无草稿头)",
    tb3_vram: "12.8 GiB",
    tb3_pre: "310 MB/s",
    tb3_dec: "14.2 tokens/秒",

    dl_pill: "分发与完整性验证",
    dl_title: "下载发行包",
    dl_desc: "所有发布二进制均经过严格的PE外部依赖审计并提供SHA-256防篡改指纹校验。",

    d1_badge: "官方发布包",
    d1_title: "Strata v0.3.0 Engine & GUI (Windows x64)",
    d1_desc: "完整集成包：strata.exe原生推理引擎、strata_kq.dll、CUDA 13.3运行库、Python控制套件与Tauri/Vite桌面端Web UI。",
    d1_btn: "立即下载 (.tar.7z) [412 MB]",

    d2_badge: "单行终端安装",
    d2_title: "自动化部署脚本",
    d2_desc: "根据当前GPU架构自动匹配下载专用引擎二进制，完成硬件检测并自动写入用户环境变量PATH，无需管理员提权。",

    arch_pill: "系统概览",
    arch_title: "三层严格隔离架构",
    arch_desc: "层与层之间职责清晰，推理底层出现异常绝不波及宿主界面与CLI进程。",

    arch_l1_title: "宿主界面与 Web 服务",
    arch_l1_desc: "Vite + React + Tauri 桌面壳体，支持高并发非阻塞 WebSocket 与 SSE 事件流。",
    arch_l2_title: "Strata Control 与智能体运行时",
    arch_l2_desc: "Python 3.10/3.12 调度中心、Hermes 记忆机制、MCP 协议端点及 ModelBundle 格式安全检验。",
    arch_l3_title: "原生 C++/CUDA 推理内核",
    arch_l3_desc: "strata.exe、strata_kq.dll、Spin(8) 三元性核心、动态共享内存专家缓存、GGUF 高速 mmap。",

    footer_text: "Strata Fork — 高性能 MoE 与 MLA 本地推理引擎。基于 MIT 开源协议发布。"
  }
};

let currentLang = "en";

function setLanguage(lang) {
  if (!translations[lang]) lang = "en";
  currentLang = lang;
  localStorage.setItem("strata_lang", lang);

  const dict = translations[lang];
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  document.querySelectorAll(".lang-selector").forEach((sel) => {
    sel.value = lang;
  });

  document.documentElement.lang = lang === "zh" ? "zh-CN" : lang;
}

function initTerminalTabs() {
  const tabs = document.querySelectorAll(".term-tab");
  const cmd = document.getElementById("terminal-cmd");
  const cmds = {
    pwsh: "irm https://github.com/zapabob/Strata/releases/latest/download/install.ps1 | iex",
    bash: "curl -fsSL https://github.com/zapabob/Strata/releases/latest/download/install.sh | sh"
  };

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const type = tab.getAttribute("data-tab");
      if (cmd && cmds[type]) {
        cmd.textContent = cmds[type];
      }
    });
  });

  const copyBtn = document.getElementById("copy-cmd-btn");
  if (copyBtn && cmd) {
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(cmd.textContent.trim()).then(() => {
        showToast();
      });
    });
  }
}

function showToast() {
  const toast = document.getElementById("copy-toast");
  if (!toast) return;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

document.addEventListener("DOMContentLoaded", () => {
  // Determine language preference
  const saved = localStorage.getItem("strata_lang");
  const urlParam = new URLSearchParams(window.location.search).get("lang");
  const browser = (navigator.language || navigator.userLanguage || "en").toLowerCase();

  let initial = "en";
  if (urlParam && translations[urlParam]) {
    initial = urlParam;
  } else if (saved && translations[saved]) {
    initial = saved;
  } else if (browser.startsWith("ja")) {
    initial = "ja";
  } else if (browser.startsWith("zh")) {
    initial = "zh";
  }

  setLanguage(initial);

  document.querySelectorAll(".lang-selector").forEach((sel) => {
    sel.addEventListener("change", (e) => {
      setLanguage(e.target.value);
    });
  });

  initTerminalTabs();
});
