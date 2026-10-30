# Hakua / Strata

Chatbot Hakua fondé sur Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · les étapes d’installation en 30 secondes

Téléchargez puis lancez le programme Windows de ce fork, choisissez un modèle compatible et chargez-le. Hakua memory dans la barre latérale ouvre le chat à mémoire. Les manipulations prennent environ 30 secondes ; téléchargement, installation et chargement demandent du temps supplémentaire.

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Strata_0.3.3-preview.20261030.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/SHA256SUMS.txt)

Le fichier 7z contient le même installateur. Extrayez-le, puis lancez le fichier EXE pour installer le logiciel.

## Fonctions propres à ce fork

Hakua ne lit les souvenirs et ne sauvegarde un résumé qu’avec votre accord pour la requête en cours. Les deux choix sont indépendants et réinitialisés ensuite. Au chargement d’un modèle natif compatible, l’application crée automatiquement un profil mémoire local. Ouvrez Hakua memory, copiez la clé du profil dans la boîte de dialogue et cochez une option de mémoire sur la page locale, puis collez la clé dans About → Settings. Le [guide mémoire](serve/MEMORY_HARNESS.md) décrit aussi la configuration d’un serveur lancé depuis les sources.

Les outils Hermes synchronisent SOUL.md / MEMORY.md approuvés et proposent mémoire Ebbinghaus, graphe sémantique, export Obsidian et consolidation sleep. Ils sont distincts du chat ; les dépendances RAG et embeddings optionnelles ne sont pas incluses.

Pour un GGUF local PQ2_0, choisissez le moteur llama-server `PrismML` dans les réglages avancés du modèle. Pour un GGUF standard avec TurboQuant, choisissez `TurboQuant`, puis réglez K sur `FP16` et V sur `TURBO2`, `TURBO3` ou `TURBO4`. Les formats TurboQuant pour K sont désactivés dans cette version après des réponses corrompues lors des essais réels. Rechargez le modèle après un changement de moteur. Chaque moteur utilise ses propres exécutables et bibliothèques inclus ; PQ2_0 et TurboQuant suivent des chemins distincts. Consultez [la configuration et les limites](docs/LOCAL_LLAMA_BACKENDS.md).

Les expériences Spin(8)/Triality, Query-v3 et Bonsai nécessitent des réglages compatibles et explicites, sans promesse générale de vitesse ou de qualité.

Node et Python privés, Hakua-memory 0.3.5 et moteur CUDA construit depuis ce fork sont fournis. Le démarrage d’un modèle n’installe aucun paquet Python et ne compile aucun code.

## Compatibilité et mises à jour

Ce paquet Windows vise les NVIDIA RTX série 50, CUDA sm_120. Les autres GPU, Linux et macOS exigent des paquets distincts. Les programmes amont n’incluent pas ces modifications. Les poids sont séparés et peuvent occuper des dizaines ou centaines de Go. Préférez un paquet compatible ISTA-DASLab, puis Unsloth, puis Gyro.

Conservez modèles et souvenirs hors du dossier de l’application. Aucun souvenir personnel, clé ou poids n’est distribué. Fermez l’application avant la mise à jour. Pour revenir en arrière, gardez une sauvegarde et installez une version antérieure de ce fork.

[Models](docs/MODELS.md) · [Install](docs/INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Versions et vérification

| | |
| --- | --- |
| GUI / Product | `0.3.3-preview.20261030.1` |
| Engine | `0.3.3` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `870aedd9` · 0.2.8 |

<!-- App version in this preview tree: `0.3.3-preview.20261030.1` -->

Cette préversion n’est pas signée. Vérifiez SHA256SUMS.txt avant l’installation. Le [rapport de qualification](docs/HAKUA_RELEASE.md) indique les résultats réels et limites. Une compilation réussie ne prouve pas l’inférence. Cette préversion non signée se met à jour manuellement avec le programme d’installation ; les mises à jour automatiques signées ne sont pas encore vérifiées.

## Développement et assistance

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Fork de Strata sous licence MIT. Hakua-memory et les poids ont leurs propres licences. Les auteurs d’origine restent crédités.

Le vecteur de contrôle amont facultatif de 480 Ko reste désactivé par défaut, sous [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE). Les poids complets du modèle sont à télécharger séparément.
