# Hakua / Strata 0.5.6-local.1 preview

`/btw <question>` opens a separate, tool-free answer while the main chat remains active. Side answers have their own stop and dismiss controls and persist outside the main transcript. A single-slot engine may schedule the answer after current inference.

`/deepresearch <topic>` extends research with multiple searches and page reads. The report distinguishes incomplete evidence and cites pages actually read. Existing `/research` remains available. Tool approval settings still apply.

RustXNG 0.31.1 is bundled as a separate pinned executable and always runs with its Full profile when selected. Choose it in Settings → Tools → Search. It listens on loopback only; optional paid providers are not automatically enabled. Search queries go to enabled external services under their terms. LICENSE, NOTICE and exact corresponding source are included both as release assets and in the installed `harness/rustxng` folder. No runtime binary download or automatic RustXNG update is used.

The README was rewritten and all eight README languages now thank and link [Strata](https://github.com/Niko1221/Strata), [llama.cpp](https://github.com/ggml-org/llama.cpp) and [RustXNG](https://github.com/sahenjp/RustXNG). Their engineering makes this work possible. This fork is independently maintained; these acknowledgements imply no upstream endorsement.

## Windows installation

Use `Strata-0.5.6-local.1-windows-x64-setup.exe`, a current-user Tauri NSIS installer using the upstream packaging approach. `Strata-0.5.6-local.1-windows-x64.tar.7z` contains the identical installer, separate signed engine and Control packages, signed feed, instructions, provenance and checksums. Extract the 7z file and then its inner tar. Compare `SHA256SUMS.txt` before use and `BUNDLE-SHA256SUMS.txt` after extraction.

Finish requests, unload the model, back up data and quit Strata including its tray icon before updating. The installer uses the existing app folder; models, chats and memories remain outside installer-managed files. Import the still-compressed engine package through the app's existing-file preparation screen. Models and personal data are not distributed.

The app version is 0.5.6-local.1. Native CUDA remains 0.5.5 and Control remains 0.5.6; their previously published signed bytes are unchanged. The Windows installer has no Authenticode signature. The component feed signature is verified independently using bundled public keys.

## Verification and limits

The app was built with five compiler jobs under the existing RAM, commit and disk resource guards. TypeScript passed; 37 focused host tests passed, with three explicit optional skips. Two real Harness research tests, 13 packaged self-tests and six installer cleanup scenarios passed. The overwrite installation matched all 29,552 managed-file hashes, and 3,719 inventoried user files were unchanged immediately after installation.

Installed WebView2 checks use the actual updated executable and a clearly isolated local model API fixture. They verify side questions during a live main stream, separate persistence, independent lifecycle, slash-menu availability, page reload and mobile layout. Actual RustXNG Full searches returned public results. These checks do not qualify real-model quality, concurrent GPU throughput or full-window inference.

The initial broad host suite recorded 2,013 passes, 29 failures and 117 skips. All 28 pre-existing failure titles reproduced on the prior-source baseline; a new duplicate translation was fixed and focused checks reran successfully. The broad suite does not pass. `releaseQualified=false`; stable v0.5.1, GitHub Latest, previous tags and previous release assets remain unchanged. `SOURCE.json` distinguishes app, native and Control source commits and records the official Tauri NSIS bundle-marker substitution. `QUALITY.json` records the limits.

日本語: `/btw` は本題と別の質問、`/deepresearch` は検索とページ閲覧を伴う調査です。RustXNG は設定のツールで選択すると Full 構成で起動します。上書き前に生成の停止、モデルのアンロード、バックアップ、トレイを含む終了を済ませてください。配布物はプレビュー版です。実モデルの回答品質やGPU同時実行性能、フルコンテキストの保証は行っていません。安定版の配布先と過去の資産は維持しています。
