# Qwen36 / RAM 32GB・VRAM 16GB 起動・推論改善 設計仕様

作成日: 2026-11-02 JST  
対象: `zapabob/Strata`、Windows native、Qwen3.6-35B-A3B UD-Q4_K_XL  
状態: **部分実装あり。GPU mapped-live / paired speed は未実行（NOT_RUN）。完了宣言しない。**  
最終再測定: 2026-11-04 05:22 JST — Hermes VRAM 占有で mapped-live **BLOCKED**（DESIGN #6 により未殺; free ~873 MiB）。ローカル未署名 q36 を help 正直化込みで再ビルドし `strata.exe` SHA-256 `64226fde…` を `0.4.0-q36-…` にだけ入れた（署名 `b5e4d525…` 非接触）。製品 `.5` インストーラは未再出荷。詳細は `NOTES-05-22-rebuild.md`。  
対になる作業計画: `Strata_Qwen36_Implementation_Plan_2026-11-02.md`

## 1. 目的と対象

ユーザーのRAM 32GB、RTX 5060 Ti 16GB環境で、Qwen36の起動失敗・約10分の初期化・分かりにくい進捗を改善し、同じモデルを継続して使える状態にする。単にREADYを早く表示するのではなく、最初の有用な応答、継続会話の応答間隔、停止・再ロードまでを評価対象とする。

主比較はcontext=65,536、同一GGUF、同一tokenizer、同一KV保存精度、MTP=2、単一会話で行う。元ログの `--prefill auto` は実効2048だったため、再現比較では実効値を固定する。32K/16K、MTP=0、FP16 KVは別の選択的試験であり、本線の性能向上に混ぜない。131,072は後段の独立認定とする。

CPUは直近の画面にRyzen 5 4500・6 cores / 12 threadsと表示されている。以前の4600という記録を優先せず、実装開始時に実機を再取得する。PCIe Gen3 x8も画面上の観測であって、転送速度の実測ではない。

## 2. 根拠と解釈

基準ソース: `170e0d330edd9c03b5dcddfc64b77e498387ff86`。これは公開mainの読取基準であり、配布済みEXEと完全一致するという意味ではない。EXE、DLL、component manifest、Control、Hostの実際のdigestは実装時に取得する。

添付2ファイルは同じ17,159 bytes、SHA-256 `8953c82d982a50f6d546c551f9bff3edb2bcb40fb8fc4f525cc79a5d954a14cb`。二重計上しない。22起動、host allocation失敗14、VRAM不足2、expert配置完了2、warmup完了1が記録される。後続行がない試行を失敗・hangと決めない。

2026-11-02 21:56:54開始の記録（原本73–78行）:

| 区間・状態 | 記録値 |
|---|---:|
| 初期tensor検査・GPU転送 | 28.6秒、4.40GiB |
| context / prompt chunk | 65,536 / 2,048 |
| expert配置前の空きVRAM | 4.91GiB |
| expert配置 | 266.0秒 |
| GPU expert slots | 各層41 / 256、合計3.00GiB |
| host expert arena | 全18.75GiB、pageable |
| GPU staging | 1.10GiB |
| warmup | 306.6秒 |

`load()`、`place_experts()`、`warmup()`は別のタイマーで、配置完了後にwarmupを呼ぶ実装である。記録3区間の和は601.2秒。ただし`Engine::init()`、server readiness等を網羅する時計ではなく、総起動時間の精密値・中央値・P95には使わない。

解釈上の境界:

- `41/256=16.015625%` はslot容量比。GPUの実仕事量・routing hit rateではない。
- `pageable` はpinされていないメモリ。18.75GiBが全てpagefile上にあることや、実際のpage fault多発までは証明しない。
- 全起動の `--native` は論理パスH:。C:のGGUFを選択した実行はログにない。ただしH:配下のjunctionやmountを解決していないため、物理ディスクの種類・所在地は未確定。
- 最終の `0 of 0 batch entries` は生成速度の証拠ではない。warmup後にcounterをresetするコードもあるため、GPU利用率0%の実測値へ読み替えない。
- 22回の起動は同時起動を証明しない。過去の2つのllama-serverは別の観測として扱い、所有元・現存状態は再取得する。
- Hikari用の16 full-attention / 48 recurrent、Q8 KV=4.25GiBという計算をQwen36へ流用しない。

## 3. 現行コードに即した原因候補

`q36_engine.cu` のGGUFはすでにmemory-mapされている。その後 `place_experts()` が全expertを新しいhost arenaへ再配置する。この追加arenaとsource mappingのworking set、GPUのresident expertコピーは区別する。

並べ替えは `expert_blob()` の `[gate | up | down]` バイトコピーで、strideは量子化block sizeと16-byte alignmentの公倍数で丸められ、`kMmqTail` が必要。raw GGUFをそのまま `hblobs` に差すだけの変更は不正。

hybridでは全量 `cudaHostAlloc` を試し、失敗すると `malloc`。CPU poolの小batch処理と、GPU stagingを使う大chunk処理が分かれる。全量pin失敗・zero-fill・repack・host→device転送のうち、何が266秒を占めたかは未計測。

warmupは最大1チャンクのfillerに加え、条件付きの小GEMM probe、decode、MTP speculative step、同期、state resetを行う。306.6秒の内訳は未計測。`--no-warmup` は現存するが、単に初回リクエストへ費用を移す可能性がある。ready時刻だけを成果にしない。

## 4. 検討した方式と推奨

| 方式 | 利点 | 欠点 | 採用判断 |
|---|---|---|---|
| 設定調整のみ | 実装小、短い比較が可能 | 全量コピーと恒常的な配置問題が残る | 切り分け用。最終解にはしない |
| 並べ替え済みread-only expert backing＋小容量pinned staging | 量子化値を変えず、再起動時の再pack・大private arenaを避けられる | 追加disk・整合性・page fault・寿命管理が必要 | **推奨する本線**。段階導入 |
| 全expertをさらに量子化／別モデルへ変更 | 収容しやすい可能性 | 品質・互換性・比較対象が変わる | 本計画外。無断変更禁止 |

推奨案は未承認の性能保証ではなく、実装者に対する設計提案。最初にsource binding、能力契約、計測とライフサイクルを整え、その後でopt-inのbacking storeを導入する。

## 5. 非交渉の契約

1. 元GGUF、tokenizer、重み精度、top-k expert選択、既存Hakua同意・認証境界を保持する。
2. 独立したnative Qwen36、Flash-Next、PrismML/PQ2_0、TurboQuantの能力を混同しない。
3. 新経路は個別opt-in。旧経路をbaselineとして残し、未知のbinaryへ新flagを投げない。
4. unsupportedな明示設定は起動前にエラー。private-cache制約を削除して起動成功扱いにしない。
5. context、KV、モデル、MTPを黙って変えない。回復再試行は同じ実効設定の繰返しにしない。
6. 他アプリの推論serverをkillしない。PIDだけでなく生成時刻・job/nonce等で所有を確認する。
7. C/Hを問わず既存重みを無断移動・再取得・上書き・再量子化しない。cache作成前にdisk reserveと容量を確認する。
8. CPU/GPUの演算順変更は数値差を生む場合がある。I/O・backing変更のbitwise parityと、配置変更・新kernelの品質評価を分ける。
9. CUDA build成功、synthetic parity、Windows実モデル、API/GUI E2Eを別々に報告。未実行をPASSにしない。
10. mainへの直接push、署名の迂回、配布componentの手動上書きは行わない。

## 6. 成功の定義

同一条件で5組以上のpaired runを取り、まず機能・隔離・品質を全件合格させる。主性能目標は「起動要求から最初の有用tokenまでの中央値を30%以上短縮」、かつ初回・継続decodeの中央値を5%超悪化させないこと。これは**採否用の提案目標であり、達成済み数値や高速化予測ではない**。小サンプルではP95を確定値と扱わず、全サンプル・範囲・中央値・paired差を記録する。

memoryの構造的な成功は、新store経路で全expert分の匿名private arenaを作らず、pinned stagingと独自host cacheを明示予算内に保つこと。file-backed working setやOS page cacheがゼロになるとは主張しない。

パス・契約・進捗・停止の修正は、速度差がなくても正確性の成果として独立して受入可能。重い最適化経路はend-to-endの改善が再現するまで既定化しない。
