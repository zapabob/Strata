# Q36 Hakua durable goal — 引き継ぎ計画書

作成: 2026-11-04 JST（Cursor）  
作業根: `C:\Users\downl\Documents\ChatGPT\Strata`  
ブランチ: `main`（HEAD `425776c3` 時点の記録。本ファイルコミット後は変わる）  
Goal complete: **false**（`UpdateGoal complete` しない）

> なんJ要約（1段落のみ）: Q36の mapped-pack+pin-pool まで製品 `.5` に乗せて、ローカル未署名 `64226fde…` まで help 正直化も済んだけど、VRAM は Hermes Hikari（歴史的 PID 14572）に食われて live が止まってる。18:14 は部分ロードまで行ったがログ取り損ねて abort。次の担当は Hermes が空いたら durable launcher 一発、pin-pool ログ取ってから T03→paired。数字捏造禁止・Hermes 無断殺禁止。

---

## 1. 目的 / 完了条件

### 目的（DESIGN / 実装計画より）

- RAM 32GB / RTX 5060 Ti 16GB で、同一 **Qwen3.6-35B-A3B UD-Q4_K_XL** を継続利用できる経路にする。
- 主比較条件: context **65536**、同一 GGUF / tokenizer、FP32 KV、**MTP=2**、実効 prefill **2048**、単一会話。
- 単なる READY 高速化ではなく、初回有用応答・継続 decode・停止・再ロードまで評価する。
- 本線は opt-in の **mapped-pack + bounded pin-pool**（全 expert 匿名 private arena を避ける）。

### 完了条件（未達）

DESIGN §6 / 計画書どおり、少なくとも次が揃うまで **完了宣言しない**:

1. Windows GPU で mapped-pack live が成立し、stderr に **`Q36_STARTUP`** と **ExpertPinPool / pin-pool** 行がファイル証跡として残る。
2. **T03** chat → stop → restart が同一実効設定で通る。
3. **T04 / T06 / T07 / T08** は paired 実測のみ。数の捏造禁止。paired なしでの既定化禁止。
4. 機能・隔離・品質ゲート合格後、主性能目標（提案）は「起動要求→最初の有用 token 中央値 30% 以上短縮」かつ初回・継続 decode 中央値を 5% 超悪化させないこと。**達成済み数値ではない。**
5. DESIGN 非交渉契約（特に #6 他推論 server 無断 kill 禁止、#10 署名迂回・配布手動上書き禁止）を破らない。

参照正本:

- `_docs/q36-32gb16gb/DESIGN.md`
- `_docs/q36-32gb16gb/Strata_Qwen36_Implementation_Plan_2026-11-02.md`
- `_docs/q36-32gb16gb/evidence-summary.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-18-21.md`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-05-22-rebuild.md`

---

## 2. 現状サマリ（証跡付き）

| 項目 | 状態 | 証跡 |
|---|---|---|
| 製品 installer | **0.4.0-preview.20261103.5** 出荷済 | `6b0dde7e`、`docs/HAKUA_RELEASE.md` / 実装ログ `.5` |
| 製品 `.5` に同梱の pin-pool 経路 | 実装・出荷済（当時 digest 系は `6fe11065…` 系） | `d2383018`, `13df0153`, `7f9be950` |
| ローカル未署名 q36 engine | SHA-256 **`64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`**（help 正直化 rebuild） | `NOTES-05-22-rebuild.md`, `e898c41c` |
| 署名済み engine | SHA-256 **`b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1`** — **非接触** | `evidence-summary.json` session_1812 / NOTES |
| mapped-pack live | **BLOCKED**（VRAM） | `NOTES-18-21.md`, `preflight-blocker-18-21.json`, `run-18-27-gate/` |
| 18:14 部分ロード | 開始成功（VRAM ~865→~15912 MiB）だが stderr/stdin 捕捉失敗で abort。**Q36_STARTUP / pin-pool 未取得** | `run-18-14/`, `abort-note.txt` |
| durable launcher | 追加済。18:22 / 18:27 ゲートは exit 4 BLOCKED（free ~5393–5399 MiB < 12000） | `launch_mapped_live_durable.py`, `run-18-22-gate/`, `run-18-27-gate/` |
| T03 GUI refuse | **PARTIAL**（private-cache 拒否。強制解除なし） | `evidence-2026-11-04-gui/`, `7f9be950` |
| T03 chat/stop/restart | **NOT_RUN** | serve 未成立 |
| T04–T08 paired | **NOT_RUN** | `invented_speeds: false` |
| Hermes kill | **false**（DESIGN #6） | 全 NOTES |

### 注目コミット（時系列・新しい順に近いもの）

| SHA | 概要 |
|---|---|
| `425776c3` | [Docs] mapped-pack 部分ロード後 Hermes VRAM 再ブロックを記録 |
| `e898c41c` | [Engine] help 正直化 unsigned digest `64226fde…` を allowlist |
| `883212c5` | [Docs] VRAM blocker + `--q36-expert-store` help 文書化 |
| `79ebbc25` | [Docs] H: 空き回収（mapped-live は依然 BLOCKED） |
| `7f9be950` | [GUI] Qwen3.6 private-cache 拒否・mutated retry 抑止 |
| `d2383018` | [GUI] pin-pool mapped-pack を 20261103.5 に同梱 |
| `6b0dde7e` | [Docs] `.5` installer ship / release URL |
| `13df0153` | [Engine] mapped-pack H2D を bounded pin-pool 経由 |

その他関連: `457e4328`（pin-pool digest 期待）、`53dd2922`（CPU-tested pin-pool lifetimes）。

---

## 3. T00–T09 表

正直ラベル。未実行を PASS にしない。

| Task | 状態 | 短い根拠 / 証跡パス |
|---|---|---|
| **T00** 基準・fixture・binding | **DONE**（計画パッケージ＋実機 binding 継続更新） | `_docs/q36-32gb16gb/` 一式、`evidence-summary.json` |
| **T01** パス・能力・契約 | **DONE**（Host 契約 / refuse / refuse） | Host q36 node **19/19 PASS**（`host-q36-node-tests-04-08.txt`）、`q36-run-contract.mjs` |
| **T02** 起動 stage 観測 | **PARTIAL** → コード側 DONE、**live ログ未捕捉** | stage/Q36_STARTUP 実装あり；`run-18-14` でファイル未取得 |
| **T03** 起動許可・停止・再起動 | **PARTIAL** | GUI refuse DONE（`evidence-2026-11-04-gui/`）；**chat→stop→restart NOT_RUN** |
| **T04** warmup 費用移動検出 | **NOT_RUN** | live 前提未達 |
| **T05** mapped ExpertStore / pin-pool | **PARTIAL** | 実装・installer `.5` / ローカル `64226fde…` DONE；**GPU live 証明 BLOCKED** |
| **T06** 転送・配置最適化（paired） | **NOT_RUN** | 偽速度禁止 |
| **T07** hotspot CUDA（paired） | **NOT_RUN** | 同上 |
| **T08** FP16 KV 等（任意） | **NOT_RUN** | 本線必須ではない |
| **T09** GUI・配布・E2E | **PARTIAL** | `.5` 出荷済；次インストーラへの `64226fde…` 反映は任意・未実施；E2E live 未完 |

全体ラベル（`evidence-summary.json`）: `PARTIAL_IMPL_GPU_SPEED_NOT_RUN` / `goal_complete: false`。

---

## 4. ブロッカー

1. **Hermes Hikari VRAM 占有（DESIGN #6）**  
   - 歴史的: PIDs `22836`/`22944`（朝方）。夕刻以降は **PID `14572`**（`llama-server`、Hikari-LoRA-fixed-scale-PQ2_0、`n_ctx 98304`）。  
   - 18:27 再測定: used ~10658 MiB / free ~**5393** MiB（ゲート下限 12000 MiB 未満）。  
   - **kill しない。** ユーザーが Hermes を止めるか、自然終了を待つ。

2. **18:14 部分ロード後のログ abort**  
   - free ~15446 MiB で GO → mapped-pack ロード開始（VRAM peak ~15912）。  
   - PowerShell async stdout/stderr がファイルに書かれず、stdin 非耐久 → **Q36_STARTUP / pin-pool 未捕捉**。  
   - strata のみ abort（Hermes 生存）。その後 free ~5.4 GiB に戻らず BLOCKED。  
   - 証跡: `run-18-14/abort-note.txt`, `NOTES-18-21.md`。

3. **durable launcher 経路**  
   - 正式入口:  
     `py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py`  
   - ゲート失敗時 exit **4**（BLOCKED）。Hermes を殺さない。  
   - **作業ツリー上、同スクリプトに未コミット改修あり**（PIPE+tee → OS ファイルリダイレクト＋stdin babysitter。18:14 再発防止）。subagent 作業の途中成果の可能性。次担当は diff を読んでから実行すること。

4. **製品 `.5` とローカル unsigned の差**  
   - 製品出荷 digest 系は旧 `6fe11065…`。ローカル allowlist 済み新 digest は `64226fde…`。次 NSIS に乗せるのは任意で、**live 成功後**が妥当。

---

## 5. 次の担当者がやること（優先順）

1. **`nvidia-smi`** で専用 VRAM free を確認。目安 **≥ 12000 MiB**（ランチャー既定）。Hermes / 他推論が残っていれば **待つかユーザー判断**。kill しない。
2. free が足りたら、**現行（または修正済み）durable launcher** を実行:  
   `py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py`  
   - EXE digest が `64226fde…` であること。  
   - argv 想定: `--native …UD-Q4_K_XL.gguf --max-context 65536 --prefill auto --mtp 2 --q36-expert-store mapped-pack --serve`
3. 証跡ディレクトリに **`Q36_STARTUP`** 行と **`mapped-pack host pin pool` / ExpertPinPool** 行をファイルで残す。無ければ成功扱いにしない。
4. **T03** chat → stop → restart（同一実効設定）。GUI refuse 経路は既に PARTIAL 済みなので、serve 成立後の停止所有権が主。
5. **T04–T08** は paired のみ。数値の発明禁止。paired なしで既定化しない。T08 は任意。
6. （任意）準備が整ったら次インストーラに `64226fde…` を載せる。GitHub latest を勝手に差し替えない想定なら **`--latest=false`** 等の既存出荷手順に従う。署名済み `b5e4d525…` を上書きしない。
7. **Goal を complete にしない**（本引き継ぎ時点）。

---

## 6. 触ってよい / 触るな

### 触ってよい

- `_docs/q36-32gb16gb/evidence-*` への新規証跡追加（NOTES / nvidia-smi / launch-meta）。
- 未署名 q36 component パス（`…\engine\0.4.0-q36-windows-x86_64-cuda-cuda13\`）の検証・再測定。
- Host / docs / allowlist の正直な更新（偽速度なし）。
- durable launcher のログ耐久性修正（DESIGN #6 を壊さない範囲）。
- H: 上の作業用 cache / build（C: 逼迫時）。モデル原本は動かさない。

### 触るな

- **署名済み** `0.4.0-windows-x86_64-cuda-cuda13\strata.exe`（`b5e4d525…`）の置換・改ざん・偽署名。
- **モデル / `.q36epk` / GGUF** の無断移動・再取得・上書き・再量子化。
- **force push** / main への無審査破壊的履歴改変。
- **`_docs/intake/`** を本作業のコミットに混ぜない（個人 path 等）。
- **`_docs/2026-11-02_qwen36-engine-died-host-experts{Cursor}.md`** を不用意にコミットしない（指示どおり skip）。
- Hermes / 他アプリ推論 server の **無断 kill**（DESIGN #6）。
- paired なしの速度数字・既定化・完了宣言。

---

## 7. コマンド・パス・ハッシュ早見表

| 用途 | 値 |
|---|---|
| 作業根 | `C:\Users\downl\Documents\ChatGPT\Strata` |
| DESIGN | `_docs/q36-32gb16gb/DESIGN.md` |
| 実装計画 | `_docs/q36-32gb16gb/Strata_Qwen36_Implementation_Plan_2026-11-02.md` |
| 証跡集約 | `_docs/q36-32gb16gb/evidence-summary.json` |
| durable launch | `py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py` |
| 未署名 EXE（想定） | `%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-windows-x86_64-cuda-cuda13\strata.exe` |
| 未署名 SHA-256 | `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7` |
| 署名 EXE（触るな） | `%LOCALAPPDATA%\Strata\components\engine\0.4.0-windows-x86_64-cuda-cuda13\strata.exe` |
| 署名 SHA-256 | `b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1` |
| 旧未署名（bak） | `6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29` |
| GGUF（論理） | `H:\Strata\models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` |
| 製品版 | `0.4.0-preview.20261103.5` |
| GPU | NVIDIA GeForce RTX 5060 Ti（専用 ~16311 MiB） |
| ゲート下限 | free VRAM **12000 MiB**（ランチャー既定） |
| VRAM 確認 | `nvidia-smi` / `nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv` |
| Host q36 tests | 以前 `19/19 PASS`（`host-q36-node-tests-04-08.txt`；再実行時は npm-cache を C:/H: に注意） |

期待 stderr マーカー（速度主張ではない）:

```text
Q36_STARTUP …
strata-q36: mapped-pack host pin pool … MiB x2
```

---

## 8. 未コミットの列挙（本引き継ぎ作成時点の正直な git status）

`git status`（要約）。**dirty。** subagent の durable launcher 改修が途中の可能性あり。

### 変更あり（tracked）

- `M _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py`  
  — 大規模差分（+223/-100 前後）。OS ファイルへ stdout/stderr、stdin babysitter、マーカー検出強化。**コミット判断は次担当 or 別レビュー。本引き継ぎでは混ぜない想定も可。**

### 未追跡（代表）

- `_docs/2026-11-02_qwen36-engine-died-host-experts{Cursor}.md` ← **コミット skip**
- `_docs/intake/` ← **コミット skip**
- `_docs/q36-32gb16gb/evidence-2026-11-04-gui/` 配下の一部 JSON（複数）
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/nvidia-smi-*-18-24.*`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/ram-recheck-18-24.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-18-27-gate/`

本ファイル `_docs/2026-11-04_qwen36-handover-plan{Cursor}.md` は引き継ぎとして **単独コミット推奨**（intake / engine-died / 未レビュー launcher 改修を混ぜない）。

---

## 9. 引き継ぎチェックリスト（受領時）

- [ ] DESIGN #1–#10 を再読した
- [ ] `nvidia-smi` で free VRAM と PID 14572（または後継）の有無を確認した
- [ ] `launch_mapped_live_durable.py` の未コミット diff を読んだ
- [ ] EXE `Get-FileHash` が `64226fde…` であることを確認した
- [ ] 署名 `b5e4d525…` を触らないと約束した
- [ ] Goal complete / 偽速度を出さないと約束した

---

## 変更対象（本ドキュメント作成）

| ファイル | 内容 |
|---|---|
| `_docs/2026-11-04_qwen36-handover-plan{Cursor}.md` | 本引き継ぎ計画書 |

**実行コマンド:** `git status` / `git log` / 証跡 Read。GPU live は未実行（ブロック継続のため）。  
**検証:** 証跡ファイルと `evidence-summary.json` の突合のみ。新ベンチなし。  
**残留リスク:** durable launcher 未コミット差分の完成度未レビュー；Hermes VRAM 継続；18:14 相当のログ喪失再発（修正版未検証）。  
**次アクション:** §5 優先順。
