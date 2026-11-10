# Hakua / Strata 0.5.5-local.1 — Windows

This package contains the measured setup EXE, signed native engine0.5.5,
Control0.5.6, signed feed, checksums, SOURCE.json and QUALITY.json. It targets
Windows x64/CUDA sm_120; checks used RTX5060Ti16GB,32GB RAM and driver621.14.
The native resource guard passes with zero violations. Actual installed Q36,
Prism, agent and sidebar/bulk-delete checks passed. releaseQualified=false:
full-window/general/low-precision quality and public search sites remain unqualified.
The historical054 Prism timeout remains recorded with unconfirmed cause.

## Install

1. Check the outer SHA256SUMS.txt, extract7z then tar, and compare the inner
   BUNDLE-SHA256SUMS.txt. Full models and personal profiles are not included.
2. Finish requests, unload models, back up app data and quit Strata including its
   tray icon. Run Strata-0.5.5-local.1-windows-x64-setup.exe once.
3. On the preparation screen choose the existing-engine-file option and select
   strata-engine-0.5.5-windows-x86_64-cuda-cuda13.tar.gz without extracting it.
   The app verifies the fork signature and complete payload before activation.
4. Choose a model that fits, or reuse a local GGUF, and press Load. Startup is
   manual/unloaded. System Python/Node/pip/compilers are unnecessary.

The setup EXE has no Windows code signature/Tauri updater signature; engine
component signatures are separate. Stable0.5.1 remains GitHub Latest. Preview
updates use the explicit immutable055 URL. A newer accepted feed sequence blocks
older feeds even across URLs: keep this anti-replay guard and use retained installed
component rollback or a separate component/data directory for stable/preview state.

Folder menu: Delete all chats in folder asks for the folder/count and includes
archived history. It is permanent; actual files and other folders stay. Archive
chat is the reversible option. Settings → Tools enables search and an isolated
browser. Manual asks before browser actions. Text-only models use accessibility
snapshots/coordinates, not claimed image understanding. Site challenges are not bypassed.

## 日本語

7z、tarの順に展開し、外側・内側のチェックサムを照合してください。
応答を終了してモデルをアンロードし、データをバックアップしてトレイからも終了後、
Strata-0.5.5-local.1-windows-x64-setup.exeを実行します。
準備画面では、同梱の署名付きエンジンtar.gzを展開せず選択します。
モデルは別途選び、読み込みを押します。手元のGGUFも再利用できます。

左フォルダーの「…」から会話履歴を一括削除できます。アーカイブも対象となり、
確認した会話だけを削除します。ファイルや他のフォルダーは削除しません。
設定→ツールでWeb検索・Webブラウザーを有効にできます。Computer-useの座標操作は
直前のページ情報を使い、Manualの確認設定を維持します。
DuckDuckGoの認証チャレンジやサイト制限を自動回避する機能ではありません。

資源違反0件、実installedのQ36・Prism・エージェント・一括削除は通過しました。
releaseQualified=false、全文入力・一般品質・低精度品質・公開検索サイトは未認定です。
安定版0.5.1と過去の配布物は保持します。
