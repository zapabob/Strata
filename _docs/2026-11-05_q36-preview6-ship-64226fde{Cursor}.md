# 2026-11-05 Q36 preview `.6` ship（64226fde honesty）{Cursor}

## 概要

durable Q36 Hakua goal を継続。T06 は明確な測定可能候補なしのため **NOT_RUN**。代わりに Windows preview `0.4.0-preview.20261103.6` を NSIS 出荷し、allowlist 正直化（`64226fde…`）・`/S /UPDATE`・`gh release create --latest=false`・README/HAKUA hashes 更新まで完了。Goal complete にしない。Hermes 未殺。署名 `b5e4d525…` 非接触。T04 採用判断なし。

## 背景・要求

- State: T03 PASS、T04 PAIR_RECORDED×1（adoption NOT_DECIDED）、製品は `.5`（旧 digest）、T06–T08 NOT_RUN
- Prefer T06 if clear candidate + VRAM≥12 GiB；else ship next preview with packaging honesty for `64226fde…`

## 前提・判断（CoT）

1. VRAM free ~14.8 GiB → T06 ハード条件は満たす
2. 計画 T06 は scheduler/code + RED tests が前提。観測ペアの再実施ではない → **候補なし = T06 BLOCKED**
3. VERSION 慣習: `20261103.N` 系列を継続 → **`.6`**（help-rebuild ログの「`.6` 相当」と一致）
4. 署名コンポーネント上書き禁止。アプリ installer は CUDA 非同梱；allowlist/docs 正直化が本 ship の中核
5. `native-build.json` の `native_gdn.hpp` 記録ハッシュ異常を現ツリー LF で再記録（バイナリ `64226fde…` 維持）。エンジン再ビルドなし

## 変更対象ファイル

- `VERSION` ほか製品版文字列 → `0.4.0-preview.20261103.6`
- `apps/host/server/q36-run-contract.mjs`（allowlist コメント）
- README 8 本 / `docs/HAKUA_RELEASE.md` / `docs/HAKUA_INSTALL.md` / `packaging/README.md` / `AGENTS.md`
- `_docs/q36-32gb16gb/{evidence-summary.json,DESIGN.md,計画書,NOTES-01-28-preview6-ship.md}`
- staged Control（`stage-control.py`；gitignored resources）
- 本実装ログ

## 実装詳細

1. Host public rebuild（Node 24.22.2）+ `stage-control.py` + `verify-release` PASS
2. NSIS（`CARGO_TARGET_DIR=H:\Strata\releases\hakua040-nsis-cargo-20261103-6`；sccache wrapper 解除）
3. Setup hash / `/S /UPDATE` / DisplayVersion `.6`
4. `gh release create v0.4.0-preview.20261103.6 --latest=false`
5. docs honesty: `64226fde…` を主導 digest として記載；signed untouched 明記

## 実行コマンド

```powershell
py -3 tools/bump_hakua_product_version.py --set 0.4.0-preview.20261103.6   # partial; README.de で止まり手直し
node24 apps/host/scripts/build.mjs   # STRATA_PUBLIC_PACKAGE=1
py -3 apps/desktop/scripts/stage-control.py
node24 apps/desktop/scripts/verify-release.mjs
# RUSTC_WRAPPER= ; CARGO_TARGET_DIR=H:\...\hakua040-nsis-cargo-20261103-6
tauri build --bundles nsis
setup.exe /S /UPDATE
gh release create v0.4.0-preview.20261103.6 --latest=false ...
```

## テスト・検証結果

| Item | Result |
|------|--------|
| verify-release | PASS（Hakua `.6`, engine 0.4.0） |
| NSIS | exit 0；113075186 bytes；SHA-256 `784d4f992443a43076e7de8dbcdc624b35d95e97e13b716ea9de0e13a1baeac9` |
| `/S /UPDATE` | INSTALL_EXIT=0；DisplayVersion `.6` |
| signed `b5e4d525…` | untouched |
| unsigned `64226fde…` | unchanged on side-by-side component |
| T04 adoption | NOT_DECIDED |
| T06–T08 | NOT_RUN |
| Hermes killed | false |
| Goal complete | false |
| Release | https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.6 |

## 残留リスク

- T06 転送最適化・T07 hotspot・T08 FP16 KV は未着手
- T04 n=1；採用判断なし
- spill guard 不合格のまま
- アプリ installer は CUDA 非同梱；ユーザーは別途 unsigned q36 component / 既存 side-by-side が必要
- `native-build.json` sources 再記録はバイナリ再ビルドではない（GDN hpp 記録異常の修正）

## 次の推奨アクション

1. T06: RED tests + 1 候補 arm の実装後に正直な paired 測定
2. 追加 T04 pairs（任意）
3. upstream PR #5216/#5221 フォロー
4. **UpdateGoal complete しない**
