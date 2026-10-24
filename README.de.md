<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <b>Deutsch</b> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8)-Triality-KV-Cache, DeepSeek-V4.1 Unzensiert, Beliebige GGUF & Langzeitgedächtnis</h3>

<p align="center">
  <b>Engineering-Fork von <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Upstream integriert · Spin(8)-$\mathrm{Cl}(8,0)$-Triality-Attention · DeepSeek-V4.1-Flash MLA Unzensiert · Inhaltsgeprüfte GGUF-Modelle · Hermes & Hakua Langzeitgedächtnis · 32 GB RAM optimiert
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Überblick über diesen Fork (`zapabob/Strata`)

**`zapabob/Strata`** ist ein spezialisierter Engineering-Fork von [Strata](https://github.com/Niko1221/Strata), synchronisiert mit der neuesten Upstream-Version v0.2.4.2 / Engine 0.1.49.2. Neben der Ausführung von 125-Milliarden-Parameter-MoE-Modellen (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) auf einem einzelnen PC über GPU-VRAM, System-RAM und SSD erweitert dieser Fork das System um **Spin(8)-Triality-KV-Cache**, **DeepSeek-V4.1 unzensierte Derivate**, **inhaltsadressierte GGUF-Modellprüfung** und **Agenten-Langzeitgedächtnis**:

1. **Spin(8)-Triality & $\mathrm{Cl}(8,0)$-Orthogonaltransformationen ([`spin8/`](spin8/README.md))**
   - Basiert auf der reellen Oktonionen-Basis ($1, e_1, \dots, e_7$) und symmetrischen $\mathrm{Cl}(8,0)$-Generatoren.
   - Zerlegt 16×16-Clifford-Spinoren in drei 8-dimensionale Darstellungen: **Vektor ($V$)**, **Positiver Halb-Spin ($S_+$)** und **Negativer Halb-Spin ($S_-$)**.
   - Mathematische Auditierung aller Transformationspläne vor Zulassung ($E_F \le 10^{-12}$).
   - Normierte Sylvester-Hadamard-Transformationen und Invarianten-Audit (`spin8_monitor`).

2. **Drei-Ansichten-KV-Cache & TurboQuant-CUDA-Dialekte ([`tqcodec/`](tqcodec/README.md))**
   - **Physischer CUDA-Drei-Ansichten-Cache (`cache_cuda.cu`)**: Getrennte Key-Arrays ($V, S_+, S_-$), geteiltes quantisiertes Value-Array, Online-Softmax und **QJL**-Residuenausgleich.
   - **Asynchrone Dialekte**: `TQ4_1S` (4,25 bpw), `TQ3_0S` (3,3125 bpw) und `PQ2_0` (2,50 bpw).
   - **SM120-Optimierung (RTX 50-Serie)**: Dynamischer Shared Memory spart 3,375 GiB VRAM-Stackreservierung ein.

3. **DeepSeek-V4.1-Flash-1017 Unzensierte Derivate & MLA-Backend ([`strata_control/backends/dsv41.py`](strata_control/backends/dsv41.py))**
   - Native Unterstützung von Multi-Head Latent Attention (MLA) über das dedizierte `strata-dsv41`-Backend.
   - Qualifizierte Modelle: ISTA-Baseline, Kiwimaker Maya-S abliteriertes Slot-Rezept und AtomicChat Standalone-Modell.
   - Automatische Unterdrückung von Refusal-Steering bei abliterierten Modellen zur Vermeidung von Verzerrungen.

4. **Inhaltsadressierter GGUF-ModelBundle-Resolver & Lokaler Router ([`strata_control/model_bundle.py`](strata_control/model_bundle.py))**
   - Beschränkte Header-Prüfung ($\le 16$ MiB) mit Überlaufschutz ($\operatorname{rank} \le 4, \operatorname{dim} \le 2^{30}$, Schutz vor GHSA-vgg9-87g3-85w8).
   - Streaming-SHA-256-Identität und Drift-Erkennung gegen Manipulation.
   - Deterministisches lokales Routing (`strata-dsv41`, `strata-native`, `prism`, `llama-cpp`) mit **striktem Verbot von Cloud-Fallbacks** (100% Offline-Privatsphäre).

5. **Hermes Agent & Hakua Langzeitgedächtnis ([`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py))**
   - Standard-MCP-Server + CLI:
     - `SOUL.md`: Hakua-Ausrichtung und Kernpersönlichkeit mit automatischem Backup.
     - `MEMORY.md`: Strukturierte Notizen im Format `§ [category] YYYY-MM-DD: Title`.
     - Hermes Agent SQLite-Speicher (`~/.hermes/ebbinghaus_memory.db`, ~5.000 Einträge).
     - Hakua Composite Memory (`~/.hakua-memory`).
   - Automatische Prompt-Injektion via `apps/host/server/memory.mjs`.

6. **32 GB RAM / 16 GB VRAM Hardware-Budget & Zero-VRAM-Drafter-Lebenszyklus**
   - Verifiziert auf Windows 11 mit 32 GB RAM und RTX 5060 Ti 16 GB (`sm_120`).
   - Einhaltung der Grenzwerte: Host-RAM $\le 24.0$ GiB, OS-Reserve $\ge 4.0$ GiB, VRAM $\le 14.0$ GiB.
   - Automatisches Entladen des Draft-Modells bei Speicherdruck zur Schonung des VRAMs.

---

## Verifikationsstatus & Upstream-Integration: `v0.3.0` Upstream Integrated Edition

- **Upstream SHA**: `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`
- **GUI-Sicherheitsfix**: `c487c875d05075113965bc61d822b27179f70639`
- **Alle 11 Fork-Verträge (F01–F11)** vollständig gewahrt.
- **Testergebnisse**: **71/71 Python-Tests bestanden** (`pytest -p no:randomly`), **13/13 Node-Host-Tests bestanden** (`apps/host`).

---

## Lizenz

Veröffentlicht unter der [MIT License](LICENSE).
