# Strata公式 Qwen3.6 実装の「詰め甘さ」監査

- 日時: 2026-11-04T21:59:20+09:00
- 実装AI: Cursor
- 目的: ユーザー指摘「Strata公式の実装が詰めが甘い」への証跡付き判定
- Goal complete: **false**（UpdateGoal complete しない）
- 偽速度: **なし**

## 結論（3層）

| 層 | 判定 |
|---|---|
| **(A) Upstream Strata（Niko1221）公式 Q36** | **甘い。同意。** 起動後失敗・未知フラグwarn+skip・STOPがプロセス終了しない・32GB表記の楽観・mapped-pack未合意 |
| **(B) この Hakua fork** | 契約・拒否・観測で穴は塞いだ。だが **STOP寿命・paired速度・unsigned allowlist・出荷とlive証明のずれ** はまだ甘い |
| **(C) 16GB VRAM + 32GB RAM 現実** | hybrid必須。host experts ~18.75 GiB。pack構築中に RAM thrash（avail ~0.2–0.7 GiB）。「快適」ではない |

Alibaba/HF 公式カードは本監査の主対象外（ユーザー明確化済み）。参考: HFは default ctx 262144・thinkingは ≥128K 推奨・OOMなら短縮、であり **16GB/32GBレシピは出していない**（2026-11-04 確認: https://huggingface.co/Qwen/Qwen3.6-35B-A3B ）。

---

## (A) Upstream / 継承パスで甘い具体点

### 1. serve で未知フラグを warn+skip → 「設定できた」見え

`src/qwen35/q36_engine.cu`（serve 分岐）:

```text
serve_mode && a.rfind("--", 0) == 0
→ "ignoring … (not an option of this engine)" して continue（fatal にしない）
```

`apps/host/server/q36-run-contract.mjs` 冒頭コメントがそのまま指摘:

> A skipped flag still looks like a successful setting in the UI.

上流 issue: https://github.com/Niko1221/Strata/issues/5023 （OPEN, 2026-11-02）  
`[Engine] Qwen3.6: refuse --cache-type-* and a hand-written --vram-reserve-mib before start`

### 2. 全 expert host arena をプロセス起動**後**に確保失敗

legacy hybrid は `cudaHostAlloc` → `malloc` → 失敗時 `no host memory for the experts (<MiB>)`。  
上流 issue: https://github.com/Niko1221/Strata/issues/5021 （OPEN）  
実ログ例: `strata-q36: no host memory for the experts (19195 MiB)`  
歴史証跡: `evidence-summary.json` — host_allocation_failure **14** / engine_start **22**。

### 3. `STOP` は生成停止フラグ。プロセス終了ではない

`q36_engine.cu` `run()`:

```text
if (l == "STOP") { stop.store(true); continue; }
```

EOF で reader が終わり、active=0 で return。  
証跡: `_docs/2026-11-03_qwen36-mapped-pack-stop-restart{Cursor}.md` — STOP 後もプロセス生存、stdin 閉じて exit 0。  
本機 T03: `run-21-05-t03/t03-report.json` → **`FAIL_STOP1_STILL_ALIVE`**（exit_code null、VRAM ほぼ満杯のまま）。

### 4. docs の「RAM setup plans for 32 GB」は条件の甘さが出やすい

`docs/MODELS.md` UD-Q4_K_XL: file 22.9 GB / **RAM 32 GB**。  
測定表は R9700 **32GB VRAM** と RTX 3060 **12GB hybrid**。  
16GB カード + 32GB RAM での thrash・10分級初期化・他 server 同居は「計画値」としては甘い。

### 5. mapped-pack は上流で範囲合意前

issue #5022 OPEN: opt-in mapped expert pack の scope 合意前に PR しない。  
公式製品経路の本線は依然 **legacy arena**。

### 6. 既定と観測のズレ

- エンジン既定 context 例: contract の `Q36_ENGINE_DEFAULT_CONTEXT = 32768`、本線比較は 65536。
- `--help` に `--q36-expert-store` が欠ける binary があり得た（fork で help-honesty rebuild `64226fde…`）。
- Upstream/製品 docs は decode 数値を出す一方、起動 wall / first useful token の厳格ペアは薄い。

---

## (B) Fork が塞いだ穴

| 穴 | 塞ぎ | 証跡 |
|---|---|---|
| private-cache を剥がして起動成功に見せる | fail-closed refuse | `q36-run-contract.mjs` / test `a private-cache demand is refused` / GUI `7f9be950` |
| mutated retry | 抑止 | `q36-load-lifecycle.test.mjs`、handover T03 GUI PARTIAL |
| 未知 engine へ mapped-pack 投げて legacy に落ちる | digest allowlist | `Q36_MAPPED_PACK_DIGESTS` |
| 起動観測なし | `Q36_STARTUP` stages | NOTES-21-05 / `run-21-05/markers.json` |
| 全量 pin / 巨大 arena | opt-in mapped-pack + pin-pool 2×32 MiB | pin-pool 行捕捉済（21:05） |
| 偽速度で完了 | invented_speeds: false / goal_complete: false | `evidence-summary.json`、`HAKUA_RELEASE.md`「Startup time and token speed were not measured」 |
| 上流への問題提起 | #5021 #5022 #5023 | `_docs/2026-11-03_upstream-qwen36-three-issues{Grok}.md` |

21:05 live（VRAM 空いた後）:

- pin-pool: `cudaHostAlloc 32 MiB x2`
- READY 65536
- expert_host_alloc ~1116 s（まだ速いとは言わない）
- T03 STOP: **FAIL_STOP1_STILL_ALIVE**

---

## (C) ハード現実（16GB/32GB）

- 16GB では全 expert 非収まり → hybrid（41/256 slots ≈ 3 GiB GPU + 18.75 GiB host）。
- 32GB RAM は OS + WS + mapped pack 検証とギリギリ。NOTES-21-05: pack/map 中 avail **0.2–0.7 GiB**。
- 他推論（Hermes）同居で mapped-live は何度も BLOCKED（DESIGN #6 で無断 kill 禁止）。
- → 「動く」と「製品として詰め切った」は別。公式が 32GB 計画と書くのは、(C) を甘く読ませやすい。

---

## まだ甘い穴（fork 側・残作業）

1. **STOP → プロセス終了** が製品契約として未定義／未合格（T03 FAIL）。
2. **T04/T06/T07 paired 速度 NOT_RUN** — mapped-pack を速いと言えない。
3. **unsigned digest allowlist**（ローカル `64226fde…`）と製品 `.5` digest 差。
4. **evidence-summary.json** が 20:56 BLOCKED のままで、21:05 READY とずれうる（集約更新遅れ＝運用の甘さ）。
5. legacy 既定のままでは 32GB 機で host alloc 失敗パターンが再発しうる。

「甘くない」にする条件（DESIGN §6）:

- chat → STOP（所有権どおり終了）→ 同一設定 restart 合格
- Q36_STARTUP + pin-pool 証跡を安定再現
- paired ≥5 で速度主張するか、主張しないまま opt-in と明記
- 未知フラグ／private-cache は全経路 fail-closed
- 署名経路と allowlist の一致、または unsigned を製品主張から外す

---

## なんJ一行

Strata公式のQ36は「動くデモ」寄りで詰め甘い、うちは拒否と観測でかなり締めた、でも STOP寿命と速度ペアが残ってるからまだ完了じゃねえ。

## 変更対象

| ファイル | 内容 |
|---|---|
| `_docs/2026-11-04_strata-official-q36-softness-audit{Cursor}.md` | 本監査 |

## 検証

証跡 Read / `gh issue view` 5021–5023 OPEN / HF card 2026-11-04。新ベンチなし。
