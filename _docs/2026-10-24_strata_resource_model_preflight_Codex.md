# Strata completion: resource and model input evidence

Date: 24 October 2026. Plan: PLAN-2026-10-24-STRATA-COMPLETION. These checks establish available resources and model content identity. They do not qualify inference, speed, quality or a release.

## Requirements and scope

The approved completion plan requires retained files, no unnecessary model download or repack, sequential large operations, and each operation's additional peak space plus 10 GiB reserve. The canonical prompt and applicable governance were read as recorded in the completion execution record. This preflight reads only Strata-related directories and the explicitly named primary model. Existing models, packs, old receipts and launch settings were not modified, moved or deleted. Port 8080 was not started.

Raw receipts are in `H:/Strata/build/completion-resources-20261024/`. Model reads used full-file SHA-256, not sampled ranges. Each model's size and last-write timestamp were checked before and after hashing. Q2 shards were opened with `FileAccess.Read` and `FileShare.Read`; the primary model was read through `Get-FileHash`.

## Resource snapshot

At 03:43 UTC, both .NET DriveInfo and Win32_LogicalDisk reported H: available bytes as 28,908,257,280, approximately 26.9 GiB. Related inventories were models 357,569,069,308 B, packs 35,469,659,709 B, build 2,202,146,720 B and mtp 6,927,660,074 B. This is a snapshot, not reserved capacity or authorisation to start an arbitrarily large build. A before-file snapshot is missing for the historical approximately 183 GiB change; complete attribution is unresolved.

The same preflight found 7,994,080 KiB free physical memory and 21,966,256 KiB free commit, with RTX 5060 Ti capacity 16,311 MiB and reported use 1,072 MiB. No 8080 listener or matching active compiler/model-server process was returned. Every later build/model run must check current resources again; these figures cannot substitute for a launch guard.

## Fresh mandatory-model content hashes

| Input | Bytes | SHA-256 | UTC read interval |
|---|---:|---|---|
| Qwen3.8-Flash-Next-GSQ-RCO-Q2_0 shard 1 of 2 | 37,623,740,192 | `69820c02ec7d0b45ef2ebb19d6620299db749fe2aded7f39f93c6b88b199b720` | 04:04:40–04:07:42 |
| Qwen3.8-Flash-Next-GSQ-RCO-Q2_0 shard 2 of 2 | 28,800,138,432 | `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113` | 04:07:42–04:09:35 |
| zapabobouj Hikari-LoRA-fixed-scale-PQ2_0 | 7,206,168,928 | `0ab2a1f237b73e5002ecd8c9b764249b90ee59eca749a6226c44bb43b1036a13` | 04:10:25–04:11:31 |

All three matched the previously frozen expected values. All before/after sizes and modification timestamps matched. Q2 scanning ended with exit 0, as did the Hikari hash operation. Together these reads covered 73,630,047,552 bytes. The receipts retain exact local model paths; no GGUF conversion, attribute change, weight edit or model download occurred.

These hashes can be reused by the next gate after verifying the paths, sizes and modification timestamps still agree. A source change or a concrete provenance doubt requires renewed verification. A documentation/tooling commit alone does not change model content identity.

## Existing Q2 pack reuse

`H:/Strata/packs/q2_0` and `H:/Strata/models/q2_0/native-pack-030-20261023` have matching `native_experts.txt`, `index.txt` and `conversions.json` hashes. Both copies of `dense.bin` were fully hashed: each has 1,485,606,400 bytes and SHA-256 `a43d7d0b69525335f4b000d5197a1d3aefcd3c0014fc3e12b3455e0a5d827ba2`.

The candidate pack's 33,973,862,400-byte `experts.bin` has matching size/source metadata but was not fully payload-verified by this preflight. No claim of full equality is made for that file. The retained native pack has no `experts.bin` and references the original GGUF expert spans; source-bound native inference can use it after checking the index/layout/tokenizer inputs. This avoids an unnecessary new pack while retaining both existing directories. Whichever expert storage path is actually used must be identified in its inference receipt.

## Receipt integrity

| Receipt | SHA-256 |
|---|---|
| inventory.json | `2a485d1e92ca31051a9869fc0473b16c6dc782bab06692dfb53a9b3fc4f14c8a` |
| pack-metadata-comparison.json | `06a60c42b10d6eda80743906451fa820e8a5b2a6779a6d84c302c9018caa9a55` |
| pack-dense-comparison.json | `aac27c28b52300e5ee5c87dd253382e30679688c5343e54863259c2f1a0985ef` |
| q2-model-source-hashes.json | `560fcb1126d0e65d0b4f0a7ea1802c2cf1b4cf1c2c35dfeafb1e4d559648f553` |
| hikari-model-source-hash.json | `4491a6ae2becaca675ac9c0630ac22bfde93ca46b88ac55505f07c760462abaf` |

Residual work: reliable bounded Windows process execution, current CPU/CUDA qualification, a completed source-bound native executable, real mandatory-model generation, the full 4K/32K comparison, distribution acceptance and formal publication. No old PASS was promoted to a new runtime result.
