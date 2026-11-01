# Strata 16GB VRAM高効率化・高速化 実装計画書

- 作成日: 2026-11-02 (JST)
- 対象リポジトリ: `zapabob/Strata`（公式: `Niko1221/Strata`）
- 実装担当: Cursor / Codex（段階的TDD、個別PR）
- 状態: **IMPLEMENTATION PLAN / NOT IMPLEMENTED**
- 主対象: Windows 11 / RTX 5060 Ti 16GB / Ryzen 5 4600系 / RAM 32GB / A520M-HDV（実機構成は開始時に再検証）
- 優先ワークロード: Hikari `Hikari-LoRA-fixed-scale-PQ2_0.gguf`（PrismML）、Hakuaローカルチャット、Strata native MoE。TurboQuantは独立バックエンドとして回帰を保護する。

## 0. Executive decision

**狙いはVRAM使用率の最大化ではなく、同じモデル・精度・context・安全性のもとで、GPU内で完結する仕事を増やしTTFT / prefill / decodeを改善すること。**

以下の6ワークストリームを、基準計測→正確な見積もり→正規化実行計画→GPU自動配置→Hakuaの安全なprefix再利用→nativeの観測ベース調整、の順で実装する。高速化の倍率は未実測であり、実機計測後に採否を判定する。

### 固定ベースライン（実装直前に必ず再確認）

| 項目 | レビュー時点で固定した値 |
| --- | --- |
| fork HEAD | `b52a198300f11437b1ed2d2cc373aa73f60ea055` |
| upstream HEAD | `c62d5e3a15b40ea51c96aae9e8d36928965f53ab` |
| PrismML source | `73bfe6cc485554822f80c473a3c0c4f25e80f41b` |
| Hikari model revision | `c42fdf9debd1ba8daf4ac171d81b2052f841058f` |
| Host Node requirement | `>=24.22.2` |
| 過去の限定テスト | Linux Node 24.22.1で29成功。Windows GPU/131kの合格証明ではない |

実装開始時は `git status --short` / `git remote -v` / `git rev-parse HEAD` / `git fetch` を実行し、**その時点のmain SHAとbackend binary SHA256を別途記録する**。この文書のSHAを「最新」と仮定しない。上流mainの追加変更があれば、差分を監査してから作業ブランチを切る。既存mainと配布物を直接書き換えない。

## 1. 非交渉の不変条件

1. **既存の独自機能を保存**: Hakuaの記憶・同意UI、PrismML/PQ2_0、TurboQuant、Spin8/Triality研究コード、Windows native・NSIS、既存agent・cancelを無断で削除しない。現在非対応の組合せを、動くと偽装しない。
2. **モデル品質・精度の固定**: baseline armではモデルrevision、tokenizer、K/V精度（HikariはまずQ8_0/Q8_0）、Flash Attention、context capacity、seed・temperatureを固定する。Q4_0 KVなどは別の品質評価armとする。
3. **131,072 capacityを保持**: 131k検証の途中でcontext=32kや64kへ黙って縮めない。`--ctx-size`/`--max-context`等の実効値をbackendの起動ログで照合し、失敗は失敗として報告する。
4. **私的記憶の境界を破らない**: principal/session/consent/model/token prefixが異なる場合は再利用禁止。ディスクへの無断保存、異なる会話のprefill state共有、ユーザーの秘密をログに残すことを禁止する。
5. **起動前の予測と実配分を区別**: モデルファイル容量≠GPU重み容量、理論KV≠実際の確保量、Windows shared memory≠専用VRAM。
6. **fail closed / rollback**: VRAM測定・backend能力が不明なら従来設定を維持し、推定値を根拠に危険な強制配置をしない。各変更はフラグで無効化できる。
7. **ユーザー環境を保護**: 他ツール所有のllama-server/Hermes/LM Studioを無断停止しない。モデルファイルを移動・再量子化しない。リリース・push・merge・設定書換えは実装作業の承認範囲を確認して実施する。

## 2. 問題と到達目標

### 2.1 根拠のある現状

- `apps/host/server/local-models.mjs` は `layers * kvHeads * (keyLength + valueLength) / 1024` でKV見積もりを作る。Hikariは64ブロックのうちFull Attentionが16、recurrentが48であるのに、通常attention KVを64層分として数えてしまう。
- `apps/host/src/lib/experience.ts` のKV見積もり・`configKey` は主にlegacy `ctx.kvMode` を用い、`ctx.kType` / `ctx.vType` / backend差を十分反映しない。
- `apps/host/server/supervisor.mjs` の外部backend `Automatic` / `All layers` はHostからともに `-ngl 999` を渡す。Host自身の空きVRAM最適化ではない（llama-server内部fitは別）。batch=2048時のubatchは512で、現在はbatchに連動する。
- Hakua native private modeは `--prompt-cache 0` / `--conversation-cache-mib 0` を設定し、Python guardも0を要求する。これはprivacyの意図ある契約であり、単純にフラグを外すのは不可。
- 0.4.0の「expert cache=512 / prefill=32 / 4K」の確認記録は**機能確認用**。最速・通常の設定だと解釈してはいけない。

### 2.2 Hikari容量の基準ベクトル

固定されたGGUFメタデータ: `qwen35.block_count=64`, `qwen35.full_attention_interval=4`, K/V head=4, K/V head dimension=256, `context_length=262144`。要件の131072はモデル最大値ではなく、今回評価する**指定context**。

- 通常Full Attention層: 16、recurrent層: 48。
- Attention KV（131072 token、単一sequence、Q8_0/Q8_0、32要素34 byte）= **4.25 GiB**。
- Attention KV（Q4_0/Q4_0、32要素18 byte）= **2.25 GiB**。
- Attention KV（FP16/FP16）= **8.00 GiB**。
- モデルファイルサイズ = 7,206,168,928 bytes ≈ **6.711 GiB**（GPU weights確保量ではない）。
- Q8_0 Attention KV＋ファイルサイズの単純小計 ≈ **10.961 GiB**。recurrent state、CUDA、graph、workspace、VRAM reserve、fragmentationなどは**別途加算**。

数式（層ごとのhead widthや量子化block paddingが異なるモデルには、その層ごとの値を使う）：

```text
attention_kv_bytes(ctx, sequences, formatK, formatV)
 = ctx * sequences * Σ(attention layer l) [
     row_bytes(formatK, n_kv_heads[l] * k_head_dim[l])
   + row_bytes(formatV, n_kv_heads[l] * v_head_dim[l])
   ]
```

ここで `row_bytes` は`GGML`のブロック形式・行paddingに従い、単純な「INT8=1byte」を使わない。実際のKV容量のalloc granularity、recurrent stateは別に計算し、backendログの実測で較正する。

### 2.3 計測で到達すべき状態

- 起動前の予測に「モデル、Attention KV、recurrent、graph/workspace、reserve、不明分」を別々に示せる。
- `Automatic` はVRAM観測に基づく**理由付き配置提案**を返し、ユーザーが指定したcontextと精度は変更しない。
- GUI、server、native/externalの実起動引数が同じ正規化 `RunPlan` に対応する。
- 頻繁なCPU→GPU転送、shared memoryスピル、重複モデルロードが可視化される。
- Hakuaは既定のprivacy挙動を維持したまま、厳密な同一sessionの新規入力に限ってprefix再利用を有効化できる（後段の独立PR）。

## 3. 実装単位・依存順序

| PR | 優先 | 主題 | 前提 | 完了条件 |
| --- | --- | --- | --- | --- |
| PR-A | P0 | 基準状態固定・診断・測定器 | なし | 実効argv、GPU/CPU/共有メモリー、cache policy、版情報を一つの診断IDで保存 |
| PR-B | P1 | GGUF hybrid memory estimator | PR-A推奨 | Hikari 16/48分離、131072 Q8_0 KV=4.25GiBを検証 |
| PR-C | P1 | `RunPlan`／GUI・server統一 | PR-B | `kType/vType`とbackend差がUI・argv・測定identityへ必ず反映 |
| PR-D | P2 | 16GB向けAutomatic GPU placement | PR-C | 余白付き計画、実load内訳照合、context/精度無断変更なし |
| PR-E | P2 | Hakua session-local private prefix cache | PR-A/PR-C、セキュリティ設計承認 | 原則不共有、会話継続は速く、consent/取消/要約時は正確に無効化 |
| PR-F | P3 | native expert/prefill autotuneと長文QA | PR-A, PR-Dの結果 | native設定とCPU/SSD待ちの実測で採否判定 |
| PR-G | P4（任意） | Spin8/Triality/TurboQuant等の研究系最適化 | 主経路の安定化 | 実行経路に接続し、同条件の速度・品質を再現して初めて採用 |

PRを跨ぐ一括巨大リファクタは禁止。各PRは新規テスト→最小実装→統合テスト→実測→監査→独立ロールバックの順で進める。前のPRが未検証でも、次段階の設計・テスト作成は可能。ただし配布は段階ごとに判定する。

## 4. PR-A: 実効設定・実確保量の測定器

**変更候補**: `apps/host/server/supervisor.mjs`, `engine.mjs`, `native-control.mjs`, `native-resources.mjs`, `apps/host/src/lib/experience.ts`, `apps/host/tests/`、必要に応じ `bench/strata-16gb/`（新規）。

**タスク**
1. `RunObservation` のJSON schemaを導入し、起動前 `requested` とload後 `effective` を分離。backend種類、backend executable SHA256/版、モデル識別、GGUF metadata signature、context、K/V、`-ngl`、実offload数、batch/ubatch、parallel、Flash Attention、expert cache、memory mode、policy revisionを記録する。
2. NVML / `nvidia-smi` / Windows取得可能APIを使い、`dedicated_vram_total/free/used` とWindows `shared_gpu_memory` を**別フィールド**にする。値が取得できない場合は`null`と観測元・時刻を記録し、0に偽装しない。
3. backend起動ログからweights/KV/recurrent/computeのGPU割当、実offload数、effective context、OOMを抽出。ログ形式が未対応なら`unknown`とし、推測値で置き換えない。
4. process名・PID・所有者を記録し、HermesやLM Studioなどの別プロセス占有を可視化する。ただし自動killしない。
5. 記憶内容、prompt生文、API key、フルパスを性能テレメトリーに含めない。診断の識別子は秘密ではない内容のハッシュと限定メタデータにする。

**テスト**: measurementが欠損／高負荷／複数GPU／OOM／cancel／起動中終了時に壊れない。`requested.context=131072`に対し、`effective.context`が小さければ失敗扱い／非比較として明示。

**受入**: Windows 5060Ti実機で少なくとも4K/32Kの起動・処理について、`RunObservation`が採取でき、専用VRAMと共有GPUメモリーを混同しない。

## 5. PR-B: architecture-aware memory model

**変更候補**: `apps/host/server/local-models.mjs`, `gguf.mjs`, `catalog.mjs`, `kv-settings.mjs`, `apps/host/tests/local-models.test.mjs`, **新規** `apps/host/server/model-memory.mjs`、`apps/host/tests/model-memory.test.mjs`。

**設計**

- Import時のGGUF metadataから `n_layer_all`, `n_full_attention`, `n_recurrent`, `n_kv_heads`, `k/v head_dim`, `context_limit`, `ssm dimensions`, `metadataSignature` を読み、バリデーションする。
- Qwen3.5では `attention.recurrent_layers` の明示配列があればそれを優先し、なければ `full_attention_interval` に基づく層判定を**Prismソースと一致させる**。曖昧な配列・サイズ不一致は保守的に`unknown`とする。
- 1層あたりのbit/row sizeは量子化blockの実sizeを用い、K/V別に計算する。`kType`,`vType`は `resolveKvSettings` 経由で一意に決定。
- KVはFull AttentionとRecurrentを明確に分離。SSMについては一律に`ctx×layers`を掛けず、state layoutをbackend別に導出できるときのみ数値を出す。
- GGUF disk bytesとGPU weight allocated bytesの予測を別扱い。メモリー不足判定は未知分の上限や安全余白を考慮し、楽観的な合算のみで`fits=true`にしない。
- 未知のarchitectureは旧見積もりを**上界候補**として残してよいが、`confidence=low`と明記し、精度が高いかのようなGUI表現をしない。

**必須テストベクトル**

| Fixture | 条件 | 正しい期待値 |
| --- | --- | --- |
| Hikari | qwen35, 64層, full interval=4 | attention 16, recurrent 48 |
| Hikari Q8 | ctx=131072, K/V=q8_0, seq=1 | Attention KV **4.25GiB** |
| Hikari Q4 | ctx=131072, K/V=q4_0 | Attention KV **2.25GiB** |
| Hikari FP16 | ctx=131072, K/V=f16 | Attention KV **8.00GiB** |
| Hikari mixed | K=q8_0, V=f16 | K/Vを別計算し中間値が変わる |
| 非対応architecture | 不明なlayer map | 不明項目を表示し、全GPU可と決めつけない |
| 異常metadata | 0層、過大dim、配列不一致 | 例外／安全な診断。NaNや負の予算を返さない |

**受入**: exact fixtureすべて成功。既存非hybrid GGUFの導入・表示・ロードを維持。`4.25GiB`はAttention KV理論値であり、full GPU fitの宣言に使わない。

## 6. PR-C: 単一の正規化RunPlan

**変更候補**: `apps/host/src/lib/experience.ts`, `apps/host/src/lib/native.ts`, `apps/host/server/engine.mjs`, `runtime-models.mjs`, `supervisor.mjs`, `kv-settings.mjs`, `run-config-check.mjs`, `ModelRun.tsx`。新規 `apps/host/server/run-plan.mjs`、`apps/host/tests/run-plan.test.mjs`。

**新規契約（実装案、現存API名ではない）**

```ts
type PlannedRun = {
  schemaVersion: 1;
  backend: { kind: 'native'|'prism'|'turboquant'|'llama'; binaryDigest: string|null };
  model: { id: string; metadataSignature: string; fileRevision?: string };
  requested: {
    context: number; kType: string; vType: string;
    gpuPlacement: string; batch: number; ubatch: number;
    parallel: number; flashAttention: boolean;
    memoryMode: 'ordinary'|'hakua-private';
  };
  estimated: {
    weightsGiB: number|null; attentionKvGiB: number|null;
    recurrentGiB: number|null; workspaceGiB: number|null;
    reserveGiB: number; confidence: 'high'|'medium'|'low';
  };
  effective?: { argvDigest: string; context: number; gpuLayers: number|null };
  comparabilityKey: string; // canonical config + binary/model identities
};
```

**タスク**
1. Host側をsingle source of truthとし、UIはその正規化planを表示。ブラウザー側に同じ算術式を複製しない（未接続時だけ`estimate unavailable`）。
2. `ctx.kvMode`は後方互換入力として`ctx.kType`/`ctx.vType`が未設定のときだけ使用。既存保存設定を破壊せず、新形式へmigrationを設ける。
3. frontend `Execution` / `configKey`はbackend、K/V別、context、GPU配置、batch/ubatch、parallel、cache policy、モデル・ランタイムidentityを反映。秘密・ローカルフルパスは含めない。
4. `RunPlan`をvalidateし、**検証済みの同じsnapshot**からargvを作る。検証後の再読み込みや無関係なグローバル設定参照を禁止。
5. TurboQuantの特定K/V、Prism PQ2 weights、Spin8が相互に非互換なら既存のcapability guardで明示拒否。勝手に別codecを選ばない。

**テスト**: K/V・backend・context・ubatch・parallel・private cache policyを1項目ずつ変更→`comparabilityKey`変更。legacy設定は同じ実効argvを作る。UI memory/argv/backendログのcontext・KVの整合性を検証。

**受入**: 同じplanなら同じargv、異なる実効設定なら比較結果を混ぜない。PR #3954由来のsnapshot契約を保持。

## 7. PR-D: GPU配置のAutomaticを実効化

**変更候補**: `apps/host/server/supervisor.mjs`, `engine.mjs`, `local-backends.mjs`, `native-resources.mjs`, `ModelRun.tsx`、新規 `gpu-fit-planner.mjs` とそのテスト。

**基本方針**: Hikariのようなdense/hybrid GGUFと、native MoEのexpert cache配置は**別アルゴリズム**とする。Prism/TurboQuantが認めていない機能を汎用化しない。

```text
available = measured_free_dedicated_vram
          - os_and_display_reserve
          - projected_context_cache
          - projected_workspace
          - uncertainty_margin

candidate = highest_supported_gpu_layer_count_that_fits(available)
```

上式は計画の概念であり、モデル層ごとのweights容量と実測の残差を用いる。既存の表示用GPU初期reserve **1536MiB** をbaselineとし、勝手に0へ下げない。

**タスク**
1. `Automatic`と`All layers`をUI意味として区別。前者のみ測定を用いる。`All layers`は現行の明示選択を保持し、警告を付ける。
2. layerサイズ、context別K/V・recurrent、workspaceの内訳が取れるときのみ自動算定。不明なら現行のbackend内部fitに委譲し、`planner status=fallback`を表示。
3. 初回は安全側の候補を選択。ロード後に実offload数、専用VRAMの使用・残り、shared使用量、OOMを照合。配分が危険なら**同一context/KVのまま**ユーザーに再提案する。無断のリトライ連鎖を避ける。
4. `-ngl`実値とモデルの`layer_count`を対応させる。`-ngl 999`を送ったことを「全層配置成功」とみなさず、ログで確認。
5. 追加の`ubatch`候補は256/512/1024など**backendが対応するものに限定**し、batch=2048/ubatch=512を比較baselineにする。`-ub1024`が効く・高速とは事前に断定しない。
6. 任意の`RTX 3060 12GB`追加時は別GPUに別レイヤーを配置できるかを独立試験。単一GPUを先に安定させ、異種GPU PCIe3.0帯域やGPU間転送のコストを無視して「28GBが一体化する」とは扱わない。

**テスト**: 余白不足、メモリー測定不可、model metadata欠損、CPU only、Quarter、Half、Automatic、All、sharedスピル、CUDA OOM、取消／再ロード。異常時の旧挙動に戻れること。

**受入**: 16GB実機で、同じK/Vとcontextのままbaseline以上のGPU配置が成立し、sharedスピルを増やさない。速度が向上しないなら「VRAM使用率改善」と「速度改善」を別々に報告する。

## 8. PR-E: Hakua private-prefix再利用（独立したセキュリティ変更）

**変更候補**: `apps/host/server/hakua-desktop.mjs`, `llama-memory-policy.mjs`, `serve/memory_harness.py`, `serve/llama_memory.py`, `src/program/generate.cpp`, `apps/host/src/components/HakuaLlamaChat.tsx`、対応するNode/Python/C++テスト。

**現状の契約**: native Hakuaでは `--prompt-cache 0 --conversation-cache-mib 0` とし、`memory_harness.py`が0を要求する。外部Prism/TurboQuant private modeも`--no-cache-prompt`等を課す。**これらを雑に外さない**。

**段階的な安全設計**

- E0: 現在のprivate modeのまま、再入力prefixと計算時間を可視化。秘密のprompt自体をログに保存しない。
- E1: 先に**native限定**の`session-local ephemeral cache`を新機能として定義。session IDはHostが認証済みprincipalへ束縛し、クライアント申告文字列のみで共有判定しない。
- E2: 再利用の鍵は `principal + authenticated session + model/backend digest + tokenizer + effective config + persona revision + memory revision + consent revision + exact rendered token prefix`。hash一致だけで承認せず、境界検査・token prefix一致を確認する。
- E3: KV/内部状態をsession間・利用者間・backend間で共有しない。初期はRAM-only、容量上限あり、cross-session parked cacheやslot_save_pathを禁止。既定は現行private-disabledのままfeature flagで有効化。
- E4: summary-saveで同じエンジンが別推論を行う場合、別session stateを使うか、厳密に状態保存・復元する。再利用不能なら安全に全prefillへfallback。cancel/error/restart/logout/consent変更時は対応するstateを破棄。
- E5: `require_private_engine`とHost guard、native backend policy、Protocol versionを**一組で変更**し、バックエンドが新たなprivate契約を実装・検証した場合のみ許可。旧backendは旧private-disabledで動くこと。
- E6: Prism/TurboQuant版は独立資格認定まで**cache off維持**。nativeだけ成功して全backendに一律適用しない。

**攻撃・回帰テスト**: 別principal、別session、prompt前半一致・後半変更、同意撤回、memory更新、persona変更、summary割込、cancel、OOM、再起動、悪意あるsession ID、parallel、古いbackend。機密データのcross-session漏えい0件。非同一prefixでの誤再利用0件。

**性能受入**: 同一sessionの反復・追加入力で、新たに計算したtokenだけを計上し、TTFT改善をWindowsでpaired測定。qualityと隔離テストが1件でも失敗したらopt-inを無効化して戻す。高速化のためにprivacy要件を弱めない。

## 9. PR-F: native MoE / expert cache / prefill / 長文

**変更候補**: `src/program/generate.cpp`, `src/core/expert_cache.cpp`, `apps/host/server/native-settings.mjs`, `native-resources.mjs`, `native-autotune.mjs`（現存位置を開始時に確認）、`docs/PERF131K.md`。

1. nativeの実効`--expert-cache`/`--prefill`/`--max-context`/`--spec`/MTP/`vram_reserve_mib`の値を記録。「過去の512/32」が現在も有効な場合のみ`auto`と比較。既にautoなら改めて採用成果と称さない。
2. expert hit rate、GPU cache占有、miss原因、RAM resident、SSD読込量・待ち時間、CPU推論時間、PCIe転送待ちを分離。
3. `kv-grow` / `kv-streaming` / `vram_elastic` / MTP の組合せを**既存の互換性条件内**でのみ試す。特にRAM32GBで全expert RAM常駐を前提にしない。
4. 128k近辺ではKV用VRAM・長時間prefill・RAM/commit/SSD圧迫を監視し、4k短文で良い設定と長文で良い設定を混同しない。
5. nativeモデルとHikariを同時にロードした複数プロセスの条件は別armとし、単独速度の数値に混ぜない。

**受入**: expert cache自動設定が固定設定を上回ることを実測で示せる場合のみ推奨。TTFT、prefill、decode、peak memory、入出力品質とcontextをセットで報告する。

## 10. 実機ベンチマーク仕様

### 10.1 共通固定条件

- GPU: 5060Ti 16GB。Windows/NVIDIA driver/CUDA/build版、実PCIe link speed/width、GPU power limit、クロック/温度を記録。
- RAM32GBとpagefile条件、NVMeストレージ、同時モデル・他アプリ・GPU画面表示負荷を記録。
- model SHA/revision、backend binary SHA256、GGUF metadata signature、prompt set、K/V、seed、temp、context capacity、batch/ubatch、parallel、cache policy、GPUレイヤー実数を各armに付ける。
- **cold start・warm start・cache-hit再利用を別サンプル群**にする。各armウォームアップ2回＋測定5回程度を初期値とし、同一promptを交互の順序で比較。中央値/P95相当（サンプル少数なら範囲も併記）を出す。
- 初期検証は短い4K・32K、続いて64K、最後に**131,072 capacityかつ実入力が131k近傍（生成用余白を明示）**を評価する。4K入力でcontext capacityだけ131kにしても「131k実入力合格」としない。
- decode計測は原則256token以上の生成で、短い終了時は出力数を明記。prefill tokenはcached分と新規分を分ける。

### 10.2 実験マトリクス

| 試験群 | 変えるもの | 固定するもの | 意図 |
| --- | --- | --- | --- |
| H0 | 変更前 vs PR-B/C | モデル・backend・K/V・context | memory予測と実効argvの一致確認 |
| H1 | Quarter / Half / Automatic / All要求 | Hikari、Q8/Q8、Flash on、parallel1 | 配置と速度の関係 |
| H2 | batch/ubatchの対応する候補 | H1で選んだ配置 | prefill/TTFT最適化 |
| H3 | Q8/Q8 vs Q4/Q4など | モデル・context・課題 | memory/速度と品質の**別arm** |
| K0 | Hakua private cache off vs session-only on | principal、prompt、consent、backend | TTFT・再利用・隔離 |
| N0 | native固定 vs既存auto expert/prefill | 同モデル・context・起動条件 | nativeの実効改善 |
| L0 | 4K/32K/64K/131k実入力 | 各条件の実効精度を保持 | 長文の容量・速度・品質 |

### 10.3 指標と成果物

**各run記録**: `model_load_seconds`, `ttft_ms`, `prefill_new_tokens_per_sec`, `decode_tokens_per_sec`, `cached_prefix_tokens`, `effective_context`, `gpu_layers_actual`, `gpu_dedicated_peak_mib`, `gpu_shared_peak_mib`, `cpu_peak_private_commit_mib`, `system_commit_peak_mib`, `kv_allocated_mib`, `recurrent_allocated_mib`, `cuda_workspace_mib`, `expert_cache_hit_rate`（取得可の場合）、`ssd_bytes_read`（取得可の場合）、`oom_or_abort`, `quality_pass`。

提案する保存先（新規）:

```text
bench/strata-16gb/
  README.md
  workload-manifest.json
  measurement-schema.json
  run-windows.ps1
  results/*.jsonl
  summary.md
  plots/               # 必要になった場合だけ
```

モデルやユーザーの秘密会話を結果としてcommitしない。合成promptまたは明示許可済みの非機密workloadを使う。

**採否ルール**: まず機能・安全・context・品質が全て合格すること。そのうえで速度差が再現可能なら採用。速度差が誤差程度なら「VRAM見積もり/安定性改善」として扱い、速度向上を宣伝しない。基準より遅くなる設定を自動推奨しない。

## 11. テスト・CI・リリースゲート

### テスト（既存または新規案）

- Unit: GGUF hybrid層判定、GGML row bytes、K/V別、unknown architecture、context上界、overflow、`RunPlan` canonical hash、auto-placementのfail closed。
- Host integration: `kv-settings`, `kv-engine`, `local-backends`, `local-models`, `native-gateway`, `supervisor-startup`, `native-load-cancel`、Hakua UI・記憶。Hostテストは既存のスクラッチHOME・filesystem guardを通す。
- Python/C++: memory harnessのprivate guard、native prefixの状態遷移、rollback/cancel/summary、外部backend非互換。
- Windows GPU E2E: 実context確認、専用/共有VRAM、実offload layer、予測との乖離、反復会話TTFT、131k入力、モデル再ロード、GUIキャンセル。
- GUI: `Automatic`/`All`が別の意味・ラベルで表示される。値を変更したら予測・実効設定・測定IDが一貫して更新。設定保存・migration成功。
- 安全: 同意前read/writeなし、他principal/sessionへcache漏れなし、ログにsecretなし、旧private backendでcache off継続。

### 確認コマンド例（リポジトリルート）

```powershell
# package.json requires Node >=24.22.2
node --version
npm --prefix apps/host test
npm --prefix apps/host run typecheck
npm --prefix apps/host run build
# native C++/CUDA と Tauri/Windows NSISは現行README/CIの正式コマンドに従う
# GPU E2Eは5060Ti実機で別途実行
```

**PRの品質ゲート**: 新規テスト成功＋既存テスト成功＋Win11の起動/取消/リロード成功＋model identity/署名/配布内容の維持。Linux Node 24.22.1の既存29件を「Windows配布合格」へ転用しない。新PRの検証が終わるまで既存releaseを維持する。

## 12. ロールバック・実装上の禁止事項

- 既定動作を変えるPR-D（Automatic）とPR-E（private-prefix）にはそれぞれ**個別の機能フラグ**（新設例: `STRATA_GPU_AUTOPLAN`, `STRATA_HAKUA_SESSION_PREFIX`）を用意。フラグ名は実装後にREADMEとテストへ固定。旧設定へ戻せること。
- 既存の個別K/V・runtime mappingを削除しない。unsupported combinationを黙って`FP16`へ修正しない。
- `--prompt-cache 0`を単に削除しただけでHakuaにcacheを有効化しない。Python guard、frontend consent、native process/session tokenの境界を一体的に設計する。
- OOM回避でVRAM reserve=0、context短縮、別モデル・低精度への勝手な変更をしない。
- 成功率の低い特別なCUDA kernelをデフォルトへ直結せず、backend-specificの別経路で評価。
- PRごとにdiff、テスト結果、失敗時のログ、起動argvの秘密を除いた正規化記録、比較ベンチ、元の挙動へ戻す手順を記載。

## 13. Cursor/Codexへそのまま渡す実装指示

> `zapabob/Strata` の最新mainと `Niko1221/Strata` の最新mainを先に調査してSHAを凍結し、差分と既存API契約を再確認する。今回の設計書を絶対の最新ソースとみなさず、現状と食い違う点は根拠を提示して計画を調整する。`zapabob/Strata`の独自機能（Hakua private memory、PrismML/PQ2_0、TurboQuant、Spin8/Triality、Windows/Tauri、agent/cancel）を維持する。PR-A〜PR-Gを小さな独立ブランチに分け、TDDで進める。最初は実効設定とメモリー観測を取得する。次にqwen35 hybrid層を正確に算定し、Hikari 64層・interval4→16 attention/48 recurrent、131072 Q8/Q8 KV=4.25GiBのテストを通す。UI・server・argv・benchは単一RunPlanを使い、異なるK/V/backend/cache policyのベンチ結果を混ぜない。実測可能なときのみ16GB Automatic GPU placementを行い、context=131072とQ8/Q8を無断変更しない。Hakuaのprefix cacheはprivacy guardを保ったnative session-local RAM-only実装として**別PR**に分け、consent変更・summary・cancel・別principalで使えないテストを最優先にする。RTX5060Ti Win11実機でbefore/afterのTTFT、prefill、decode、専用/共有VRAM、CPU/RAM/SSD、品質を測り、改善を再現できなければ性能向上と主張しない。テスト・CI・NSIS/配布整合性が完了する前にmainへ直接merge/push/releaseしない。`

## 14. 完成判定チェックリスト

- [ ] 計測条件・upstream/fork/runtime/model SHA固定、Baseline Windows計測を保存
- [ ] Hikari hybrid metadataを正しく解釈し、16/48のfixtureに合格
- [ ] KV量子化block計算のfixtureに合格（131072 Q8/Q8=4.25GiB）
- [ ] GUI/Host/argv/測定identityが同じRunPlanを参照
- [ ] Automatic GPU配置は余白を確保し、実GPU offloadとeffective contextを照合
- [ ] 16GB専用VRAMとWindows shared memoryを分けて報告
- [ ] Hakuaのprivate session cacheは同意・隔離・取消・要約のセキュリティテストに合格
- [ ] PrismML/PQ2_0とTurboQuantを誤って併用せず、既存の非対応ガード維持
- [ ] native expert/prefill/long-contextは同条件のperformance+qualityで評価
- [ ] 4K/32K/64K/131k実入力で段階的に確認（実際の131k inputは別途）
- [ ] 全Node/Python/C++/Windows GUI・GPU回帰テスト合格
- [ ] 速度改善が再現した経路だけ推奨へ反映、失敗時の切戻しが可能

## 15. 根拠ソース

- 公式とフォークの差分: https://github.com/zapabob/Strata/compare/c62d5e3a15b40ea51c96aae9e8d36928965f53ab...b52a198300f11437b1ed2d2cc373aa73f60ea055
- 2026-11-02詳細レビュー（ChatGPT Library）: `Strata_Official_Comparison_VRAM16GB_20261102.md`
- Hikari公開GGUF: https://huggingface.co/zapabobouj/Hikari-Bonsai-27B-Nimble-LoRA-GGUF/blob/c42fdf9debd1ba8daf4ac171d81b2052f841058f/Hikari-LoRA-fixed-scale-PQ2_0.gguf
- GGUF参照・KV概算: https://github.com/zapabob/Strata/blob/b52a198300f11437b1ed2d2cc373aa73f60ea055/apps/host/server/local-models.mjs
- K/V設定: https://github.com/zapabob/Strata/blob/b52a198300f11437b1ed2d2cc373aa73f60ea055/apps/host/server/kv-settings.mjs
- GUI予測: https://github.com/zapabob/Strata/blob/b52a198300f11437b1ed2d2cc373aa73f60ea055/apps/host/src/lib/experience.ts
- 外部GPU引数: https://github.com/zapabob/Strata/blob/b52a198300f11437b1ed2d2cc373aa73f60ea055/apps/host/server/supervisor.mjs
- Hakua private起動: https://github.com/zapabob/Strata/blob/b52a198300f11437b1ed2d2cc373aa73f60ea055/apps/host/server/hakua-desktop.mjs
- Hakua memory guard: https://github.com/zapabob/Strata/blob/b52a198300f11437b1ed2d2cc373aa73f60ea055/serve/memory_harness.py
- Prism Qwen35の構造: https://github.com/PrismML-Eng/llama.cpp/blob/73bfe6cc485554822f80c473a3c0c4f25e80f41b/src/models/qwen35.cpp
- Prism hybrid memory: https://github.com/PrismML-Eng/llama.cpp/blob/73bfe6cc485554822f80c473a3c0c4f25e80f41b/src/llama-memory-hybrid.cpp
- 量子化blockサイズ: https://github.com/PrismML-Eng/llama.cpp/blob/73bfe6cc485554822f80c473a3c0c4f25e80f41b/ggml/src/ggml-common.h
