# Strata PrismL 2-bit・Bonsai Hikari07 27B・Spin8 引き継ぎ実装計画

作成日: 2026-10-23
対象: Strata 0.3.0 実装・Windows配布・正式公開
状態: 2026-10-23時点の基幹計画。最新の実行状態（G1 PASS、G2起動後停止、H:空き容量の再確認要）は [2026-10-24_strata_030_handoff_implementation_plan_Codex.md](2026-10-24_strata_030_handoff_implementation_plan_Codex.md) を参照する。この計画単独で実装完了やRelease承認を示すものではない。

## 目的

PrismLの2-bit量子化、Hikari07系を基にしたBonsai 27BのPQ2_0モデル、StrataのSpin8・Triality演算を、形式境界と実行能力を明確にしたうえでStrataへ統合する。Windows x64向けGUIインストーラーとCLI/APIポータブル配布物を作成し、受入条件を満たした場合に限り、同じ検証済みソースコミットをmainへ通常pushし、v0.3.0として公開する。

この文書は引き継ぎのための実装順序と確認条件を定める。過去に記録された限定試験や計画上の目標を、新しい試験結果として扱わない。

## 現在確認できた作業状態

- 作業フォルダーはStrataリポジトリ。確認時のブランチは codex/strata-spin8-bonsai、HEADは b6a1b95。
- ローカルのorigin/main参照は 02e4414。今回の確認ではリモートへの再接続・再取得をしていないため、GitHub上の現在値とは断定しない。
- 作業ツリーには既存の変更がある。これらを保持し、内容を確認せずに上書き・破棄・一括stageしない。
- 変更済み: _docs/2026-10-23_strata_030_execution_Codex.md、tqcodec/CMakeLists.txt。
- 未追跡: tools/verify_codec_dialect_faults.py、tools/verify_codec_dialects.py、tools/verify_codec_dialects_build.ps1、tqcodec/DIALECT_LICENSE.txt、tqcodec/include/tqcodec/dialects.h、tqcodec/src/dialect_tables.inc、tqcodec/src/dialects.cpp、tqcodec/tests/dialects_c_test.c、tqcodec/tests/dialects_test.cpp、tqcodec/tests/fixtures/dialects-v1.bin。
- 実行記録では、Spin8 v3 query adapterの限定的なHikari 27B統合試験が報告されている。報告範囲は512 contextの14-token試験などであり、4K/32Kの品質・性能受入や正式配布の証明ではない。
- 大型Strata Q2_0はnative packのデータ準備が記録されているが、native engineでの実推論と受入測定は未完了。
- 実行記録の最後に確認されたHドライブ空きは約296 MiB。現在の空き容量は未確認であり、大型build・download前に再確認する。
- 実行記録では8080を停止状態に保っている。再開時にも状態を確認し、明示的な指示がない限り停止状態を保つ。
- Windows setup.exe、tarを7z圧縮したportable配布物、最終インストール試験、正式Releaseは未確認。正式Release条件は未達として扱う。

作業開始時に、上記Git状態・ディスク容量・8080の状態を改めて読み取り、結果をこの計画とは別の実行記録に追記する。過去の時点付き状態を現在の事実として流用しない。

## 引き継ぎ対象と形式の境界

1. Spin8: 同じSpin(8)元から導出するベクトル・左右スピノル表現、Triality query変換、直交性とDetの監査を扱う。端数チャネルは恒等経路とし、既定経路は変更しない。
2. PrismL: 固定したPrismML runtimeと2-bit codecを専用dialectとして検証する。PrismとTheTom、Strata独自形式、参照PoCのabsmax codecを同じ型番号や名称だけで同一視しない。
3. Bonsai: Hikari07由来のPQ2_0と、ローカルのHikari-Bonsai派生モデルを別々の成果物として識別する。配布元の元PQ2_0 hashを、派生GGUFのhashとして転用しない。
4. 実行能力: モデル名だけで対応可否を決めず、演算・形状・cache操作・device・実際にbuildされたkernelに基づき判定する。未接続の再帰層は従来経路を維持する。

## 実装順序と完了条件

### 1. 状態保全と入力の固定

現ブランチの全差分、未追跡ファイル、直近コミット、remote main、対象モデル・依存ソースの版を記録する。既存の作業記録・PoC由来資料は読み取り、出所と今回のPCで得た証拠を分ける。Hikari派生モデルとHikari07元モデルのファイル名、サイズ、SHA-256、量子化形式を個別に照合する。

完了条件: 作業前の状態が復元可能な一覧として記録され、対象ソース・モデル・runtimeの固定版とライセンスが確認されている。記録されていないファイル移動や削除はしない。

### 2. 進行中のcodec dialectをレビューして確定

tqcodecとtoolsの未コミット変更を一つずつ読み、生成表、型識別、packing、scale/norm、bit順序、Hadamardとsignの適用順を固定したPrism/Bonsai一次ソースと照合する。既存の型番号衝突を拒否し、形式の識別情報が足りない場合は読み込みを失敗させる。ライセンス表示と由来記録を各形式に結び付ける。

確認する内容: C/C++ ABIとPython側の既知回答一致、fixtureの出所とhash、非連続stride、境界値、容量不足、旧形式・誤形式の拒否、故障注入。CPUの小規模試験を先に行い、CUDAや全体buildは空き容量・RAMを再確認してから一つずつ実施する。

完了条件: 独立した期待値による形式別試験が通り、実装済み・未実装のbit幅とshapeが明確になっている。試験未実行なら、対応済みと表示しない。

### 3. Spin8とTrialityの数理契約を確定

Clifford関係、カイラリティ、群積・逆元、Triality不変式、2π/4πのスピノル挙動、恒等初期化、左右表現、Hadamardの正規化と逆順を独立した参照実装と比較する。行列監査では直交誤差、Det符号、log|det|、読み込み時との差を記録する。係数行列の誤差と実際のCPU/CUDA演算誤差、量子化損失を分ける。

完了条件: FP64参照、CPU実装、対象CUDA kernelが許容誤差内で一致し、異常時にtransform_invariant_violationとcache無効化が起きることを確認する。未接続の演算を能力情報に含めない。

### 4. Prism runtimeへHikari Bonsaiの実演算を接続

固定Prism runtime上で、Hikari 27Bの通常Attention層へSpin8 query adapterと対応codecを接続する。Q変換位置、RoPE/MRoPE、mask、scale、gate、sparse選択規則、GQA、KV cacheの状態を確認する。48再帰層は既存経路を維持し、全16通常Attention層の適用範囲を診断に出す。ゼロadapterは既定Attentionと一致し、非ゼロadapterは別途品質評価する。

cacheの保存・復元・複製・位置移動・キャンセルを検査し、model・数学規約・codec・係数・adapter・位置処理の識別情報が違う状態を再利用しない。単独演算のpassを実モデル統合の証拠に置き換えない。

完了条件: Hikari 27Bでprefillとdecode、通常層の適用範囲、未対応演算の従来経路、cache状態管理を実際のruntimeで確認する。警告・失敗・未実行を分けて保存する。

### 5. 3方式と基準経路を比較し、品質を評価

同じ重み・入力・sampling条件で、通常経路、単独Spin8表現、consensus、Prism 2-bit経路、必要な場合のQJLおよびquery adapterを比較する。QJLはbeta=0を必須基準とし、補正の採否は較正用データと最終評価データを分離して決める。K/V形式は独立して記録し、metadataとscratchを含む実使用メモリを測る。

Hikari Bonsai 27BとStrata大型Q2_0の両方で4K/32Kを測る。各条件3回warm-up後に10組の交互測定を行い、生成速度、TTFT、p50/p95、PPL、RAM/VRAM、監視コスト、失敗を保存する。小型モデルや合成課題は実モデルの代替にしない。

### 6. Windows配布物を作り、隔離した環境で試験

Windows x64、RTX 5060 Ti向けsm_120、CPU AVX2を対象に、依存lockを維持して逐次buildする。モデル重みと開発用学習環境は配布物から除外する。fork識別子とupdate feedを確認し、上流feedへ誤接続しないことを検証する。再配布ライセンス、DLL、固定runtime、font・imageの条件を確認する。

候補成果物: Strata-0.3.0-windows-x64-sm120-setup.exe と Strata-0.3.0-windows-x64-sm120-portable.tar.7z。portableはtar作成後に7z圧縮し、展開テスト、manifest、SHA-256、build provenanceを添える。

試験範囲: GUI install/start/inference/exit/restart/uninstall、CLI/API起動、空白を含むportable移動先、system PATHにPython/Nodeがない状態、既存モデルと設定の保持、8080停止の確認。署名の有無を明記し、SHA-256をpublisher署名の代わりと説明しない。

### 7. README、レビュー、main公開

README冒頭とRelease本文の先頭に、AI engineer向け80〜100語のBritish English TL;DRを置く。添付PoCの図表を使う場合は、Linux CPU・合成課題・3 seedの結果であることを図の近くに明記し、単一6-bitの優位と信頼区間も隠さない。今回のPCで測った表は独立に生成し、データ元を保存する。

同一の検証済みコミットについて、変更差分の独立レビュー、該当backendのbuildと回帰試験、必要なCI、モデル試験、配布物試験を完了する。条件を満たした後だけmainへ通常pushし、v0.3.0 tagとGitHub Releaseを作る。公開後に各assetを再取得し、manifestとSHA-256を照合する。

## 正式公開の判定基準

| 指標 | Hikari Bonsai 27B・大型Strata Q2_0の各モデルで必要な結果 |
|---|---|
| 生成速度 | 同日・最適化済み基準より中央値で5%以上向上 |
| TTFT | 中央値の悪化が5%以内 |
| PPL | 同一評価データで増加が1%以内 |
| 機能試験 | 固定試験で新規失敗がない |
| 監視コスト | 追加コストが1%以内 |
| 配布 | installerとportableの導入・起動・実推論・終了が確認済み |
| 再現性 | ソース、runtime、モデル、試験結果、配布manifestが同じcommitへ結び付く |

三つの物理K viewが機能することと、速度採用プロファイルの性能判定は別々に記録する。速度・品質のどれかが未達なら正式Releaseを止め、結果を残して改善を続ける。実験機能として残す場合も、未達条件を明記する。

## 次の担当者が最初に行うこと

1. 現在のブランチ、HEAD、remote main、作業ツリー差分を読み直し、既存変更を保存する。
2. 実行記録と関連するacceptance、codec、Spin8、Prism統合の各記録を読んで、最後の証拠と未完了ゲートを照合する。
3. Hドライブ空き、RAM/VRAM、8080 listener、対象モデルの場所とhashを確認する。古い容量値を使わない。
4. codec dialectの未追跡ファイルをレビューし、小規模CPU試験の実行可否を容量上限付きで決める。
5. この計画とは別の実行記録に、実施した正確なコマンド、対象SHA、PASS/FAIL/NOT RUN、ログ保存先を書く。

## 関連記録

- 実行とRelease記録: [2026-10-23_strata_030_execution_Codex.md](2026-10-23_strata_030_execution_Codex.md)
- 受入評価器: [2026-10-23_acceptance_v2_Codex.md](2026-10-23_acceptance_v2_Codex.md)
- Prism側統合: [2026-10-23_prism_query_integration_Codex.md](2026-10-23_prism_query_integration_Codex.md)
- Spin8 core: [2026-10-23_spin8_core_Codex.md](2026-10-23_spin8_core_Codex.md)
- codec/cache: [2026-10-23_quant_cache_Codex.md](2026-10-23_quant_cache_Codex.md)
- 貢献と検証ルール: [CONTRIBUTING.md](../CONTRIBUTING.md)

この引き継ぎ計画の作成中に実装試験・build・Git操作・モデル実行は行っていない。
