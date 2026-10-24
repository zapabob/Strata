# Strata 0.3.0 引き継ぎ実装計画書

作成日: 2026-10-24  
対象: Strata 0.3.0、Spin8/Triality検証、実モデル評価、Windows配布  
計画ID: PLAN-2026-10-24-STRATA-G1-G6  
状態: 最新の確認済み状態と次の受入手順。Release承認ではない。

## 目的と適用範囲

この文書は、前回の基幹計画 [`2026-10-23_strata_prism2_bonsai_spin8_handoff_plan.md`](2026-10-23_strata_prism2_bonsai_spin8_handoff_plan.md) を引き継ぎ、2026-10-24に確認したG1の数値検証、G2のモデル起動状態、空き容量、未完了ゲートを記録する。前回計画は全体設計とRelease受入基準の参照元とし、この文書は最新実行状態の参照元とする。

G1は完了した。G2はQ2_0の4Kサーバー起動まで完了したが、512トークンを超えるAPIリクエストをまだ送っていない。G3以降は未実行である。現在Strataサーバーは停止しており、8080のLISTENソケットはない。H:の空き容量は起動前より約183 GiB減っている。原因を特定するまで、大型のダウンロードやbuildを始めない。

## 最新状態

### リポジトリと変更

確認した作業ディレクトリは `C:\Users\downl\Documents\ChatGPT\Strata`、ブランチは `main`、HEADは `f8074a670fc0d8b4971a30685f6093b266582e5f`。この確認時点では既存の変更として実行記録に差分があった。今回の作業で変更するのは実行記録と引き継ぎ文書のみであり、ソース、モデル、設定ファイルはこのワークスペース内では変更しない。ステージ、commit、push、remoteの再取得は行わない。

G1のprobe、reference、build出力は `H:\Strata\build\task5a-gateA-spin8-20261023` に置かれており、Gitワークスペース外の証跡である。G1作業中に `scripts\gate_probe\probe_spin8.cpp` と `scripts\compare.py` を更新した（F32 loopback比較、数理reference、JSON/report gates）。これらの外部ファイルと全receiptを削除・移動しない。

### G1: Spin8/Triality数値ゲート — PASS

- CPUライブラリbuildとCTest: `cfg-cpu`, `build-cpu`, `ctest-cpu`。CTestは6/6 PASS。
- Probe: seed `20261023`、5,000 trials、1,000 Python-check trials。probe実行 `probe-run-r5` はPASS。
- 独立FP64比較: `H:\Strata\build\task5a-gateA-spin8-20261023\probe\reference_compare.json`。`compare-run-r12` は12/12 family PASS。
- 主な最大誤差: trial vector-fit 7.8e-16、vector/action 1.4e-15、conjugation 2.0e-15、F64 loopback 7.8e-16、F32 loopback 5.96e-8。query v3 VJP差は非ゼロ係数1.94e-10、ゼロ係数9.50e-11。Hadamardの256 maskすべてでdet符号がmask parityと一致し、独立Bareiss整数行列式も256/256で一致。
- double LUによるdet符号は該当行列で不安定だったため、rotor符号は要素を分母上限10^12で有理化したFraction演算による先頭100 trialsのspot checkで、Hadamard符号はmask parityと整数Bareissで確認した。監査のlog|det|、Gram誤差、行列作用の数値チェックは別々に記録されている。
- 受入判定とG1の詳細は [`2026-10-23_strata_030_execution_Codex.md`](2026-10-23_strata_030_execution_Codex.md) のG1 addendum、および上記JSONと各label receiptを参照する。

### G2: 実モデルの4K起動 — 起動確認のみ、受入未完了

実行したrepo-local Terminalコマンドは次のとおり。`strata`はこのシェルのPATH上になかったため、Python 3.12から `strata.py` を呼び出した。

```powershell
& "C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe" -B strata.py launch --plan --model q2_0 --context 4k `
  --model-path "H:/Strata/models/q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf" `
  --data-dir "H:/Strata" --vision cpu --tune skip --access local --port 8080

& "C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe" -B strata.py launch --model q2_0 --context 4k `
  --model-path "H:/Strata/models/q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf" `
  --vision cpu --tune skip --access local --port 8080 --data-dir "H:/Strata" `
  --yes --no-tui
```

Planはローカルの約66 GBモデルを認識し、不足物として約6.1 GB（draft layerとpicture reader）を見積もった。起動出力では低メモリ用expert packの一回処理が完了し、draft layerを取得し、engineがloadされ、`http://127.0.0.1:8080` でserving readyになった。進捗表示はexpert pack処理中に「38 min so far」と報告した。写真readerが今回新規取得されたかは、起動出力から確認していない。

`strata.py launch --status --output json` はprofile `q2_0-4k`、state `ready`、host `127.0.0.1` を報告した。保存されたrun設定の場所は `C:\Users\downl\AppData\Local\Strata\launch\q2_0-4k.json`。この設定を削除・書き換えない。起動後にAPI requestを送っていないため、HTTP応答、`usage.prompt_tokens`、512超の実プロンプト、応答品質、速度は未検証である。したがってG2をPASSにしない。

停止コマンドと確認結果:

```powershell
& "C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe" -B strata.py launch --stop --preset "Q2_0 4K"
& "C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe" -B strata.py launch --status --output json
Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
```

停止コマンドは `Stopped q2_0-4k.` を返した。statusの `running` は空配列で、LISTEN結果はなかった。次回も作業開始時にlistenerを読み取り、作業終了後に再度停止確認する。

### 容量・モデルの状態

起動前のH:空きはPowerShell計測で209.8 GiBだった。停止後は、.NET DriveInfo、`Get-Volume`、WMI `Win32_LogicalDisk`、`fsutil volume diskfree H:` がすべて `28,910,108,672` bytes（26.92 GiB）を報告した。ある直後のGet-PSDrive出力では一時的に0 bytesと表示され、その後のGet-PSDriveは28,910,108,672 bytesと一致した。したがって現在確認した値は26.92 GiBだが、計測時点の不一致も記録しておく。起動前からの約183 GiBの減少原因は未特定であり、起動処理だけが原因とは断定しない。

C:空きは10.00 GiB。RAMは起動前4.74 GiB、停止後9.28 GiBのfree表示だった。H:上のモデルshardのサイズとmtimeは既存記録と一致したが、本セッションでは再hashしていない。過去のSHA256は [`2026-10-23_strata_030_execution_Codex.md`](2026-10-23_strata_030_execution_Codex.md) を参照する。モデルの同一性が必要な正式計測前にはhashを再確認する。

空き容量の変化を説明できるまで、H:に対する追加download、build、packを保留する。読み取りだけの容量調査は可能だが、ファイルを削除・移動・圧縮して容量を戻す操作は別途所有者の許可なしで行わない。

## 実装順序と受入ゲート

### Gate 0 — 容量と実行状態を再確認

1. `strata.py launch --status --output json` とTCP LISTENを確認する。8080が動作中なら、次のテストを意図せず止めないよう状態を記録し、完了後に停止する。
2. H:のfree bytesを.NET DriveInfoとWin32_LogicalDiskまたはGet-Volumeで照合する。Get-PSDrive単独の瞬間表示を容量判断に使わない。
3. H:\Strataの今回の関連領域と、Strataが管理するpack/outputのみをread-onlyで確認し、起動前後の容量差を説明できる記録を探す。ドライブ全体を無差別走査しない。原因が特定できない場合は未特定として残し、所有者の容量判断を待つ。
4. `strata.py launch --plan` を明示したmodel path、data dir、contextで再実行し、不足物と見積もりを確認する。計画上のpeak使用量と安全余裕を満たすまでは再起動しない。

完了条件: H:の実測空きが再現可能な形で確認され、既存ファイルを削除せずに次の検証を実行できる容量根拠がある。

### Gate 1 — G2: 4Kで512トークン超のAPI実行

1. Gate 0通過後、同じQ2_0 shard、`--data-dir H:/Strata`、`--context 4k`、`--vision cpu`、`--tune skip`、`--access local`、port 8080で起動する。loopback以外にbindしない。
2. statusがreadyで、listenerのlocal addressが`127.0.0.1`であることを確かめる。
3. `http://127.0.0.1:8080/v1/chat/completions` へ合成テキストのみを送る。秘密情報・個人データは含めない。応答JSONのHTTP成功、non-empty response、`usage.prompt_tokens > 512`、完了状態を確認し、応答時間とtoken数を記録する。プロンプト長を見積もりだけで済ませず、serverのtoken usageを受入根拠にする。
4. OS RAM、GPU VRAM、model/context、request/response IDs、失敗とtimeoutを保存する。認証情報や秘密鍵を記録しない。
5. `strata.py launch --stop --preset "Q2_0 4K"` を実行し、statusが空、8080のLISTENが0であることを確認する。

G2受入: 実際のQ2_0からHTTP成功応答があり、server-reported prompt tokensが512を超え、loopback限定、モデル/context情報と実行記録が保存され、停止後にlistenerが0であること。起動だけではPASSにしない。

### Gate 2 — G3: 4K/32Kの比較と品質・性能

G2後、既存の基幹計画のSection 5と正式公開判定基準を適用する。比較対象・基準経路・モデル・prompt set・samplingを固定してから測る。Hikari Bonsai 27Bと大型Q2_0を混同せず、各モデルごとに4Kと32Kを実測する。各条件3 warm-up後に10組の交互測定を行い、生成速度、TTFT、p50/p95、PPL、RAM/VRAM、監視コスト、失敗を記録する。異なるモデルや異なる日の実行を同一比較として扱わない。

G3受入: 同一入力・同一設定の記録があり、性能、品質、memory、monitoringの各基準が前回計画の表に照らして判定されていること。未測定指標は未測定とする。

### Gate 3 — G4: native engine実推論

既存native packを使う場合も、native engineの正確なbuild、対象GPU backend、モデル入力、推論結果、成功/失敗を新しい証跡で記録する。pack準備やlibrary testだけで実推論済みとしない。大規模buildの前にGate 0の容量を再確認する。

### Gate 4 — G5: Windows配布物

前回計画のWindows x64/CUDA・CPU対象とinstaller/portable条件に従う。逐次buildし、隔離環境でinstall/start/inference/stop/uninstall、portable展開・移動、manifestとSHA256を試験する。配布ライセンスとfork update feedも再確認する。G5を実測なしにPASSとしない。

### Gate 5 — G6: fork-only正式Release判定

すべての前段ゲート、独立レビュー、release asset検証が完了するまでtag/Releaseを作成しない。既存の承認範囲どおりfork側だけを対象とし、upstream `Niko1221/Strata`には変更を公開しない。正式公開基準未達または未測定ならReleaseを保留する。正式MILSPEC適合を主張しない。

## 要求から証跡への対応

| ID | 要求 | 実装・実行状態 | 検証証跡 |
|---|---|---|---|
| G1 | Spin8/TrialityのCPU基準と独立参照を通す | 完了、12/12 family PASS | `H:\Strata\build\task5a-gateA-spin8-20261023\probe\reference_compare.json`、各label receipt |
| G2 | 実Q2_0で512を超えるpromptをserver経由で完了する | engine起動は成功、API受入未実行 | start/stop/statusの記録は実行journal。API応答は未取得 |
| G3 | Bonsaiと大型Q2_0の4K/32Kを同条件で比較する | 未実行 | 未取得 |
| G4 | 大型Q2_0のnative engine実推論を確認する | native pack準備記録のみ。推論は未実行 | 未取得 |
| G5 | Windows installer/portableをbuild・隔離試験する | 未実行 | 未取得 |
| G6 | 条件を満たした同一commitをfork-onlyで公開する | 保留 | release承認なし |

## 適用基準と作成記録

選定SOP: 共通MILSPECLLMOps、Implementation Start Gate、Skill Selection、Security、LLMOps、Internet Connectivity、Application Development。選定Skill: `milspec-codex-standard`、`plan-mode`。この文書作成はローカルの実行記録、codebase docs、status、receiptsを根拠とし、web researchは行っていない。最新の外部情報に依存しない。

変更ファイル: この計画書、`2026-10-23_strata_030_execution_Codex.md`（G1記録の訂正とG2の起動・停止状態追記）、`2026-10-23_strata_prism2_bonsai_spin8_handoff_plan.md`（最新計画への参照追記）。作業用H:にはG1 probe/reference scriptの変更とreceipt群があり、Terminalは `C:\Users\downl\AppData\Local\Strata\launch\q2_0-4k.json` run設定を保存した。これら外部状態は変更済み・保持対象であり、本計画書作成時に削除やresetはしていない。

作成時に実行した確認は `git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`git diff --check`、`strata.py launch --status --output json`、`Get-NetTCPConnection`、Get-Volume/.NET DriveInfo/WMI/FSUtilの空き容量照合である。API smoke、32K評価、native inference、配布buildはこの計画書作成時に実行していない。

残留リスク: H:の約183 GiB空き容量減少原因、今回のlaunchが作成したexpert pack/support fileの所在と容量、4Kでの実API応答、32K時の資源使用、モデル品質と性能、native engineの実推論、installer/portable試験は未解決。既存ファイルは保持し、H:への大規模書き込みを容量再確認まで保留する。

推奨する次の作業: Gate 0の読み取り専用容量確認を実施し、容量と必要な余裕が根拠付きで確保された後にG2の4K・512超API smokeを行う。各ゲートの完了は新しい証跡を記録してから判定する。

Self-review-event: type=qa_defect scope=_docs/2026-10-24_strata_030_handoff_implementation_plan_Codex.md category=docs-traceability evidence=_docs/2026-10-24_strata_030_handoff_implementation_plan_Codex.md. Review-only: review caught imprecise wording around denominator-limited Fraction checks and an initial Markdown-fence validation command whose PowerShell quoting was wrong. The wording was corrected and fence/link validation rerun with a character-code-based check. No AGENTS, SOP, skill, QA policy, or automation update is justified by this single local documentation event. Residual risk remains the un-attributed H: capacity change recorded above.

Self-review-event: type=ticket_completed scope=strata-0.3.0-handoff category=docs-traceability evidence=_docs/2026-10-24_strata_030_handoff_implementation_plan_Codex.md. Review-only; no governance update applied.
