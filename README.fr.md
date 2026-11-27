# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata est la branche de [Niko1221/Strata](https://github.com/Niko1221/Strata) dédiée à Windows. Elle utilise des modèles locaux pour dialoguer, programmer et exécuter des tâches avec un agent. Pour les modèles MoE compatibles, le moteur natif peut répartir les poids des experts entre la mémoire du GPU, la RAM et le SSD.

## Premiers pas

Téléchargez le programme d’installation Windows pour votre compte depuis les [versions de Hakua](https://github.com/zapabob/Strata/releases). Le moteur CUDA est fourni séparément. Dans **Modèles**, choisissez le profil correspondant aux poids installés. Inkling 2 Mini SC117 dispose de profils distincts pour SQ-10, SQ-15 et SQ-20. Adaptez le contexte à la mémoire disponible. Consultez le [guide Windows](docs/HAKUA_INSTALL.md) et la [documentation des modèles](docs/MODELS.md).

## Réutiliser les procédures de l’agent

Dans **Paramètres → Outils**, activez la recherche de compétences à la demande. L’agent peut alors rechercher puis ouvrir les compétences utiles. Dans **Compétences**, les options d’apprentissage à partir du travail terminé et d’application automatique sont indépendantes. Une procédure enregistrée est un fichier `SKILL.md` modifiable. La sélection automatique tient compte du nom, des expressions déclencheuses et de l’espace de travail. Les compétences, les agents auxiliaires, les outils de fichiers et `/goal` disposent de réglages distincts. [Guide des procédures](docs/WORKFLOW_SKILLS.md)

## Mesures et limites

Sur une RTX 5060 Ti de 16 Go, SC117 SQ-10 a produit une scène Pagoda Bench en un fichier HTML via `/goal`, puis a corrigé son moteur de rendu à partir des diagnostics. Après un zoom arrière, Chrome a affiché cinq toits. La scène a signalé 7 079 voxels. Le cadrage initial coupait le sommet et aucun score officiel n’a été mesuré. Les [mesures du moteur 0.8.5](_docs/2026-11-27_v085-release-notes.md) portent sur des entrées courtes à la capacité de contexte indiquée.

La [fiche de version](docs/HAKUA_RELEASE.md) précise la compatibilité, les signatures et les limites des essais. Hakua est distribué sous [licence MIT](LICENSE). Les modèles et composants ont leurs propres conditions.
