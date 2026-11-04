# Hakua / Strata

Chatbot Hakua sur Strata. Cette fourche propose une préversion Windows avec Hakua memory et des runtimes GPU séparés. [zapabob/Strata](https://github.com/zapabob/Strata) · amont [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Installation (préversion Windows)

1. Téléchargez l’[EXE d’installation](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.6/Strata_0.4.0-preview.20261103.6_x64-setup.exe).
2. Vérifiez-le avec [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.6/SHA256SUMS.txt) avant de l’exécuter. Pas de signature de code Windows. SHA-256 de l’EXE : `784d4f992443a43076e7de8dbcdc624b35d95e97e13b716ea9de0e13a1baeac9` (114 984 071 octets).
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
| GUI / Product | `0.4.0-preview.20261103.6` |
| Engine / Control | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Gel amont | `ffa80d73` · 0.2.10 |

Page de release : [v0.4.0-preview.20261103.6](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.6). L’installateur et le paquet moteur Qwen3.6 de cette balise ne sont pas signés. Le flux Ed25519 et le moteur signé de `v0.4.0-preview.20261101.1` restent en place. Les mises à jour automatiques signées de l’app ne sont pas qualifiées ; utilisez cet installateur. L’installateur ne contient pas le moteur CUDA. Le paquet Qwen3.6 n’a pas de lecteur d’image et `signature` est null. PrismML et TurboQuant restent dans le composant signé. Ligne principale : Qwen3.6-35B-A3B UD-Q4_K_XL, contexte 65536, KV FP32, MTP 2, prefill auto. Les nouveaux chemins sont opt-in. Un réglage non appliqué, ou un cache privé, est refusé avant le démarrage. Le mapped expert pack ne part que sur demande et si le SHA-256 du moteur est `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`, `6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29`, `dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5` ou `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046`. L’ancien condensé reste admis. L’arène hôte d’origine reste le défaut. Le temps de démarrage et la vitesse des jetons ne sont pas mesurés. Le garde-fou CUDA spill n’a pas passé la baseline revue. Sur un PC de 32 Go, UD-Q4_K_XL peut être refusé avant le lancement si la RAM physique libre ne couvre pas l’arène legacy de 18,75 Gio plus la réserve. Ce n’est pas une mesure de tenue dans 16 Go de VRAM.

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
