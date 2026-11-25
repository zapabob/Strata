# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

**Lokale KI, die sämtliche Ressourcen Ihres Windows-PCs ausschöpft — GPU, physische + SMT-CPU-Threads, Arbeitsspeicher und NVMe/SSD-Speicher.** Hakua ist der eigenständige `zapabob/Strata`-Fork von [Niko1221/Strata](https://github.com/Niko1221/Strata) auf Basis von Upstream **v0.2.21** (`d46f5f268`, Engine/Control `0.1.67`) und bewahrt alle Fork-spezifischen Runtimes, Speicher-/Agenten-Workflows sowie Blackwell-CUDA-13.5-Optimierungen.

## Neuerungen in 0.8.1 (Engine 0.7.0)

- **Heterogene Full-Machine-Inferenz über alle 4 Hardware-Stufen (GPU + 6P/6SMT-CPU + RAM + SSD)**:
  - **Natives Windows-`aux_cpus` mit CPU Sets & SMT-I/O-Trennung** (`aux_cpus.hpp`, `ssd_stream_scheduler.hpp`, `direct_file.cpp`): bindet GPU-Host- und AVX2-MoE-Compute strikt an physische Primärkerne und reserviert alle SMT-Sekundärthreads (`io_smt=[1,3,5,7,9,11]` bei 6C/12T) für 6-Thread-Overlapped-Direct-I/O und asynchrones `PrefetchVirtualMemory`.
  - **5 frisch kompilierte CUDA-13.5-/SM120-Blackwell-Engines** (`strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`): Gen-K/L-Zero-Copy-Doorbells, WDDM-1536-MiB-VRAM-Schutz, Windows-Commit-sichere RAM-Budgets (`hy4_cpu_experts.cpp`, `inkling2_engine.cu`), Windows-Kern-Pinning mit `_mm_pause` (`ink_hybrid.cuh`) sowie SM120-Q38-Pinned-Embedding-Staging + gebündeltes `PrefetchVirtualMemory` (`engine/q38/src/engine.cu`).
  - **Einheitlicher Full-Machine-Launcher & Presets**: `tools/full_machine_infer.py` (`--list-models`, `--plan`, `--bench`, `--serve`) erkennt GPU, physische/SMT-Kerne, RAM/Commit-Reserven und SSDs automatisch und erzeugt optimale 3-Tier-Pläne sowie Server-Konfigurationen unter `configs/`.
- **Offizieller Upstream-v0.2.21-3-Way-Merge**: übernimmt das offizielle 4-Tier-GPU+RAM+CPU+SSD-MoE, Multi-GPU-`--layer-split`, GUI-Abgleich und Control/Engine-`0.1.67`-Fixes bei vollständigem Erhalt aller Fork-Funktionen (`/btw`, `/deepresearch`, RustXNG Full, Workflow-Skills, Q38-Dense-Runner, DeepSeek-Erweiterung, Hermes-`inkling2`-Provider und kuraneko1s MIT-Profiltabellen).

## Reale Hardware-Messwerte

Gemessen auf **NVIDIA GeForce RTX 5060 Ti 16 GB (SM120, CUDA 13.5) · AMD Ryzen 5 4500 (6C/12T) · 32 GB DDR4 · Dual-SSD (`C:` Crucial P3 NVMe + `H:` S5-1TB SSD)** mit 16-Token-Prompt und 32-Token-Greedy-Decode:

| Modell (Größe) | Engine & Kontext | Aktive Stufen | Prefill (`pp`) | Decode (`tg`) | Parität |
|---|---|---|---:|---:|---|
| **Sakura Inkling-2-Mini Q4_K_M** (16,28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | GPU 10,85 GiB (2232 Exps) + Pinned RAM 4,34 GiB (840 Exps) + 6P/6SMT | **85,08 t/s** | **42,22–42,33 t/s** | **32/32 exakt** |
| **Sakura Inkling-2-Mini Q4_K_M** (16,28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | 3-Tier-Spill: GPU 10,85 GiB + RAM 3,60 GiB + **SSD mmap 0,74 GiB (`prefetch=on`)** + 6P/6SMT | 64,80 t/s | 14,24 t/s | **32/32 exakt** |
| **Inkling-2-Mini UD Q4_K_M** (15,47 GiB) | `strata-inkling2.exe` · 16K (Q8 KV) | GPU 10,42 GiB (2339 Exps) + Pinned RAM 3,34 GiB (733 Exps) + 6P/6SMT | **109,64 t/s** | **53,28 t/s** | Sauber |
| **Qwen3.8-27B 3.69bpw MTP** (11,73 GiB) | `strata-q38.exe` · 4K (F16 KV) | GPU-SM120-Gewichte (10,44 GiB) + Pinned-Emb-Staging + `PrefetchVirtualMemory` | 6,21 s (kalt) | **29,95 t/s** | Sauber |

*CPU-Threading-Messung (Ryzen 5 4500 A/B)*: 6 physische Compute-Kerne + 6 SMT-I/O-Threads erreichten **42,22–42,33 t/s** gegenüber **29,68 t/s** (-21,9 %) bei Überbelegung mit 11 Compute-Workern.

## Version und Downloads

Aktuelles Release: **0.8.1** — GitHub Latest: [v0.8.1-Release-Seite](https://github.com/zapabob/Strata/releases/tag/v0.8.1)

- **Desktop-Installer**: `Strata-0.8.1-windows-x64-setup.exe` (Benutzer-Installation per Tauri/NSIS mit eigenem Node 24.22.3, Python, Control 0.6.3 und RustXNG Full).
- **Installer-Paket**: `Strata-0.8.1-windows-x64.tar.7z` (Installer + `SHA256SUMS.txt`).
- **CUDA-13.5-SM120-Engine-Komponente (Opt-in)**: `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` (alle fünf neu gebauten SM120-Engines: `strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`).
- **Hy4-Flash-Komponente (Opt-in)**: `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`.

Laden Sie stets direkt aus den **Assets** der Release-Seite herunter und prüfen Sie die SHA-256-Prüfsummen. Die ed25519-Signaturprüfung ist entfernt (kein Signaturschlüssel); Windows-Authenticode fehlt; **`releaseQualified=false`**.

![Hakua / Strata real-model Japanese chat on Qwen3.8-27B](docs/media/native-qwen38-japanese-chat.png)
*Hakua / Strata Desktop mit `qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf` über `strata-q38.exe` (CUDA 13.5 / RTX 5060 Ti 16 GB).*

## Schnellstart (Desktop & Full-Machine-CLI)

### Desktop-Installation oder Überschreib-Update

1. Beenden Sie laufende Anfragen, entladen Sie Modelle, sichern Sie App-Daten und schließen Sie Strata inklusive Tray-Symbol.
2. Führen Sie `Strata-0.8.1-windows-x64-setup.exe` in den bestehenden Installationsordner aus — Modelle, Chats, Speicher, Tools, API-Schlüssel und Freigaben bleiben erhalten.
3. Importieren Sie `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` über *Ich habe die Datei bereits*, wählen Sie ein kompatibles Modell oder lokales GGUF und klicken Sie auf **Laden**. Details unter [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md).

### Full-Machine-Launcher (`tools/full_machine_infer.py`)

```powershell
# GPU/CPU/RAM/SSD-Stufen prüfen und lokale Modelle erkennen
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --list-models

# Sakura-Inkling-2-Mini-131K-Benchmark mit Full-Machine-Einstellungen
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --bench --model Sakura --max-new 32

# Lokalen OpenAI/Anthropic-API-Server (127.0.0.1:8092) mit RAM-Squeeze starten
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model Sakura --port 8092 --squeeze
```

## Empfohlenes GGUF & Fork-Funktionen

- **Qwen3.8-27B auf 16 GB VRAM**: getestet mit dem [3,69-bpw-Mixed-Quant-GGUF von soyaakinohara](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf) (Dank an **soyaakinohara** und **AEON-7**). Beginnen Sie mit 4.096 Kontext-Tokens; `12GB` im Dateinamen garantiert keinen Betrieb auf 12-GB-Karten.
- **Eigener Q38-Dense-Runner (`strata-q38.exe`)**: Tensor-spezifischer Polymorphismus für 11 Formate (`F32`–`PQ2_0`), Tensor-Core-Prefill, Spin(8)/TurboQuant-KV (`auto`: `f16` → `f16_turbo4` → `spin8_k8v4`), MTP `K=3` und optionales Japanisch-Profil ([QWEN38_DENSE_NATIVE.md](docs/QWEN38_DENSE_NATIVE.md)).
- **Agenten & Workflows**: werkzeugfreier `/btw`-Subagent mit eigener Stopp-Steuerung, `/research` & `/deepresearch` mit integriertem RustXNG Full (sendet bei Aktivierung Anfragen an externe Anbieter), optionale private Workflow-Skills, Sidebar-Dateioperationen und bereichsbezogener Chat-Speicher ([WORKFLOW_SKILLS.md](docs/WORKFLOW_SKILLS.md), [BROWSER_SEARCH.md](docs/BROWSER_SEARCH.md)).

## Schutzgrenzen und Einschränkungen

Unverändert: **>= 3 GiB freier RAM**, **>= 4 GiB Commit-Reserve**, **>= 768 MiB GPU-Reserve** (`1536 MiB` WDDM-Standard für Inkling-2 auf <= 17 GiB), **>= 5 GiB frei auf `C:`**, **>= 10 GiB frei auf `H:`**. Allgemeine Modellqualität, Vollkontext-Inferenz und gleichzeitige GPU-Last sind unqualifiziert (**`releaseQualified=false`**). Kein nativer Bildeingang und keine qualifizierte Linux/macOS-Inferenz in diesem Windows-Paket. Historische Nachweise: [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Dokumentation & Entwicklung

[Installation](docs/HAKUA_INSTALL.md) · [Release-Nachweise](docs/HAKUA_RELEASE.md) · [API & Hardware](docs/AI_REFERENCE.md) · [Terminal](docs/TERMINAL.md) · [Quell-Build](docs/SOURCE_INSTALL.md) · [Paketierung](tools/packaging/README.md) · [Mitwirken](.github/CONTRIBUTING.md) · [Sicherheit](.github/SECURITY.md) · [Lizenz](LICENSE)

```powershell
pytest tests/test_full_machine_infer.py
python -m pytest terminal/tests/terminal
```

```powershell
cd app/host
pnpm test
pnpm run build
```

[Niko1221/Strata](https://github.com/Niko1221/Strata) · [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [Drittanbieter-Hinweise](third_party/)

## Danksagung

Herzlichen Dank an **Niko1221/Strata**, **kuraneko1 (`_ryu15_`)**, **ggml & llama.cpp**, **NousResearch (Hermes Agent)**, **Qwen Team (Alibaba Cloud)**, **NVIDIA**, **RustXNG**, **libstrix**, **Node.js / Python / Tauri**, **Microsoft**, **ISTA-DASLab**, **PrismML**, **TurboQuant**, **Spin(8)**, **soyaakinohara** und **AEON-7**.
