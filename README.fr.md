# Strata · Hakua

**Code candidat :** upstream `v0.2.12` / `146df3c4` est intégré ; compilation native et essais matériels restent à faire.
L’installeur personnel testé avant cette intégration est `Strata-0.5.2-local.2-windows-x64-setup.exe`.
Les liens ci-dessous restent ceux de 0.5.1. [État de l’intégration](docs/UPSTREAM_0212.md).

La version 0.5.1 charge les modèles sur demande et corrige le démarrage de Qwen3.6 natif. Les modèles existants et les paquets d’experts vérifiés sont conservés.

Modèles locaux, discussion, outils et mémoire Hakua facultative. Il s’agit du [fork zapabob](https://github.com/zapabob/Strata) de [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Version Windows

Qwen3.6 natif a atteint READY en 41,250 secondes avec une capacité de 4096 cellules et a réussi six tests courts du cache privé. Les entrées complètes de 98K/131K et la qualité du modèle en FP16/NVFP4 ne sont pas validées. Consultez les [résultats et limites](docs/HAKUA_RELEASE.md).

Cette version vise Windows x64 CUDA sm_120. Les vérifications locales ont utilisé une RTX 5060 Ti avec 16 Go de VRAM et 32 Go de RAM. Consultez les [résultats et limites restantes](docs/HAKUA_RELEASE.md) avant l’installation.

**0.5.1** se met à jour manuellement et ne possède pas de signature de code Windows. [Version](https://github.com/zapabob/Strata/releases/tag/v0.5.1) · [Installation](docs/HAKUA_INSTALL.md) · [Vérifications et limites](docs/HAKUA_RELEASE.md).

1. Téléchargez [l’installateur](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64-setup.exe) et comparez son empreinte à [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.1/SHA256SUMS.txt).
2. Quittez Strata, y compris son icône de notification, puis lancez l’installation. Conservez modèles et données personnelles hors du dossier de l’application.
3. Installez le composant CUDA signé depuis l’écran de préparation, via le flux latest ou le fichier inclus `strata-engine-0.5.1-windows-x86_64-cuda-cuda13.tar.gz`.
4. Choisissez un modèle adapté ou **Use a local GGUF** pour vos fichiers existants. Node et Python sont inclus ; aucun interpréteur système ni compilateur n’est nécessaire.

Les versions suivent [SemVer 2.0.0](https://semver.org/) : application `0.5.1`, moteur natif `0.5.1`; Control `0.5.1` ; les environnements PrismML/TurboQuant inchangés restent en `0.4.0`. Le dossier habituel de l’application est `%LOCALAPPDATA%\Programs\Strata` sur C:, indépendamment des modèles. Une installation existante peut conserver un autre emplacement.

L’[archive tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64.tar.7z) contient le même installateur NSIS, le composant CUDA signé, Control, les sommes de contrôle et les instructions. Les modèles et données personnelles sont exclus. Publication avec `v0.5.1`, l’alias de tag `latest` et GitHub Latest.

## Réutiliser les modèles présents

Pour un GGUF fractionné, sélectionnez une partie : Strata vérifie l’ensemble. Les poids importés restent à leur emplacement. Un nom générique tel que `Hf` est remplacé à l’affichage par le nom du fichier. Vos noms personnalisés sont conservés après vérification et redémarrage.

Les réglages d’un modèle local enregistré restent accessibles pendant le chargement des autres listes de modèles.

Avant de préparer un modèle du catalogue, Strata recherche un ensemble local compatible dans le dossier choisi et ses sous-dossiers, avec une exploration limitée. Un résultat valide unique est réutilisé ; plusieurs résultats imposent une sélection explicite. Les téléchargements habituels conservent leurs contrôles d’intégrité et leur reprise. Le moteur et les couches de brouillon facultatives sont traités séparément.

Les modèles Qwen/Swift natifs peuvent nécessiter une conversion initiale en pack. La progression affiche les couches terminées lorsque le convertisseur les fournit. La reprise d’un pack à faible consommation mémoire tient compte de l’espace déjà alloué au fichier temporaire. Les GGUF Hikari/PQ2_0 compatibles utilisent PrismML via **Load with Strata**, sans conversion native Q2_0. Pour les GGUF ordinaires compatibles, TurboQuant propose K=`FP16` et V=`TURBO2/3/4`, puis un rechargement. Voir les [moteurs locaux](docs/LOCAL_LLAMA_BACKENDS.md).

## Cache privé et mémoire

Le nouveau mode Qwen3.6 conserve le cache dans une même conversation authentifiée. Une autre conversation ou un autre utilisateur ne le réutilise pas. Changement de conversation, annulation, erreur ou cinq minutes d’inactivité effacent le cache privé. Sans identifiant de conversation, aucune réutilisation n’est effectuée.

Les deux branches de refus avant démarrage du Host ont été supprimées. Le serveur vérifie la capacité de cache privé dans la réponse INFO du moteur actif, y compris pour les compilations locales compatibles. Une seule requête est traitée à la fois ; les caches partagés restent désactivés. Le mapped expert pack reste facultatif. Consultez les mesures et vérifications encore ouvertes dans le [compte rendu de version](docs/HAKUA_RELEASE.md).

Ouvrez **Hakua memory** dans la barre latérale. La lecture et la sauvegarde demandent des choix distincts à chaque tour. PrismML/TurboQuant redémarre son serveur avec authentification et caches privés ; terminez les requêtes en cours auparavant. [Guide](serve/MEMORY_HARNESS.md).

## Composants et limites

Application/Host : `0.5.1` ; moteur natif : `0.5.1`; Control `0.5.1` ; Node : `24.22.2` ; CPython : `3.12.15` ; Hakua-memory : `0.3.5`. Référence amont : `5d37280d` / `0.2.11`.

0.5.1 intègre la version amont 0.2.11 et les corrections jusqu’à `5d37280d` : fichiers par conversation, reprise des réponses actives, corrections IME et du moteur de rendu, nouveaux modèles, isolation des flux et Pillow 13. La mémoire Hakua, la réutilisation des GGUF locaux et les caches privés Qwen3.6 sont conservés. La nouvelle compilation CUDA est vérifiée séparément ; les mesures de 0.4.1 ne qualifient pas ses nouveaux réglages par défaut. La génération native sur toute la fenêtre reste non qualifiée. Voir les [vérifications et la publication](docs/HAKUA_RELEASE.md).

Les vérifications Windows x64 portent sur une RTX 5060 Ti, CUDA sm_120 et 32 Go de RAM. Les autres GPU et systèmes, les images natives et un moteur natif DeepSeek distinct ne sont pas qualifiés. L’ancienne allocation hôte Qwen3.6 peut demander environ 18,7 Gio plus une réserve ; 32 Go ne garantissent pas le démarrage. Une réponse courte avec un contexte de 131 072 tokens ne valide ni la pleine fenêtre ni sa qualité. Les modes K de TurboQuant restent désactivés après des échecs aux essais de qualité. Spin(8), Triality, Query-v3 et Bonsai restent expérimentaux et facultatifs. Performances et besoins dépendent du modèle et de l’ordinateur.

## 96K–128K avec 16 Go de VRAM

L’éditeur propose 96K (98 304) et 128K (131 072). Sur le PC testé, équipé d’une RTX 5060 Ti de 16 Go et de 32 Go de RAM, Qwen3.6 UD-Q4_K_XL avec PrismML, un cache K/V Q8 et 28 couches MoE sur le CPU a traité 130 792 tokens sans troncature et retrouvé les trois codes éloignés. Cette requête a pris environ 29 minutes ; elle ne garantit ni la qualité générale ni la vitesse d’autres modèles. Voir les [réglages et résultats en contexte complet](docs/WINDOWS_16GB_CONTEXT.md).

## Développement

[Modèles](docs/AI_REFERENCE.md) · [Compilation](packaging/README.md) · [Contribution](CONTRIBUTING.md) · [Sécurité](SECURITY.md)

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

Strata est sous licence MIT. Les poids, Hakua-memory et les dépendances conservent leurs licences et notices. Le petit vecteur de contrôle facultatif est désactivé par défaut et relève de la [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).

## Soutiens du projet Strata d’origine

Merci à toutes les personnes qui soutiennent Strata.

<!-- supporters:start (one line per public supporter, newest last; copy a line and change the GitHub name in all four places) -->
<a href="https://github.com/ryan4yin"><img src="https://github.com/ryan4yin.png?size=96" width="48" height="48" alt="ryan4yin" title="ryan4yin"></a>
<a href="https://github.com/themactep"><img src="https://github.com/themactep.png?size=96" width="48" height="48" alt="themactep" title="themactep"></a>
<a href="https://github.com/macintog"><img src="https://github.com/macintog.png?size=96" width="48" height="48" alt="macintog" title="macintog"></a>
<a href="https://github.com/bisonbet"><img src="https://github.com/bisonbet.png?size=96" width="48" height="48" alt="bisonbet" title="bisonbet"></a>
<a href="https://github.com/vizv"><img src="https://github.com/vizv.png?size=96" width="48" height="48" alt="vizv" title="vizv"></a>
<!-- supporters:end -->
