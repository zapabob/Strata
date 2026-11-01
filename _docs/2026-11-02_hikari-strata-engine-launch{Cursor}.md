# Hikari を Strata エンジンから起動

- **日時**: 2026-11-02 08:32 JST（MCP / ローカル時刻）
- **実装AI**: Cursor (Composer)
- **GPU**: RTX 5060 Ti 16GB

## 背景 / 仮説

1. Hikari（PQ2_0）は native Qwen Q2_0 パック準備では起動できない。
2. 正しい経路は bundled **PrismML**（UI 上は「Load with Strata」）で `runtime.backend` をピン留めして supervisor（llama-server）起動。
3. Agent / web_search は native-only だと届かない → supervisor ready を `localInstances` にマージする必要あり。

## 実装

| 領域 | 変更 |
|------|------|
| UI | `NativeLocalModel`: Ready for Strata / Load with Strata → `preferredBackend` |
| Run | `ModelRun`: `pinStrataEngineBackend` をプロファイル／推奨設定の両経路で適用 |
| Lib | `apps/host/src/lib/strata-engine-backend.ts`（PQ2_0→PrismML, PTQ1_0→TurboQuant） |
| Agent | `agent-local.mjs` + `index.mjs` supervisor 行マージ、stall 用 `engineProgress` |
| Skills | 空トリガー = always-on（最大 5）、UI ヒント済み |
| 文言 | `strata_control/models.py` / `tools/strata_mcp.py` を Strata エンジン案内に更新 |

## 検証

```text
node --test tests/strata-engine-backend.test.mjs tests/agent-local.test.mjs tests/request-flow.test.mjs
→ 14 pass / 0 fail
npm run typecheck → exit 0
```

## 使い方（ユーザー）

1. Models → Use a local GGUF → Hikari フォルダを Check
2. **Load with Strata**（Prepare and load ではない）
3. 出てきた Local import で GGUF を Use → Load（`runtime.backend=PrismML` 済み）
4. Chat / Agent で web_search が supervisor インスタンス経由で到達

## 非目標

- PQ2_0 を native prepare で通すこと（不可・意図的に案内を拒否）
- Prism+TurboQuant の新規発明
