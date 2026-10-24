# DeepSeek Derivative Qualification & Model Set Ledger

## Qualification Standards
- **Strict Provenance**: Every uncensored / abliterated variant is bound to an exact repository revision, file SHA-256, and verified shard recipe.
- **No Double-Apply**: A model with baked-in ablation vectors must not have runtime refusal-direction steering implicitly stacked on top.
- **Clear Identification**: A derivative shares the base architecture family name but possesses a unique cryptographic `model_set_id`.

## Target Candidates
1. **Base Reference**: `ISTA-DASLab/DeepSeek-V4.1-Flash-GGUF` (Standard baseline)
2. **Uncensored Replacement Derivative**: `Kiwimaker/DeepSeek-Maya-S-Abliterated` (Slot replacement recipe)
3. **Stand-alone Uncensored Derivative**: `AtomicChat/DeepSeek-V4.1-Uncensored-GGUF` (Full standalone bundle)
