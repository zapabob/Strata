# Strata · Hakua

Modèles locaux, discussion, outils et mémoire Hakua facultative. Il s’agit du [fork zapabob](https://github.com/zapabob/Strata) de [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Préversion Windows

**0.4.1-beta.1** se met à jour manuellement et ne possède pas de signature de code Windows. [Version](https://github.com/zapabob/Strata/releases/tag/v0.4.1-beta.1) · [Installation](docs/HAKUA_INSTALL.md) · [Vérifications et limites](docs/HAKUA_RELEASE.md).

1. Téléchargez [l’installateur](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/Strata_0.4.1-beta.1_x64-setup.exe) et comparez son empreinte à [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/SHA256SUMS.txt).
2. Quittez Strata, y compris son icône de notification, puis lancez l’installation. Conservez modèles et données personnelles hors du dossier de l’application.
3. Téléchargez `strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz` depuis cette version bêta et importez-le dans l’écran de préparation. Le flux latest conserve le moteur précédent.
4. Choisissez un modèle adapté ou **Use a local GGUF** pour vos fichiers existants. Node et Python sont inclus ; aucun interpréteur système ni compilateur n’est nécessaire.

Les versions suivent [SemVer 2.0.0](https://semver.org/) : application `0.4.1-beta.1`, moteur natif/Control `0.4.1` ; les environnements PrismML/TurboQuant inchangés restent en `0.4.0`. Le dossier habituel de l’application est `%LOCALAPPDATA%\Programs\Strata` sur C:, indépendamment des modèles. Une installation existante peut conserver un autre emplacement.

## Réutiliser les modèles présents

Pour un GGUF fractionné, sélectionnez une partie : Strata vérifie l’ensemble. Les poids importés restent à leur emplacement. Un nom générique tel que `Hf` est remplacé à l’affichage par le nom du fichier. Vos noms personnalisés sont conservés après vérification et redémarrage.

Avant de préparer un modèle du catalogue, Strata recherche un ensemble local compatible dans le dossier choisi et ses sous-dossiers, avec une exploration limitée. Un résultat valide unique est réutilisé ; plusieurs résultats imposent une sélection explicite. Les téléchargements habituels conservent leurs contrôles d’intégrité et leur reprise. Le moteur et les couches de brouillon facultatives sont traités séparément.

Les modèles Qwen/Swift natifs peuvent nécessiter une conversion initiale en pack. La progression affiche les couches terminées lorsque le convertisseur les fournit. La reprise d’un pack à faible consommation mémoire tient compte de l’espace déjà alloué au fichier temporaire. Les GGUF Hikari/PQ2_0 compatibles utilisent PrismML via **Load with Strata**, sans conversion native Q2_0. Pour les GGUF ordinaires compatibles, TurboQuant propose K=`FP16` et V=`TURBO2/3/4`, puis un rechargement. Voir les [moteurs locaux](docs/LOCAL_LLAMA_BACKENDS.md).

## Cache privé et mémoire

Le nouveau mode Qwen3.6 conserve le cache dans une même conversation authentifiée. Une autre conversation ou un autre utilisateur ne le réutilise pas. Changement de conversation, annulation, erreur ou cinq minutes d’inactivité effacent le cache privé. Sans identifiant de conversation, aucune réutilisation n’est effectuée.

Ce mode exige le fichier moteur validé correspondant et sa confirmation au démarrage. Les anciens moteurs restent refusés. Une seule requête est traitée à la fois ; les caches partagés restent désactivés. Le mapped expert pack reste facultatif. Consultez les mesures et vérifications encore ouvertes dans le [compte rendu de version](docs/HAKUA_RELEASE.md).

Ouvrez **Hakua memory** dans la barre latérale. La lecture et la sauvegarde demandent des choix distincts à chaque tour. PrismML/TurboQuant redémarre son serveur avec authentification et caches privés ; terminez les requêtes en cours auparavant. [Guide](serve/MEMORY_HARNESS.md).

## Composants et limites

Application/Host : `0.4.1-beta.1` ; moteur natif/Control : `0.4.0` ; Node : `24.22.2` ; CPython : `3.12.15` ; Hakua-memory : `0.3.5`. Référence amont : `ffa80d73` / `0.2.10`.

Le composant CUDA/PrismML/TurboQuant signé reste celui de [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1). Le composant expérimental Qwen3.6 séparé n’est pas signé. L’installateur n’inclut pas le moteur CUDA. Les mises à jour automatiques signées de l’application ne sont pas qualifiées.

Les vérifications Windows x64 portent sur une RTX 5060 Ti, CUDA sm_120 et 32 Go de RAM. Les autres GPU et systèmes, les images natives et un moteur natif DeepSeek distinct ne sont pas qualifiés. L’ancienne allocation hôte Qwen3.6 peut demander environ 18,7 Gio plus une réserve ; 32 Go ne garantissent pas le démarrage. Une réponse courte avec un contexte de 131 072 tokens ne valide ni la pleine fenêtre ni sa qualité. Les modes K de TurboQuant restent désactivés après des échecs aux essais de qualité. Spin(8), Triality, Query-v3 et Bonsai restent expérimentaux et facultatifs. Performances et besoins dépendent du modèle et de l’ordinateur.

## Développement

[Modèles](docs/AI_REFERENCE.md) · [Compilation](packaging/README.md) · [Contribution](CONTRIBUTING.md) · [Sécurité](SECURITY.md)

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

Strata est sous licence MIT. Les poids, Hakua-memory et les dépendances conservent leurs licences et notices. Le petit vecteur de contrôle facultatif est désactivé par défaut et relève de la [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
