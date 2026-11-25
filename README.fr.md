# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

**IA locale conçue pour exploiter chaque ressource de votre PC Windows — GPU, cœurs CPU physiques + threads SMT, RAM système et stockage NVMe/SSD.** Hakua est le fork indépendant `zapabob/Strata` de [Niko1221/Strata](https://github.com/Niko1221/Strata), aligné sur l’amont officiel **v0.2.21** (`d46f5f268`, moteur/Control `0.1.67`) tout en conservant les moteurs propres au fork, les workflows agents/mémoire et les optimisations Blackwell CUDA 13.5.

## Nouveautés de 0.8.1 (Moteur 0.7.0)

- **Inférence hétérogène pleine machine sur les 4 niveaux matériels (GPU + CPU 6P/6SMT + RAM + SSD)** :
  - **Backend Windows natif `aux_cpus` (CPU Sets) + séparation SMT I/O** (`aux_cpus.hpp`, `ssd_stream_scheduler.hpp`, `direct_file.cpp`) : fixe la boucle hôte GPU et le calcul MoE AVX2 sur les cœurs physiques primaires tout en dédiant tous les threads secondaires SMT (`io_smt=[1,3,5,7,9,11]` sur 6C/12T) aux entrées/sorties Direct I/O asynchrones (6 threads) et au préchargement `PrefetchVirtualMemory`.
  - **5 moteurs natifs CUDA 13.5 / SM120 Blackwell fraîchement compilés** (`strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`) : sonnettes mappées zéro-copie Gen-K/L, réserve WDDM 1536 Mio (zéro débordement en mémoire partagée), budgets RAM compatibles avec la limite de validation Windows (`hy4_cpu_experts.cpp`, `inkling2_engine.cu`), affinité physique Windows + `_mm_pause` (`ink_hybrid.cuh`), et tampon épinglé d’embeddings + `PrefetchVirtualMemory` par lot sur Q38 SM120 (`engine/q38/src/engine.cu`).
  - **Lanceur unifié et profils** : `tools/full_machine_infer.py` (`--list-models`, `--plan`, `--bench`, `--serve`) sonde GPU, topologie CPU physique/SMT, RAM/commit et SSD pour bâtir les plans 3 niveaux et les configurations serveur dans `configs/`.
- **Fusion 3 voies avec l’amont officiel v0.2.21** : intègre le MoE unifié 4 niveaux, `--layer-split` multi-GPU, la synchronisation GUI et les correctifs Control/moteur `0.1.67`, tout en préservant `/btw`, `/deepresearch`, RustXNG Full, les compétences de workflow, le moteur dense Q38, l’extension DeepSeek, le fournisseur Hermes `inkling2` et les tables de profils MIT de kuraneko1.

## Benchmarks mesurés sur matériel réel

Mesuré sur **NVIDIA GeForce RTX 5060 Ti 16 Go (SM120, CUDA 13.5) · AMD Ryzen 5 4500 (6C/12T) · 32 Go DDR4 · Double SSD (`C:` Crucial P3 NVMe + `H:` S5-1TB SSD)** (invite 16 jetons / décodage glouton 32 jetons) :

| Modèle (Taille) | Moteur & Contexte | Niveaux actifs | Prefill (`pp`) | Décodage (`tg`) | Parité |
|---|---|---|---:|---:|---|
| **Sakura Inkling-2-Mini Q4_K_M** (16,28 Gio) | `strata-inkling2.exe` · 131K (KV Q8) | GPU 10,85 Gio (2232 exps) + RAM épinglée 4,34 Gio (840 exps) + 6P/6SMT | **85,08 t/s** | **42,22–42,33 t/s** | **32/32 exact** |
| **Sakura Inkling-2-Mini Q4_K_M** (16,28 Gio) | `strata-inkling2.exe` · 131K (KV Q8) | 3 niveaux : GPU 10,85 Gio + RAM 3,60 Gio + **SSD mmap 0,74 Gio (`prefetch=on`)** + 6P/6SMT | 64,80 t/s | 14,24 t/s | **32/32 exact** |
| **Inkling-2-Mini UD Q4_K_M** (15,47 Gio) | `strata-inkling2.exe` · 16K (KV Q8) | GPU 10,42 Gio (2339 exps) + RAM épinglée 3,34 Gio (733 exps) + 6P/6SMT | **109,64 t/s** | **53,28 t/s** | Propre |
| **Qwen3.8-27B 3.69bpw MTP** (11,73 Gio) | `strata-q38.exe` · 4K (KV F16) | Poids GPU SM120 (10,44 Gio) + embeddings épinglés + `PrefetchVirtualMemory` | 6,21 s (froid) | **29,95 t/s** | Propre |

*Comparaison CPU A/B (Ryzen 5 4500)* : 6 cœurs physiques dédiés au calcul + 6 threads SMT pour les E/S atteignent **42,22–42,33 t/s**, contre **29,68 t/s** (-21,9 %) en sur-allouant 11 workers de calcul sur les threads SMT.

## Version et téléchargements

Version actuelle : **0.8.1** — GitHub Latest : [page de version v0.8.1](https://github.com/zapabob/Strata/releases/tag/v0.8.1)

- **Installateur Desktop** : `Strata-0.8.1-windows-x64-setup.exe` (installation par utilisateur Tauri/NSIS avec Node 24.22.3, Python, Control 0.6.3 et RustXNG Full embarqués).
- **Archive bundle** : `Strata-0.8.1-windows-x64.tar.7z` (installateur + `SHA256SUMS.txt`).
- **Composant moteur CUDA 13.5 SM120 (optionnel)** : `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` (les 5 moteurs SM120 recompilés : `strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`).
- **Composant Hy4-Flash (optionnel)** : `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`.

Téléchargez toujours depuis la section **Assets** et vérifiez les empreintes SHA-256. La vérification de signature ed25519 est retirée (aucune clé de signature) ; pas de signature Windows Authenticode ; **`releaseQualified=false`**.

![Hakua / Strata real-model Japanese chat on Qwen3.8-27B](docs/media/native-qwen38-japanese-chat.png)
*Hakua / Strata Desktop exécutant `qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf` via `strata-q38.exe` (CUDA 13.5 / RTX 5060 Ti 16 Go).*

## Démarrage rapide (Desktop & CLI pleine machine)

### Installation ou mise à jour par écrasement

1. Terminez les requêtes en cours, déchargez les modèles, sauvegardez vos données et quittez Strata (icône de la barre des tâches comprise).
2. Exécutez `Strata-0.8.1-windows-x64-setup.exe` dans le dossier existant pour mettre à jour en conservant modèles, discussions, mémoire, outils, clés API et autorisations.
3. Importez `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` via *J’ai déjà le fichier*, choisissez un modèle compatible ou un GGUF local et cliquez sur **Charger**. Voir [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md).

### Lanceur pleine machine (`tools/full_machine_infer.py`)

```powershell
# Inspecter GPU/CPU/RAM/SSD et découvrir les modèles locaux
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --list-models

# Benchmark Sakura Inkling-2-Mini 131K en mode pleine machine
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --bench --model Sakura --max-new 32

# Démarrer le serveur API OpenAI/Anthropic (127.0.0.1:8092) avec compression RAM
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model Sakura --port 8092 --squeeze
```

## GGUF recommandé et fonctionnalités du fork

- **Qwen3.8-27B sur 16 Go de VRAM** : testé avec le [GGUF mixte 3,69 bpw de soyaakinohara](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf) (merci à **soyaakinohara** et **AEON-7**). Commencez avec un contexte de 4 096 jetons ; `12GB` dans le nom ne garantit pas le fonctionnement sur une carte de 12 Go.
- **Moteur dense natif Q38 (`strata-q38.exe`)** : polymorphisme de quantification par tenseur sur 11 formats (`F32`–`PQ2_0`), prefill Tensor Core, caches KV Spin(8) / TurboQuant (`auto` : `f16` → `f16_turbo4` → `spin8_k8v4`), MTP `K=3` et profil japonais optionnel ([QWEN38_DENSE_NATIVE.md](docs/QWEN38_DENSE_NATIVE.md)).
- **Agents & workflows** : sous-agent sans outils `/btw` avec arrêt indépendant, `/research` et `/deepresearch` via RustXNG Full intégré (envoie les requêtes aux fournisseurs activés), apprentissage/application optionnels de compétences privées, CRUD fichiers et mémoire scopée ([WORKFLOW_SKILLS.md](docs/WORKFLOW_SKILLS.md), [BROWSER_SEARCH.md](docs/BROWSER_SEARCH.md)).

## Gardes de sécurité et limites

Seuils inchangés : **>= 3 Gio RAM libre**, **>= 4 Gio marge de commit**, **>= 768 Mio réserve GPU** (`1536 Mio` WDDM par défaut pour Inkling-2 <= 17 Gio), **>= 5 Gio sur `C:`** et **>= 10 Gio sur `H:`**. Qualité générale, contexte complet et concurrence GPU restent non qualifiés (**`releaseQualified=false`**). Aucune entrée image native ni validation Linux/macOS dans ce paquet Windows. Historique : [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Documentation et développement

[Installation](docs/HAKUA_INSTALL.md) · [Preuves de version](docs/HAKUA_RELEASE.md) · [API & matériel](docs/AI_REFERENCE.md) · [Terminal](docs/TERMINAL.md) · [Compilation](docs/SOURCE_INSTALL.md) · [Packaging](tools/packaging/README.md) · [Contribuer](.github/CONTRIBUTING.md) · [Sécurité](.github/SECURITY.md) · [Licence](LICENSE)

```powershell
pytest tests/test_full_machine_infer.py
python -m pytest terminal/tests/terminal
```

```powershell
cd app/host
pnpm test
pnpm run build
```

[Niko1221/Strata](https://github.com/Niko1221/Strata) · [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [Licences tierces](third_party/)

## Remerciements

Merci à **Niko1221/Strata**, **kuraneko1 (`_ryu15_`)**, **ggml & llama.cpp**, **NousResearch (Hermes Agent)**, **Qwen Team (Alibaba Cloud)**, **NVIDIA**, **RustXNG**, **libstrix**, **Node.js / Python / Tauri**, **Microsoft**, **ISTA-DASLab**, **PrismML**, **TurboQuant**, **Spin(8)**, **soyaakinohara** et **AEON-7**.
