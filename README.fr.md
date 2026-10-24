<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <b>Français</b> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Cache KV Spin(8) Triality, DeepSeek-V4.1 Sans Censure, Chargeur GGUF & Mémoire Long Terme</h3>

<p align="center">
  <b>Fork d'ingénierie de <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Upstream Intégré · Attention Spin(8) $\mathrm{Cl}(8,0)$ Triality · DeepSeek-V4.1-Flash MLA Sans Censure · Chargement Sécurisé GGUF · Mémoire Long Terme Hermes & Hakua · Optimisé pour 32 Go RAM
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Vue d'ensemble de ce Fork (`zapabob/Strata`)

**`zapabob/Strata`** est un fork d'ingénierie avancé synchronisé avec la dernière version amont v0.2.4.2 / moteur 0.1.49.2 de [Strata](https://github.com/Niko1221/Strata). En plus d'exécuter des modèles MoE de 125B paramètres (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) sur un seul PC grâce à un streaming coordonné entre VRAM GPU, RAM système et SSD, ce fork intègre le **Cache KV Spin(8) Triality**, les **dérivés sans censure DeepSeek-V4.1**, le **chargement sécurisé de modèles GGUF basé sur le contenu** et la **mémoire long terme pour agents** :

1. **Bibliothèque de Transformation Orthogonale Spin(8) Triality & $\mathrm{Cl}(8,0)$ ([`spin8/`](spin8/README.md))**
   - Basée sur l'algèbre des octonions réels ($1, e_1, \dots, e_7$) et les générateurs symétriques de Clifford $\mathrm{Cl}(8,0)$.
   - Décompose les spineurs 16×16 selon la chiralité en trois représentations à 8 dimensions : **Vecteur ($V$)**, **Demi-spin Positif ($S_+$)** et **Demi-spin Négatif ($S_-$)**.
   - Audit mathématique rigoureux de chaque plan de rotation avant admission ($E_F \le 10^{-12}$).
   - Transformations de Sylvester-Hadamard et moniteur d'invariants en temps réel (`spin8_monitor`).

2. **Cache KV Triality à Trois Vues & Dialectes TurboQuant CUDA ([`tqcodec/`](tqcodec/README.md))**
   - **Cache CUDA Trois Vues (`cache_cuda.cu`)** : Matrices de clés tournées ($V, S_+, S_-$), valeurs quantifiées partagées, softmax en ligne et correction résiduelle **QJL**.
   - **Dialectes asynchrones** : `TQ4_1S` (4,25 bpw), `TQ3_0S` (3,3125 bpw) et `PQ2_0` (2,50 bpw).
   - **Optimisation SM120 (Série RTX 50)** : Mémoire partagée dynamique éliminant 3,375 Gio de réservation de pile VRAM CUDA.

3. **Dérivés Sans Censure DeepSeek-V4.1-Flash-1017 & Backend MLA ([`strata_control/backends/dsv41.py`](strata_control/backends/dsv41.py))**
   - Support natif des projections Multi-Head Latent Attention (MLA) via le backend dédié `strata-dsv41`.
   - Modèles préqualifiés : Référence ISTA, recette de remplacement ablitérée Kiwimaker Maya-S et modèle autonome AtomicChat.
   - Désactivation automatique du pilotage de refus sur les modèles ablitérés pour éviter toute déformation des réponses.

4. **Résolveur ModelBundle Adressé par le Contenu & Routeur Local ([`strata_control/model_bundle.py`](strata_control/model_bundle.py))**
   - Analyse d'en-tête bornée ($\le 16$ Mio) et protection contre les dépassements de capacité ($\operatorname{rank} \le 4, \operatorname{dim} \le 2^{30}$, atténuant GHSA-vgg9-87g3-85w8).
   - Empreinte SHA-256 en flux continu et détection des altérations.
   - Routage local déterministe (`strata-dsv41`, `strata-native`, `prism`, `llama-cpp`) avec **interdiction stricte de repli sur le cloud** (confidentialité 100% hors-ligne).

5. **Mémoire Long Terme Hermes Agent & Hakua ([`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py))**
   - Serveur MCP stdio standard + CLI :
     - `SOUL.md` : Personnalité de base et directive d'affinité Hakua avec sauvegarde automatique horodatée.
     - `MEMORY.md` : Mémoire épisodique structurée au format `§ [category] YYYY-MM-DD: Title`.
     - Base SQLite Hermes Agent (`~/.hermes/ebbinghaus_memory.db`, ~5 000 souvenirs indexés).
     - Hakua Composite Memory (`~/.hakua-memory`).
   - Injection automatique dans les sessions de discussion via `apps/host/server/memory.mjs`.

6. **Budget Matériel 32 Go RAM / 16 Go VRAM & Cycle de Vie Drafter Zéro VRAM**
   - Validé sous Windows 11 avec 32 Go RAM et RTX 5060 Ti 16 Go (`sm_120`).
   - Respect strict : RAM hôte $\le 24.0$ Gio, réserve système $\ge 4.0$ Gio, budget VRAM $\le 14.0$ Gio.
   - Déchargement automatique du modèle d'ébauche sous pression mémoire sans interrompre le processus principal.

---

## Validation & Intégration Upstream : `v0.3.0` Upstream Integrated Edition

- **SHA Upstream** : `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`
- **Correctif de sécurité GUI** : `c487c875d05075113965bc61d822b27179f70639`
- **Contrats du Fork (F01–F11)** : Intégralement préservés.
- **Suite de tests** : **71/71 tests Python réussis**, **13/13 tests Node.js réussis**.

---

## Licence

Distribué sous la [Licence MIT](LICENSE).
