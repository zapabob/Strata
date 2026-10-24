<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <b>Deutsch</b> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8)-Triality-KV-Cache, TurboQuant-CUDA-Dialekte & Native MoE-Inferenz-Engine</h3>

<p align="center">
  <b>Engineering-Fork von <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Spin(8)-$\mathrm{Cl}(8,0)$-Triality-Attention · Drei-Ansichten-KV-Cache · Query-v3-`.prismq3`-Sidecars · Vollständige GUI- & CLI-Steuerung
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Überblick über diesen Fork (`zapabob/Strata`)

**`zapabob/Strata`** ist ein spezialisierter Forschungs- und Engineering-Fork von [Strata](https://github.com/Niko1221/Strata) (v0.2.2 / Engine 0.1.47). Neben der Ausführung von 125-Milliarden-Parameter-MoE-Modellen (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) auf einem einzelnen PC über GPU-VRAM, System-RAM und SSD erweitert dieser Fork die C++/CUDA-Engine, den Python-Server, die CLI und die Desktop-/Web-GUI um einen vollständigen **Spin(8)-Triality- & TurboQuant-KV-Cache-Stack**:

### Die vier Kernfunktionen dieses Forks

1. **Spin(8)-Triality- & $\mathrm{Cl}(8,0)$-Orthogonaltransformations-Bibliothek ([`spin8/`](spin8/README.md))**
   - Basiert auf der reellen Oktonionen-Basis ($1, e_1, \dots, e_7$) und symmetrischen $\mathrm{Cl}(8,0)$-Generatoren ($\Gamma_0, \dots, \Gamma_7$).
   - Zerlegt 16×16-Clifford-Spinoren nach Chiralität in drei 8-dimensionale Darstellungen: **Vektor ($V$)**, **Positiver Halb-Spin ($S_+$)** und **Negativer Halb-Spin ($S_-$)** unter Erfüllung der Triality-Intertwiner-Relation $U \Gamma(v) U^\top = \Gamma(Rv)$.
   - Jeder Rotationsplan wird vor der Zulassung mathematisch geprüft: Frobenius-Orthogonalitätsfehler $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$, maximaler Gram-Eintragsfehler $\le 10^{-12}$ sowie vorzeichenbehaftete Log-Determinante über pivotierte LU-Zerlegung ($\operatorname{sign}=+1, |\log|\det|| \le 10^{-12}$).
   - Enthält normierte Sylvester-Hadamard-Transformationen für Zweierpotenz-Blöcke ($n = 1 \dots 1024$, einschließlich 8D-Spin(8)-Masken und 128D-Bonsai-Blöcken) sowie einen Laufzeit-Monitor (`spin8_monitor`), der alle 1.024 Tokens oder 60 Sekunden Invarianten prüft.

2. **Drei-Ansichten-Triality-KV-Cache & Asynchrone TurboQuant-CUDA-Dialekte ([`tqcodec/`](tqcodec/README.md))**
   - **Physischer CUDA-Drei-Ansichten-Cache (`cache_cuda.cu`)**: Verwaltet drei physisch getrennte rotierte Key-Arrays ($V, S_+, S_-$) und ein gemeinsames quantisiertes Value-Array pro Attention-Head, ausgewertet mittels Online-Softmax, Simplex-Konsensgewichten $(\alpha_0, \alpha_1, \alpha_2)$ und optionaler Gaußscher **QJL**-Residuenkorrektur.
   - **Exakte asynchrone CUDA-Quantisierungsdialekte**: `TQ4_1S` (4,25 bpw), `TQ3_0S` (3,3125 bpw) und `PQ2_0` (2,50 bpw).
   - **VRAM-Stack-Optimierung für SM120 (RTX-50-Serie)**: Dynamischer Shared Memory (`65.536` Bytes) in `audit_kernel` ersetzt thread-lokale `float f[128 * 128]`-Arrays (64 KiB/Thread) und beseitigt so **3,375 GiB (`3.623.878.656 B`)** an CUDA-Stack-Reservierungen bei `tqc_cache_cuda_initialize` (`audit_local=0`, `audit_delta=0`). Dadurch werden ~3,3 GiB VRAM für den Experten-Cache frei und alle drei Ansichten (`off`, `f32`, `compressed`) laufen zuverlässig auf einer 16-GiB-GPU mit 32 GiB System-RAM.

3. **Versionierter Query-v3-Adapter & `.prismq3`-Sidecars**
   - Implementiert eine beschränkte rationale Tangentialkarte auf den 7 schiefsymmetrischen Generatoren aus geprüften $\mathrm{Cl}(8,0)$-Blöcken, gesteuert durch einen Rang-8-Controller auf normalisierten Queries ($Q$) vor der Positionskodierung (RoPE).
   - Unterstützt allokationsfreie fusionierte CUDA-Kernels (`query_v3_cuda.h`) sowie kryptografisch gebundene `.prismq3`-Sidecars (`--query-v3-sidecar`) für **Prism / TheTom (`qwen35-9b-thetom-q2kxl`)** und **Hikari / Bonsai (`bonsai-8b-prism-q1_0_g128`)**.

4. **Nahtlose Integration in GUI, CLI und Control-Plane**
   - **Desktop- & Web-GUI (`apps/host`)**: Direkte Auswahl von **K cache type**, **V cache type** (`f16`, `tq3`, `tq3_spin8_hadamard`, `tq3_spin8_native`), **Spin(8) KV cache mode** (`off`, `f32`, `compressed`), **Spin(8) native config path** und **Spin(8) native config SHA-256** unter **Settings → GPU & memory** inklusive Echtzeit-Preflight-Prüfung (`run-config-check.mjs`).
   - **CLI & Python-Server (`strata_cli`, `strata_control`, `serve/server.py`)**: Vollständige Unterstützung über `strata launch --set ...` und `strata serve` mit automatischer Kapsel- und SHA-256-Verifizierung.

---

## Aktuelles Fork-Release: `v0.3.0-preview.20261024.2`

- **Release-Seite**: [GitHub Release `v0.3.0-preview.20261024.2`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2)
- **Komplettarchiv (Engine + GUI + Control)**: `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z`
  - **Größe**: `412.311.508` Bytes
  - **SHA-256**: `7639fb8ffb3c8fd13857a59c6b5d9d8b392c8b82a496442f0486a9405fd16e21`
  - **Engine (`strata.exe`) SHA-256**: `564e23b5bcd2b0670d0a2d82e7cd2c20cd5afedf85ddca7c653bea11403727db`
- **Vorheriges CLI-Preview**: [`v0.3.0-preview.20261024.1`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.1) · [Technische Release-Notes](docs/releases/preview030.md) · [Triality-PoC](research/triality_poc/README.md)

---

## Schnellstart (Fork-Funktionen)

### 1. Konfiguration in der GUI

1. Entpacke `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z` (zuerst `.7z`, dann `.tar`) oder überschreibe deine lokale Installation unter `%LOCALAPPDATA%\Programs\Strata` und `%LOCALAPPDATA%\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13`.
2. Öffne **Settings → GPU & memory**.
3. Wähle die gewünschten KV-Cache- und Spin(8)-Parameter (`cache_type_k`, `cache_type_v`, `spin8_mode`, `spin8_native_config`, `spin8_native_sha256`).

### 2. Start über die `strata`-CLI

```powershell
# Standardstart (identisch mit Upstream)
strata launch --model q2_0 --yes --no-tui

# Start mit Hadamard-rotiertem TurboQuant 3-Bit KV-Cache
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_hadamard \
  --set cache_type_v=tq3_spin8_hadamard \
  --yes --no-tui

# Start mit verifizierter Spin(8)-Drei-Ansichten-Kapsel
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_native \
  --set cache_type_v=tq3_spin8_native \
  --set spin8_mode=compressed \
  --set spin8_native_config=C:\pfad\zur\capsule.json \
  --set spin8_native_sha256=<64-hex-sha256> \
  --yes --no-tui
```

---

## Systemanforderungen & Modellgrößen

**Mindestens 32 GB kombinierter Arbeitsspeicher (RAM) und Grafikspeicher (VRAM)** werden benötigt. Strata bietet OpenAI- (`/v1/chat/completions`, `/v1/responses`) und Anthropic-kompatible (`/v1/messages`) Endpunkte für Claude Code, Codex CLI und OpenCode.

| Speicher (RAM + VRAM) | Empfohlenes Modell | Hinweise |
| --- | --- | --- |
| **28–32 GB** | **[Gyro-S](docs/GYRO.md)** (27,6 GB) oder **[Coder](docs/MODELS.md#coder)** | Gyro-S für knappen Speicher; Coder behält die Hälfte der Experten für Programmieraufgaben. |
| **35–40 GB** | **[Swift 1.5](docs/MODELS.md#swift-15)** IQ2_XS (39,2 GB) oder **Gyro-M** (35 GB) | Swift 1.5 antwortet mit kürzerer Denkzeit; Gyro-M spart ~20 % GPU-Speicher bei nahezu IQ3_XXS-Qualität. |
| **48 GB** | **IQ3_XXS** (47,0 GB) | Höhere Präzision als 2-Bit-Modelle. |
| **64 GB** | **IQ3_S** (54,8 GB) oder **Q2_0** | IQ3_S erreicht volle Modellqualität in Benchmarks; Q2_0 liefert maximale Geschwindigkeit (94 tok/s auf RTX 5070). |
| **96 GB+** | **UD-IQ4_XS** (72 GB) bis **Q8_0** (136 GB), **[NVFP4](docs/NVFP4.md)** | 4- bis 8-Bit-Modelle, wenn alle Experten in den RAM passen. |

---

## Aus dem Quellcode bauen und testen

```powershell
# Spin(8)-CPU-Referenz & Tests
cmake -S spin8 -B build\spin8-cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF
cmake --build build\spin8-cpu --config Release
ctest --test-dir build\spin8-cpu -C Release --output-on-failure

# tqcodec CPU + CUDA + Spin(8)-Tests
cmake -S tqcodec -B build\tqcodec-cuda -G "Visual Studio 17 2022" -A x64 -DTQCODEC_ENABLE_CUDA=ON -DTQCODEC_SPIN8_TESTS=ON
cmake --build build\tqcodec-cuda --config Release
ctest --test-dir build\tqcodec-cuda -C Release --output-on-failure

# Native CUDA-Engine (strata.exe / spin8_verify)
cmake -S . -B build\engine-cuda -G "Visual Studio 17 2022" -A x64 -DSTRATA_CUDA=ON
cmake --build build\engine-cuda --config Release --target strata spin8_verify

# Host-GUI & Control-Tests
pnpm --dir apps/host typecheck
pnpm --dir apps/host build
node --test apps/host/tests/native-settings.test.mjs apps/host/tests/spin8-backend.test.mjs apps/host/tests/kv-settings.test.mjs apps/host/tests/kv-engine.test.mjs
py -3 -m pytest -p no:randomly tests/terminal/test_profiles.py
```

---

## Credits & Lizenz

- **Fork-Entwicklung (`zapabob/Strata`)**: Spin(8)-$\mathrm{Cl}(8,0)$-Triality-Cache, `tqcodec`-CUDA-Dialekte, Query-v3-`.prismq3`-Integration, SM120-`audit_kernel`-Shared-Memory-Optimierung und GUI/CLI-Integration.
- **Upstream ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))**: Drei-Stufen-MoE-Engine, Experten-Cache, spekulatives Decoding, Desktop-App und Terminal-CLI.
- **Lizenz**: Veröffentlicht unter der [MIT-Lizenz](LICENSE). Mitgelieferte CUDA/cuBLAS- und Microsoft-VC++-Laufzeitbibliotheken unterliegen den jeweiligen Herstellerbedingungen.
