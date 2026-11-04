# Q36 → Codex 引き継ぎ計画書

作成: 2026-11-04T23:02+09:00（Cursor）  
作業根: `C:\Users\downl\Documents\ChatGPT\Strata`  
remote: `origin` = https://github.com/zapabob/Strata.git ；`upstream` = https://github.com/Niko1221/Strata.git  
Goal complete: **false**（`UpdateGoal complete` しない / 完了宣言しない）

> なんJ要約（1段落のみ）: mapped-live READY と pin-pool ログ取れて T03（chat→STOP+EOF→restart）まで PASS した。製品 `.5` 出荷済み・未署名 `64226fde…` で回してる。残仕事は T04–T08 の paired 速度と、任意の次インストーラ（help 正直化 digest）、upstream 向け STOP-only-without-EOF 契約整理と PR-2 docs。Hermes は殺すな。数字捏造するな。ゴールまだ閉じてない。

旧引き継ぎ（BLOCKED 時点）: `_docs/2026-11-04_qwen36-handover-plan{Cursor}.md` — **本ファイルが Codex 受領の正本**。

---

## 1. Goal / completion criteria

### Goal

RAM ~32GB / RTX 5060 Ti 16GB で、同一 **Qwen3.6-35B-A3B UD-Q4_K_XL** を継続利用できる経路を整え、DESIGN / 実装計画の T00–T09 を正直な証跡で閉じる。主比較: context **65536**、同一 GGUF / tokenizer、FP32 KV、**MTP=2**、実効 prefill **2048**。

### Completion criteria（未達 — まだ Goal complete にしない）

DESIGN §6 / 計画書どおり、少なくとも次が揃うまで完了宣言しない:

1. Windows GPU で mapped-pack live が成立し、stderr に **`Q36_STARTUP`** と **pin-pool** 行がファイル証跡として残る → **達成**（`NOTES-21-05.md` / `run-21-05/`）。
2. **T03** chat → stop → restart が同一実効設定で通る → **達成**（`run-21-05-t03/`、`t03-report.json` result=PASS）。ただし STOP 単独では serve が残るため **stdin EOF 必須**（契約メモは Remaining）。
3. **T04 / T06 / T07 / T08** は paired 実測のみ。数の捏造禁止。paired なしでの既定化禁止 → **未達**。
4. 機能・隔離・品質ゲート合格後の主性能目標（提案）は「起動要求→最初の有用 token 中央値 30% 以上短縮」かつ初回・継続 decode 中央値を 5% 超悪化させないこと。**達成済み数値ではない。**
5. DESIGN 非交渉契約（特に #6 他推論 server 無断 kill 禁止、#10 署名迂回・配布手動上書き禁止）を破らない。

正本:

- `_docs/q36-32gb16gb/DESIGN.md`
- `_docs/q36-32gb16gb/Strata_Qwen36_Implementation_Plan_2026-11-02.md`
- `_docs/q36-32gb16gb/evidence-summary.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-21-05.md`

---

## 2. Current HEAD / remote sync

本ファイルコミット直前の観測（Cursor クリーンアップ時点）:

| 項目 | 値 |
|---|---|
| branch | `main` |
| HEAD (pre-handover commit) | `8824ec217643c4b3ad74fd170185a8eb884ba6e4` |
| tip message | `[Docs] sync launch2 READY pass stderr/stdout txt evidence` |
| vs `origin/main` | up to date（本引き継ぎコミット前） |
| intentional leftovers (skip) | `_docs/intake/` ；`_docs/2026-11-02_qwen36-engine-died-host-experts{Cursor}.md` |
| secrets / `.env` | コミット対象外 |

Codex 受領時は必ず:

```powershell
cd C:\Users\downl\Documents\ChatGPT\Strata
git fetch origin
git status -sb
git log -5 --oneline
git rev-parse HEAD
```

本ドキュメントを含むコミット SHA は push 後の `git log -1` を正とする。

---

## 3. Done

| 項目 | 状態 | 証跡 / 参照 |
|---|---|---|
| 製品 installer **`.5`** | 出荷済 | `0.4.0-preview.20261103.5` / `docs/HAKUA_RELEASE.md` |
| 未署名 q36 engine | digest **`64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`**（help 正直化含む） | `NOTES-05-22-rebuild.md`, allowlist |
| 署名済み engine | **`b5e4d525…` 非接触** | `evidence-summary.json` |
| mapped-live READY + pin-pool | **PASS**（21:28+09:00） | `run-21-05/`, pin-pool `cudaHostAlloc 32 MiB x2` |
| T03 chat → STOP+EOF → restart | **PASS**（22:53:50+09:00） | `run-21-05-t03/t03-report.json`, `t03-final-status.json`；launch2 pid **37524** |
| Host q36 node tests | 19/19 PASS（再実行時は npm-cache 注意） | `host-q36-node-tests-04-08.txt` |
| T03 GUI private-cache refuse | PARTIAL（強制解除なし） | `evidence-2026-11-04-gui/` |
| Upstream **PR-1** | Open | https://github.com/Niko1221/Strata/pull/5216 |
| Softness audit / PR plan | 文書化済 | `_docs/2026-11-04_strata-official-q36-softness-audit{Cursor}.md` ；`_docs/2026-11-04_q36-upstream-pr-plan{Cursor}.md` ；`_docs/2026-11-04_q36-upstream-pr1-refuse-flags{Cursor}.md` |
| durable launcher | コミット済・live 検証済 | `launch_mapped_live_durable.py` |
| orphan cleanup helper | あり | `cleanup_orphans.ps1`（**Hermes 対象外**） |
| invented speeds | **false** | 全 NOTES / evidence-summary |
| Hermes killed | **false** | DESIGN #6 |

### T00–T09 snapshot（正直ラベル）

| Task | 状態 | 短い根拠 |
|---|---|---|
| **T00** | DONE | 計画パッケージ＋ binding 証跡 |
| **T01** | DONE | Host 契約 / refuse；node 19/19 |
| **T02** | DONE（live 捕捉） | `Q36_STARTUP` stages in `run-21-05/` |
| **T03** | PASS（serve 経路） | chat/stop+EOF/restart；GUI refuse は PARTIAL のまま |
| **T04** | NOT_RUN | paired warmup 費用移動検出なし |
| **T05** | PARTIAL→live 証明済 | mapped-pack+pin-pool 実装＋GPU ログ；製品 `.5` は旧 digest 系のまま |
| **T06** | NOT_RUN | paired 転送最適化なし |
| **T07** | NOT_RUN | paired CUDA hotspot なし |
| **T08** | NOT_RUN（任意） | FP16 KV 等・本線必須外 |
| **T09** | PARTIAL | `.5` 出荷；`64226fde…` 次インストーラ未；E2E/配布閉じは未完 |

`evidence-summary.json` ラベル: `PARTIAL_IMPL_MAPPED_LIVE_READY_T03_PASS_SPEED_NOT_RUN` / `goal_complete: false`。

---

## 4. Remaining（Codex の主戦場）

1. **T04 / T06 / T07 / T08 paired speeds**  
   - 同一条件の paired run のみ。DONE 行の tok/s を T04 合格に読み替えない。  
   - T08 は任意。混ぜない。

2. **（任意）次インストーラ**  
   - help-honesty digest **`64226fde…`** を製品に載せる。  
   - 署名 `b5e4d525…` を触らない。GitHub latest 勝手差し替え禁止。既存出荷手順（`--latest=false` 等）に従う。

3. **Upstream 契約メモ: STOP-only-without-EOF**  
   - 観測: idle serve は `STOP` だけではプロセス残留；**stdin EOF** が必要（`t03-final-status.json` `stop_note`）。  
   - upstream へ出すなら「製品契約として文書化 / または挙動修正」を小さな PR に分ける。現状は fork 証跡。偽主張禁止。

4. **Upstream PR-2（docs）**  
   - PR plan どおり PR-1（#5216）の後。  
   - 候補: `docs/MODELS.md` の Qwen3.6 / 32GB RAM honesty。  
   - Hakua-only（private-cache、digest allowlist、mapped-pack 本体）を混ぜない。

5. **Goal を complete にしない**（本引き継ぎ時点）。

---

## 5. Hardware / ops constraints

| 項目 | 値 |
|---|---|
| GPU | NVIDIA GeForce RTX **5060 Ti 16GB**（専用 ~16311 MiB） |
| RAM | ~**32 GB**（観測 total ~31.87 GB） |
| OS | Windows 11 |
| Python | `py -3` |
| durable launcher ゲート | free VRAM **≥ 12000 MiB**（既定） |
| cleanup | `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/cleanup_orphans.ps1` — **所有確認済みの stray strata / babysitter のみ** |
| DESIGN #6 | **Hermes / 他アプリ推論 server を殺すな**（PID だけ見て雑殺禁止） |

VRAM が足りなければ待つ。ユーザーが Hermes を止めるか自然終了を待つ。`cleanup_orphans.ps1` で Hermes を狙わない。

---

## 6. Commands cheat sheet

```powershell
# status / sync
cd C:\Users\downl\Documents\ChatGPT\Strata
git status -sb
git fetch origin ; git log -5 --oneline
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv

# digest check (unsigned q36)
Get-FileHash "$env:LOCALAPPDATA\Strata\components\engine\0.4.0-q36-windows-x86_64-cuda-cuda13\strata.exe" -Algorithm SHA256

# durable mapped-live (GO only if free VRAM enough)
py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py --out-dir _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-<HH-mm>

# T03 (existing harness; prefer after clean VRAM)
py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/t03_chat_stop_restart.py

# owned orphan cleanup ONLY (never Hermes)
powershell -File _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/cleanup_orphans.ps1
```

期待 argv（概念）: `--native …UD-Q4_K_XL.gguf --max-context 65536 --prefill auto --mtp 2 --q36-expert-store mapped-pack --serve`

STOP 後にプロセスを終えるときは **stdin EOF** を忘れない（T03 スクリプト修正済み）。

---

## 7. Do / Don't for Codex

### Do

- DESIGN #1–#10 と本ファイル・`NOTES-21-05.md` を最初に読む。
- 新規証跡は `_docs/q36-32gb16gb/evidence-*` に NOTES / JSON / nvidia-smi CSV で残す。
- paired 速度は同一条件・同一 digest・再現可能な手順で。
- upstream 作業は `upstream/main` から綺麗な枝を切る。Hakua-only を混ぜない。
- 実装ログを `_docs/yyyy-mm-dd_機能名{Codex}.md` に残す。
- PowerShell は `;` 区切り。Python は `py -3`。UV 管理なら既存プロジェクト規約に従う。

### Don't

- **`UpdateGoal complete` / 完了宣言**（T04–T08 と DESIGN 閉じ前）。
- **偽速度・未実行 PASS**。
- **Hermes / 他推論 server の無断 kill**（DESIGN #6）。
- **署名済み** `b5e4d525…` の置換・改ざん。
- **モデル / `.q36epk` / GGUF** の無断移動・上書き・再量子化。
- **force push**。
- **`_docs/intake/`** と **`_docs/2026-11-02_qwen36-engine-died-host-experts{Cursor}.md`** をコミットに混ぜる。
- secrets / `.env` をコミット。
- STOP-only で「プロセス必ず終了」と upstream に偽主張。
- mapped-pack 本体を PR-1 系に便乗させて上流へ流す。

---

## 8. Key evidence paths (`_docs/q36-32gb16gb/`)

| Path | Why |
|---|---|
| `DESIGN.md` | 非交渉契約・成功定義 |
| `Strata_Qwen36_Implementation_Plan_2026-11-02.md` | T00–T09 |
| `PACKAGE_README.md` | パッケージ入口 |
| `evidence-summary.json` | セッション横断ステータス（`goal_complete: false`） |
| `evidence-2026-11-04-mapped-live/NOTES-21-05.md` | **最新成功ノート** |
| `evidence-2026-11-04-mapped-live/run-21-05/` | READY + Q36_STARTUP + pin-pool |
| `evidence-2026-11-04-mapped-live/run-21-05-t03/` | T03 PASS（report / final-status / launch2 ready-pass txt） |
| `evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py` | durable launcher |
| `evidence-2026-11-04-mapped-live/cleanup_orphans.ps1` | owned orphan 掃除 |
| `evidence-2026-11-04-mapped-live/t03_chat_stop_restart.py` | T03 harness |
| `evidence-2026-11-04-gui/` | private-cache refuse UI |
| `evidence-2026-11-04-mapped-live/NOTES-05-22-rebuild.md` | `64226fde…` rebuild |
| repo `_docs/2026-11-04_strata-official-q36-softness-audit{Cursor}.md` | softness audit |
| repo `_docs/2026-11-04_q36-upstream-pr-plan{Cursor}.md` | upstream PR plan |
| repo `_docs/2026-11-04_q36-upstream-pr1-refuse-flags{Cursor}.md` | PR-1 記録 → https://github.com/Niko1221/Strata/pull/5216 |

---

## 9. Codex receive checklist

- [ ] DESIGN #1–#10 を再読した
- [ ] `git fetch` / `git status` / HEAD を確認した
- [ ] `nvidia-smi` で free VRAM と他推論 PID を確認した（Hermes 殺さない）
- [ ] EXE `Get-FileHash` が `64226fde…` であることを確認した
- [ ] 署名 `b5e4d525…` を触らないと約束した
- [ ] T04–T08 は paired のみ・偽速度なしと約束した
- [ ] Goal complete にしないと約束した
- [ ] upstream 作業時は Hakua-only を混ぜないと約束した

---

## Meta (this handover document)

| 項目 | 内容 |
|---|---|
| ファイル | `_docs/2026-11-04_qwen36-codex-handover-plan{Cursor}.md` |
| 作者 | Cursor（クリーン worktree → commit → push 依頼に応じた引き継ぎ） |
| 検証 | 既存証跡・`evidence-summary.json`・`NOTES-21-05`・git log 突合のみ。新ベンチなし |
| 残留リスク | T04–T08 未測；製品 `.5` と local `64226fde…` の差；STOP/EOF 契約の upstream 未整理；VRAM 再占有時は再ゲート |
| 次アクション | §4 Remaining |
