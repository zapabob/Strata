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

    hero_pill: "Windows fork preview: 29 October 2026",
    hero_title: "Local inference, with measured limits",
    hero_desc: "Desktop and Terminal interfaces for native inference and compatible GGUF models. Actual 4K and 32K generation is documented; full 131k certification remains open.",
    hero_download: "Download Windows NSIS (0.3.2-preview.20261029.2)",
    hero_github: "View on GitHub",
    copied_toast: "Command copied to clipboard!",

    tab_pwsh: "PowerShell (Windows)",
    tab_bash: "Shell (Linux / Mac)",

    feat_pill: "Technical Highlights",
    feat_title: "What this preview changes",
    feat_desc: "Measured on RTX 5060 Ti 16 GiB and 32 GiB RAM. Model compatibility depends on the selected backend.",

    f1_title: "Qwen3.8 inference verified",
    f1_desc: "Q2_0, configured capacity 131072, spec4 + MTP and k8v4 completed exact 4096- and 32768-token requests. This does not certify full-length inference.",
    f1_tag: "Actual generation",

    f2_title: "Local GGUF import",
    f2_desc: "Inspect local text GGUF files and offer a generic backend when native import is unsupported. Loading still checks actual backend compatibility.",
    f2_tag: "Explicit compatibility checks",

    f3_title: "Startup resource lifetime",
    f3_desc: "Join completed prefetch threads so their I/O scratch is released. CPU failure-injection tests and the CUDA build have separate evidence.",
    f3_tag: "Measured startup fix",

    f4_title: "Hakua memory + Hermes SOUL",
    f4_desc: "Sidebar Hakua stays on via host/hakua-chatbot.enabled. Hermes SOUL.md/MEMORY.md sync into hakua-memory (Ebbinghaus, RAG + graph, Obsidian, sleep). Harness consent stays opt-in; pip pin hakua-memory==0.3.5.",
    f4_tag: "Consented; pin 0.3.5",

    f5_title: "Long local requests",
    f5_desc: "The quiet local inference allowance is 30 minutes. Remote and tool limits remain separate. Cancellation and subsequent recovery passed real Harness tests.",
    f5_tag: "Finite timeout and cancellation",

    f6_title: "Windows CUDA SM120 preview",
    f6_desc: "The tested artifact targets Windows x64 and RTX 5060 Ti. HIP, SYCL, other GPUs and image inference are not qualified by these results.",
    f6_tag: "Hardware scope stated",

    bench_pill: "Actual synthetic inference",
    bench_title: "RTX 5060 Ti 16 GiB + RAM 32 GiB",
    bench_desc: "One synthetic recall task; diagnostics OFF. First and repeated requests each generated 52 tokens. No paired statistical speed or broad quality conclusion.",

    m1_val: "4096 / 32768",
    m1_label: "Actual input tokens",
    m2_val: "4 / 4",
    m2_label: "Sentinel recall probes passed",
    m3_val: "494.76 s",
    m3_label: "32K first prompt processing",
    m4_val: "22.69 GiB",
    m4_label: "32K peak Job commit",

    th_model: "Input / request",
    th_engine: "Configuration",
    th_vram: "Peak Job commit",
    th_prefill: "Prompt time",
    th_decode: "Decode time (52 tokens)",

    tb1_model: "4096 / first",
    tb1_eng: "Qwen3.8 Q2_0, spec4 + MTP",
    tb1_vram: "22.14 GiB",
    tb1_pre: "105.562 s",
    tb1_dec: "13.531 s",

    tb2_model: "32768 / first",
    tb2_eng: "Qwen3.8 Q2_0, spec4 + MTP",
    tb2_vram: "22.69 GiB",
    tb2_pre: "494.758 s",
    tb2_dec: "13.759 s",

    tb3_model: "32768 / repeated",
    tb3_eng: "Same run; prefix reuse",
    tb3_vram: "22.69 GiB (run peak)",
    tb3_pre: "0.646 s",
    tb3_dec: "3.255 s",

    dl_pill: "Distribution & Verification",
    dl_title: "Download Releases",
    dl_desc: "Preview archives have SHA-256 checksums and dependency manifests. Read their scope and installation instructions before applying an overlay.",

    d1_badge: "Windows NSIS installer",
    d1_title: "Strata 0.3.2-preview.20261029.2 (unsigned NSIS)",
    d1_desc: "Overwrite-capable Windows x64 setup for product 0.3.2-preview.20261029.2 (engine 0.1.53). Unsigned preview; signed feed/Tauri updater is not included. Keep your models folder when upgrading. Link 404s until the release asset is uploaded.",
    d1_btn: "Download NSIS (when published)",

    d2_badge: "Upstream sync notes",
    d2_title: "v0.3.2-preview.20261028.1 (source sync)",
    d2_desc: "Fork tip notes after merging official Strata v0.2.7.1. No installer asset on this tag — use the NSIS card for setup.exe.",

    arch_pill: "System Overview",
    arch_title: "Desktop, Control and inference backend",
    arch_desc: "Separate processes manage the interface, model lifecycle and inference. Ownership checks stop recovery when a child cannot be identified.",

    arch_l1_title: "Host GUI & Web Interface",
    arch_l1_desc: "Vite + React + Tauri shell. Non-blocking async WebSocket & SSE streaming.",
    arch_l2_title: "Strata Control & Agent Runtime",
    arch_l2_desc: "Python profile and runtime ownership management, model setup and API service. Optional memory integration is disabled by default.",
    arch_l3_title: "Native C++/CUDA Inference Engine",
    arch_l3_desc: "The native CUDA engine and the separately packaged generic GGUF backend. Support and resource needs depend on model and configuration.",

    footer_text: "Strata fork. Source and measured preview limitations are available on GitHub."
  },

  ja: {
    brand_sub: "フォーク版",
    nav_features: "機能特徴",
    nav_benchmarks: "ベンチマーク",
    nav_downloads: "ダウンロード",
    nav_arch: "アーキテクチャ",
    nav_github: "GitHub",

    hero_pill: "Windows フォークプレビュー: 2026年10月29日",
    hero_title: "Local inference, with measured limits",
    hero_desc: "Desktop and Terminal interfaces for native inference and compatible GGUF models. Actual 4K and 32K generation is documented; full 131k certification remains open.",
    hero_download: "Windows NSIS をダウンロード (0.3.2-preview.20261029.2)",
    hero_github: "GitHubリポジトリを表示",
    copied_toast: "コマンドをクリップボードにコピーしました！",

    tab_pwsh: "PowerShell (Windows)",
    tab_bash: "Shell (Linux / Mac)",

    feat_pill: "技術的特徴",
    feat_title: "What this preview changes",
    feat_desc: "Measured on RTX 5060 Ti 16 GiB and 32 GiB RAM. Model compatibility depends on the selected backend.",

    f1_title: "Qwen3.8 inference verified",
    f1_desc: "Q2_0, configured capacity 131072, spec4 + MTP and k8v4 completed exact 4096- and 32768-token requests. This does not certify full-length inference.",
    f1_tag: "Actual generation",

    f2_title: "Local GGUF import",
    f2_desc: "Inspect local text GGUF files and offer a generic backend when native import is unsupported. Loading still checks actual backend compatibility.",
    f2_tag: "Explicit compatibility checks",

    f3_title: "Startup resource lifetime",
    f3_desc: "Join completed prefetch threads so their I/O scratch is released. CPU failure-injection tests and the CUDA build have separate evidence.",
    f3_tag: "Measured startup fix",

    f4_title: "Hakua memory + Hermes SOUL",
    f4_desc: "Sidebar Hakua stays on via host/hakua-chatbot.enabled. Hermes SOUL.md/MEMORY.md sync into hakua-memory (Ebbinghaus, RAG + graph, Obsidian, sleep). Harness consent stays opt-in; pip pin hakua-memory==0.3.5.",
    f4_tag: "Consented; pin 0.3.5",

    f5_title: "Long local requests",
    f5_desc: "The quiet local inference allowance is 30 minutes. Remote and tool limits remain separate. Cancellation and subsequent recovery passed real Harness tests.",
    f5_tag: "Finite timeout and cancellation",

    f6_title: "Windows CUDA SM120 preview",
    f6_desc: "The tested artifact targets Windows x64 and RTX 5060 Ti. HIP, SYCL, other GPUs and image inference are not qualified by these results.",
    f6_tag: "Hardware scope stated",

    bench_pill: "Actual synthetic inference",
    bench_title: "RTX 5060 Ti 16 GiB + RAM 32 GiB",
    bench_desc: "One synthetic recall task; diagnostics OFF. First and repeated requests each generated 52 tokens. No paired statistical speed or broad quality conclusion.",

    m1_val: "4096 / 32768",
    m1_label: "Actual input tokens",
    m2_val: "4 / 4",
    m2_label: "Sentinel recall probes passed",
    m3_val: "494.76 s",
    m3_label: "32K first prompt processing",
    m4_val: "22.69 GiB",
    m4_label: "32K peak Job commit",

    th_model: "Input / request",
    th_engine: "Configuration",
    th_vram: "Peak Job commit",
    th_prefill: "Prompt time",
    th_decode: "Decode time (52 tokens)",

    tb1_model: "4096 / first",
    tb1_eng: "Qwen3.8 Q2_0, spec4 + MTP",
    tb1_vram: "22.14 GiB",
    tb1_pre: "105.562 s",
    tb1_dec: "13.531 s",

    tb2_model: "32768 / first",
    tb2_eng: "Qwen3.8 Q2_0, spec4 + MTP",
    tb2_vram: "22.69 GiB",
    tb2_pre: "494.758 s",
    tb2_dec: "13.759 s",

    tb3_model: "32768 / repeated",
    tb3_eng: "Same run; prefix reuse",
    tb3_vram: "22.69 GiB (run peak)",
    tb3_pre: "0.646 s",
    tb3_dec: "3.255 s",

    dl_pill: "配布 & 検証",
    dl_title: "リリースダウンロード",
    dl_desc: "Preview archives have SHA-256 checksums and dependency manifests. Read their scope and installation instructions before applying an overlay.",

    d1_badge: "Windows NSIS インストーラ",
    d1_title: "Strata 0.3.2-preview.20261029.2（署名なし NSIS）",
    d1_desc: "製品 0.3.2-preview.20261029.2（エンジン 0.1.53）向けの上書き可能な Windows x64 セットアップ。署名付き feed / Tauri updater は含みません。資産アップロード前はリンクが 404 になります。",
    d1_btn: "NSIS をダウンロード（公開後）",

    d2_badge: "上流同期メモ",
    d2_title: "v0.3.2-preview.20261028.1（ソース同期）",
    d2_desc: "公式 Strata v0.2.7.1 取り込み後のフォーク tip メモ。このタグにインストーラ資産はありません。setup.exe は NSIS カードを使ってください。",

    arch_pill: "システム全体像",
    arch_title: "Desktop, Control and inference backend",
    arch_desc: "Separate processes manage the interface, model lifecycle and inference. Ownership checks stop recovery when a child cannot be identified.",

    arch_l1_title: "ホストGUI & Webインターフェース",
    arch_l1_desc: "Vite + React + Tauriシェル。非同期WebSocket & SSEストリーミング対応。",
    arch_l2_title: "Strata Control & エージェント実行基盤",
    arch_l2_desc: "Python profile and runtime ownership management, model setup and API service. Optional memory integration is disabled by default.",
    arch_l3_title: "ネイティブ C++/CUDA 推論エンジン",
    arch_l3_desc: "The native CUDA engine and the separately packaged generic GGUF backend. Support and resource needs depend on model and configuration.",

    footer_text: "Strata fork. Source and measured preview limitations are available on GitHub."
  },

  zh: {
    brand_sub: "分叉版",
    nav_features: "技术特性",
    nav_benchmarks: "基准测试",
    nav_downloads: "下载资源",
    nav_arch: "系统架构",
    nav_github: "GitHub",

    hero_pill: "Windows 分叉预览：2026 年 10 月 29 日",
    hero_title: "Local inference, with measured limits",
    hero_desc: "Desktop and Terminal interfaces for native inference and compatible GGUF models. Actual 4K and 32K generation is documented; full 131k certification remains open.",
    hero_download: "下载 Windows NSIS (0.3.2-preview.20261029.2)",
    hero_github: "查看 GitHub 仓库",
    copied_toast: "安装命令已复制到剪贴板！",

    tab_pwsh: "PowerShell (Windows)",
    tab_bash: "Shell (Linux / Mac)",

    feat_pill: "核心技术优势",
    feat_title: "What this preview changes",
    feat_desc: "Measured on RTX 5060 Ti 16 GiB and 32 GiB RAM. Model compatibility depends on the selected backend.",

    f1_title: "Qwen3.8 inference verified",
    f1_desc: "Q2_0, configured capacity 131072, spec4 + MTP and k8v4 completed exact 4096- and 32768-token requests. This does not certify full-length inference.",
    f1_tag: "Actual generation",

    f2_title: "Local GGUF import",
    f2_desc: "Inspect local text GGUF files and offer a generic backend when native import is unsupported. Loading still checks actual backend compatibility.",
    f2_tag: "Explicit compatibility checks",

    f3_title: "Startup resource lifetime",
    f3_desc: "Join completed prefetch threads so their I/O scratch is released. CPU failure-injection tests and the CUDA build have separate evidence.",
    f3_tag: "Measured startup fix",

    f4_title: "Hakua memory + Hermes SOUL",
    f4_desc: "Sidebar Hakua stays on via host/hakua-chatbot.enabled. Hermes SOUL.md/MEMORY.md sync into hakua-memory (Ebbinghaus, RAG + graph, Obsidian, sleep). Harness consent stays opt-in; pip pin hakua-memory==0.3.5.",
    f4_tag: "Consented; pin 0.3.5",

    f5_title: "Long local requests",
    f5_desc: "The quiet local inference allowance is 30 minutes. Remote and tool limits remain separate. Cancellation and subsequent recovery passed real Harness tests.",
    f5_tag: "Finite timeout and cancellation",

    f6_title: "Windows CUDA SM120 preview",
    f6_desc: "The tested artifact targets Windows x64 and RTX 5060 Ti. HIP, SYCL, other GPUs and image inference are not qualified by these results.",
    f6_tag: "Hardware scope stated",

    bench_pill: "Actual synthetic inference",
    bench_title: "RTX 5060 Ti 16 GiB + RAM 32 GiB",
    bench_desc: "One synthetic recall task; diagnostics OFF. First and repeated requests each generated 52 tokens. No paired statistical speed or broad quality conclusion.",

    m1_val: "4096 / 32768",
    m1_label: "Actual input tokens",
    m2_val: "4 / 4",
    m2_label: "Sentinel recall probes passed",
    m3_val: "494.76 s",
    m3_label: "32K first prompt processing",
    m4_val: "22.69 GiB",
    m4_label: "32K peak Job commit",

    th_model: "Input / request",
    th_engine: "Configuration",
    th_vram: "Peak Job commit",
    th_prefill: "Prompt time",
    th_decode: "Decode time (52 tokens)",

    tb1_model: "4096 / first",
    tb1_eng: "Qwen3.8 Q2_0, spec4 + MTP",
    tb1_vram: "22.14 GiB",
    tb1_pre: "105.562 s",
    tb1_dec: "13.531 s",

    tb2_model: "32768 / first",
    tb2_eng: "Qwen3.8 Q2_0, spec4 + MTP",
    tb2_vram: "22.69 GiB",
    tb2_pre: "494.758 s",
    tb2_dec: "13.759 s",

    tb3_model: "32768 / repeated",
    tb3_eng: "Same run; prefix reuse",
    tb3_vram: "22.69 GiB (run peak)",
    tb3_pre: "0.646 s",
    tb3_dec: "3.255 s",

    dl_pill: "分发与完整性验证",
    dl_title: "下载发行包",
    dl_desc: "Preview archives have SHA-256 checksums and dependency manifests. Read their scope and installation instructions before applying an overlay.",

    d1_badge: "Windows NSIS 安装包",
    d1_title: "Strata 0.3.2-preview.20261029.2（未签名 NSIS）",
    d1_desc: "面向产品 0.3.2-preview.20261029.2（引擎 0.1.53）的可覆盖 Windows x64 安装程序。不含签名 feed / Tauri 更新器。资产上传前链接会 404。",
    d1_btn: "下载 NSIS（发布后）",

    d2_badge: "上游同步说明",
    d2_title: "v0.3.2-preview.20261028.1（源码同步）",
    d2_desc: "合并官方 Strata v0.2.7.1 后的分叉 tip 说明。此标签无安装包——请用 NSIS 卡片下载 setup.exe。",

    arch_pill: "系统概览",
    arch_title: "Desktop, Control and inference backend",
    arch_desc: "Separate processes manage the interface, model lifecycle and inference. Ownership checks stop recovery when a child cannot be identified.",

    arch_l1_title: "宿主界面与 Web 服务",
    arch_l1_desc: "Vite + React + Tauri 桌面壳体，支持高并发非阻塞 WebSocket 与 SSE 事件流。",
    arch_l2_title: "Strata Control 与智能体运行时",
    arch_l2_desc: "Python profile and runtime ownership management, model setup and API service. Optional memory integration is disabled by default.",
    arch_l3_title: "原生 C++/CUDA 推理内核",
    arch_l3_desc: "The native CUDA engine and the separately packaged generic GGUF backend. Support and resource needs depend on model and configuration.",

    footer_text: "Strata fork. Source and measured preview limitations are available on GitHub."
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
    pwsh: "Start-Process https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261029.2",
    bash: "if command -v open >/dev/null 2>&1; then open https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261029.2; else xdg-open https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261029.2; fi"
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
