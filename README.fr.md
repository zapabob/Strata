<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <b>Français</b> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Cache KV Triality Spin(8), Dialectes CUDA TurboQuant & Moteur d'Inférence MoE Natif</h3>

<p align="center">
  <b>Fork d'ingénierie de <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Attention Triality Spin(8) $\mathrm{Cl}(8,0)$ · Cache KV Quantifié à Trois Vues · Sidecars Query-v3 `.prismq3` · Contrôle Complet GUI & CLI
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Présentation de ce Fork (`zapabob/Strata`)

**`zapabob/Strata`** est un fork de recherche et d'ingénierie basé sur [Strata](https://github.com/Niko1221/Strata) (v0.2.2 / moteur 0.1.47). En plus d'exécuter localement des modèles Mixture-of-Experts de 125 milliards de paramètres (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) sur un seul PC en répartissant les experts entre la VRAM du GPU, la RAM système et le SSD, ce fork intègre une pile complète **Spin(8) Triality & Cache KV TurboQuant** dans le moteur C++/CUDA, le serveur Python, le CLI et l'interface graphique Desktop/Web :

### Les 4 Innovations Clés de ce Fork

1. **Bibliothèque de Transformations Orthogonales Spin(8) Triality & $\mathrm{Cl}(8,0)$ ([`spin8/`](spin8/README.md))**
   - Fondée sur la base réelle des octonions ($1, e_1, \dots, e_7$) et les générateurs symétriques $\mathrm{Cl}(8,0)$ ($\Gamma_0, \dots, \Gamma_7$).
   - Décompose les spineurs 16×16 selon la chiralité en trois représentations de dimension 8 : **Vecteur ($V$)**, **Demi-Spin Positif ($S_+$)** et **Demi-Spin Négatif ($S_-$)**, vérifiant la relation d'entrelacement $U \Gamma(v) U^\top = \Gamma(Rv)$.
   - Chaque plan de rotation est audité mathématiquement avant admission : erreur d'orthogonalité de Frobenius $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$, erreur maximale de Gram $\le 10^{-12}$ et log-déterminant signé par factorisation LU avec pivot ($\operatorname{sign}=+1, |\log|\det|| \le 10^{-12}$).
   - Inclut les transformations de Sylvester Hadamard normalisées ($n = 1 \dots 1024$, y compris les masques Spin(8) 8D et les blocs Bonsai 128D) ainsi qu'un moniteur d'audit persistant (`spin8_monitor`) vérifiant les invariants tous les 1 024 tokens ou 60 secondes.

2. **Cache KV Triality à Trois Vues & Dialectes CUDA Asynchrones TurboQuant ([`tqcodec/`](tqcodec/README.md))**
   - **Cache CUDA physique à trois vues (`cache_cuda.cu`)** : Maintient trois tableaux de clés (K) tournées physiquement indépendants ($V, S_+, S_-$) et un tableau de valeurs (V) quantifié partagé par tête d'attention, évalués via un softmax en ligne à passe unique avec poids de consensus sur le simplexe $(\alpha_0, \alpha_1, \alpha_2)$ et correction résiduelle gaussienne **QJL**.
   - **Dialectes CUDA asynchrones exacts** : `TQ4_1S` (4,25 bits/poids), `TQ3_0S` (3,3125 bits/poids) et `PQ2_0` (2,50 bits/poids).
   - **Optimisation de la mémoire partagée dynamique pour SM120 (RTX série 50)** : Le noyau `audit_kernel` utilise désormais la mémoire partagée dynamique (`65 536` octets) au lieu de tableaux locaux `float f[128 * 128]` (64 Kio/thread), éliminant la réservation de pile CUDA de **3,375 Gio (`3 623 878 656 o`)** lors de `tqc_cache_cuda_initialize` (`audit_local=0`, `audit_delta=0`) et permettant aux trois vues (`off`, `f32`, `compressed`) de fonctionner de manière fiable sur un GPU de 16 Gio / 32 Gio de RAM.

3. **Adaptateur Query-v3 Versionné & Sidecars `.prismq3`**
   - Implémente une carte tangente rationnelle bornée sur les 7 générateurs antisymétriques dérivés des blocs $\mathrm{Cl}(8,0)$ audités, pilotée par un contrôleur de rang 8 sur les requêtes normalisées ($Q$) avant l'encodage positionnel (RoPE).
   - Prend en charge l'exécution CUDA fusionnée sans allocation (`query_v3_cuda.h`) et les fichiers sidecars `.prismq3` liés par SHA-256 (`--query-v3-sidecar`) pour **Prism / TheTom (`qwen35-9b-thetom-q2kxl`)** et **Hikari / Bonsai (`bonsai-8b-prism-q1_0_g128`)**.

4. **Intégration Transparente GUI, CLI & Serveur**
   - **Interface Desktop & Web (`apps/host`)** : Configurez **K cache type**, **V cache type** (`f16`, `tq3`, `tq3_spin8_hadamard`, `tq3_spin8_native`), **Spin(8) KV cache mode** (`off`, `f32`, `compressed`), **Spin(8) native config path** et **Spin(8) native config SHA-256** directement dans **Settings → GPU & memory**, avec validation pré-lancement en temps réel (`run-config-check.mjs`).
   - **CLI & Serveur Python (`strata_cli`, `strata_control`, `serve/server.py`)** : Prise en charge complète via `strata launch --set ...` et `strata serve` avec vérification préalable de la capsule JSON et de son empreinte SHA-256.

---

## Dernière Version du Fork : `v0.3.0-preview.20261024.2`

- **Page de publication** : [GitHub Release `v0.3.0-preview.20261024.2`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2)
- **Archive complète (Moteur + GUI + Control)** : `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z`
  - **Taille** : `412 311 508` octets
  - **SHA-256 de l'archive** : `7639fb8ffb3c8fd13857a59c6b5d9d8b392c8b82a496442f0486a9405fd16e21`
  - **SHA-256 du moteur (`strata.exe`)** : `564e23b5bcd2b0670d0a2d82e7cd2c20cd5afedf85ddca7c653bea11403727db`
- **Aperçu CLI précédent** : [`v0.3.0-preview.20261024.1`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.1) · [Notes techniques](docs/releases/preview030.md) · [PoC Triality](research/triality_poc/README.md)

---

## Démarrage Rapide (Fonctionnalités du Fork)

### 1. Depuis l'interface graphique (GUI)

1. Extrayez `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z` (d'abord le `.7z`, puis le `.tar`) ou copiez les fichiers dans `%LOCALAPPDATA%\Programs\Strata` et `%LOCALAPPDATA%\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13`.
2. Ouvrez **Settings → GPU & memory**.
3. Sélectionnez vos options de cache KV et Spin(8) (`cache_type_k`, `cache_type_v`, `spin8_mode`, `spin8_native_config`, `spin8_native_sha256`).

### 2. Depuis le Terminal (`strata` CLI)

```powershell
# Lancement par défaut (compatible upstream)
strata launch --model q2_0 --yes --no-tui

# Lancement avec cache KV TurboQuant 3 bits et rotation de Hadamard
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_hadamard \
  --set cache_type_v=tq3_spin8_hadamard \
  --yes --no-tui

# Lancement avec capsule native Spin(8) à trois vues vérifiée par SHA-256
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_native \
  --set cache_type_v=tq3_spin8_native \
  --set spin8_mode=compressed \
  --set spin8_native_config=C:\chemin\vers\capsule.json \
  --set spin8_native_sha256=<64-hex-sha256> \
  --yes --no-tui
```

---

## Configuration Requise & Modèles Pris en Charge

**Au moins 32 Go de mémoire combinée (RAM système + VRAM GPU)** sont nécessaires. Strata expose des API compatibles OpenAI (`/v1/chat/completions`, `/v1/responses`) et Anthropic (`/v1/messages`) pour Claude Code, Codex CLI et OpenCode.

| Mémoire combinée (RAM + VRAM) | Modèle recommandé | Description |
| --- | --- | --- |
| **28–32 Go** | **[Gyro-S](docs/GYRO.md)** (27,6 Go) ou **[Coder](docs/MODELS.md#coder)** | Gyro-S pour les configurations serrées ; Coder conserve la moitié des experts pour le code. |
| **35–40 Go** | **[Swift 1.5](docs/MODELS.md#swift-15)** IQ2_XS (39,2 Go) ou **Gyro-M** (35 Go) | Swift 1.5 réfléchit plus vite ; Gyro-M approche la qualité d'IQ3_XXS avec ~20 % de VRAM en moins. |
| **48 Go** | **IQ3_XXS** (47,0 Go) | Meilleure précision que les quantifications 2 bits. |
| **64 Go** | **IQ3_S** (54,8 Go) ou **Q2_0** | IQ3_S égale le modèle complet sur les benchmarks ; Q2_0 offre une vitesse maximale (94 tok/s sur RTX 5070). |
| **96 Go et plus** | **UD-IQ4_XS** (72 Go) à **Q8_0** (136 Go), **[NVFP4](docs/NVFP4.md)** | Versions 4 à 8 bits lorsque tous les experts tiennent en RAM. |

---

## Compilation et Tests depuis les Sources

```powershell
# Bibliothèque de référence Spin(8) (CPU)
cmake -S spin8 -B build\spin8-cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF
cmake --build build\spin8-cpu --config Release
ctest --test-dir build\spin8-cpu -C Release --output-on-failure

# Tests d'intégration tqcodec (CPU + CUDA + Spin8)
cmake -S tqcodec -B build\tqcodec-cuda -G "Visual Studio 17 2022" -A x64 -DTQCODEC_ENABLE_CUDA=ON -DTQCODEC_SPIN8_TESTS=ON
cmake --build build\tqcodec-cuda --config Release
ctest --test-dir build\tqcodec-cuda -C Release --output-on-failure

# Moteur CUDA natif (strata.exe / spin8_verify)
cmake -S . -B build\engine-cuda -G "Visual Studio 17 2022" -A x64 -DSTRATA_CUDA=ON
cmake --build build\engine-cuda --config Release --target strata spin8_verify

# Interface Host GUI & tests de contrôle
pnpm --dir apps/host typecheck
pnpm --dir apps/host build
node --test apps/host/tests/native-settings.test.mjs apps/host/tests/spin8-backend.test.mjs apps/host/tests/kv-settings.test.mjs apps/host/tests/kv-engine.test.mjs
py -3 -m pytest -p no:randomly tests/terminal/test_profiles.py
```

---

## Crédits & Licence

- **Ingénierie du Fork (`zapabob/Strata`)** : Cache Triality Spin(8) $\mathrm{Cl}(8,0)$, dialectes CUDA `tqcodec`, adaptateur Query-v3 `.prismq3`, optimisation de mémoire partagée dynamique SM120 `audit_kernel` et intégration complète GUI/CLI.
- **Projet Upstream ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))** : Moteur de streaming MoE à trois niveaux, cache d'experts, décodage spéculatif, application Desktop et Terminal CLI.
- **Licence** : Distribué sous [Licence MIT](LICENSE). Les bibliothèques redistribuables CUDA/cuBLAS et Microsoft Visual C++ incluses dans les archives conservent leurs licences respectives.
