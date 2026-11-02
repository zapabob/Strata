# Hakua / Strata

Chatbot Hakua sur Strata. Cette fourche propose une préversion Windows avec Hakua memory et des runtimes GPU séparés. [zapabob/Strata](https://github.com/zapabob/Strata) · amont [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Installation (préversion Windows)

1. Téléchargez l’[EXE d’installation](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) (ou le [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) qui contient le même EXE).
2. Vérifiez-le avec [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt) avant de l’exécuter. Pas de signature de code Windows. Les empreintes de cette balise ont été mises à jour le 2026-11-02 ; n’utilisez pas un ancien SUMS.
3. Quittez Strata complètement (plateau → Quitter Strata) s’il est déjà installé, puis lancez l’EXE.
4. Au premier démarrage, installez le moteur signé proposé, ou importez le `.tar.gz` correspondant de la même release. Choisissez ensuite un dossier de modèles et chargez un modèle.

Le parcours de clics est court. Téléchargements, activation du moteur et chargement du modèle prennent plus longtemps et demandent de l’espace disque et de la VRAM. Détails : [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md). Limites mesurées : [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Contenu de l’installateur

| Dans l’installateur de l’app | Séparé |
| --- | --- |
| GUI / Host, Node privé 24.22.2, Control / CPython 3.12.15, Hakua-memory 0.3.5, Harness | Composant CUDA signé (~1,4 Go) : Strata natif + PrismML + TurboQuant |
| Mises à jour manuelles via cet EXE | Poids de modèles (dizaines ou centaines de Go) |

Pas besoin de Node, Python, pip ou compilateur système pour l’app publiée. L’installateur amont Niko1221 n’inclut pas les changements de cette fourche.

## Charger un modèle local

- **Paquets Strata natifs** (paquets texte Qwen pris en charge) : chemin prepare / load natif de l’app.
- **Hikari / PQ2_0 GGUF** : utilisez **Load with Strata** (PrismML). Pas de prepare natif pour PQ2_0.
- **GGUF ordinaire + cache TurboQuant** : backend `TurboQuant`, K=`FP16`, V=`TURBO2` / `TURBO3` / `TURBO4`, puis recharger. Les modes K TurboQuant restent désactivés après des réponses corrompues en test réel.

PrismML et TurboQuant sont des exécutables distincts dans le composant moteur. Détails : [LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md). Préférez des paquets adaptés : ISTA-DASLab → Unsloth → Gyro.

Quand un modèle tourne via le chemin Strata / superviseur, Agent peut utiliser cette instance locale pour les outils supportés (par ex. recherche web). Une session uniquement native n’expose pas le même chemin.

## Hakua memory

Après le chargement d’un modèle pris en charge, ouvrez **Hakua memory** dans la barre latérale. Consentements lecture et enregistrement séparés, réinitialisés à chaque tour.

- Natif : collez la clé du dialogue dans About → Settings, puis cochez la mémoire sur la page locale.
- PrismML / TurboQuant : l’app fournit la clé locale ; terminez les requêtes actives avant la première ouverture.

Guide : [MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md). Les outils Hermes SOUL/MEMORY sont distincts du chat et non requis pour un usage de base.

## Versions

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine / Control | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Gel amont | `c62d5e3a` · 0.2.9 |

Page de release : [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1). Le moteur et le flux sont signés Ed25519 et vérifiés par l’app. Les mises à jour automatiques signées de l’app ne sont pas qualifiées ; utilisez cet installateur.

## Limites (préversion mesurée)

Windows x64, NVIDIA RTX 50 / CUDA sm_120, vérifié sur RTX 5060 Ti. Texte natif inclus. Pas d’entrée image native ni de moteur DeepSeek natif séparé. Autres GPU et OS : paquets dédiés. Gardez modèles et mémoires personnelles hors du dossier de l’app. Aucune mémoire personnelle, clé ou pack de poids complet dans la release.

Spin(8) / Triality / Query-v3 / Bonsai restent des expériences optionnelles. Aucune promesse générale de vitesse ou de qualité.

## Développement

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Models](docs/MODELS.md) · [Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Fourche Strata sous MIT. Hakua-memory et poids de modèles ont leurs licences. Crédits aux auteurs et à l’amont. Le vecteur de contrôle optionnel (~480 Ko) reste désactivé par défaut sous [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
