# Hakua / Strata

Hakua-Chatbot auf Basis von Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · Installationsschritte in 30 Sekunden

Lade den Windows-Installer dieses Forks herunter und führe ihn aus. Installiere beim ersten Start die angebotene kompatible Engine, wähle dann ein Modell und lade es. Hakua memory in der Seitenleiste öffnet den Gedächtnis-Chat. Die Schritte dauern etwa 30 Sekunden; Downloads, Installation und Laden dauern länger.

Windows-Vorschau 0.4.0: Gemessene Prüfungen und unterstützte Grenzen stehen im [Prüfbericht](docs/HAKUA_RELEASE.md).

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt)

Das 7z-Archiv enthält denselben Installer. Entpacke es und starte dann die Setup-EXE.

## Besonderheiten dieses Forks

Hakua liest Erinnerungen und speichert Zusammenfassungen nur nach deiner Zustimmung für die jeweilige Anfrage. Beide Optionen sind unabhängig und werden danach zurückgesetzt. Beim Laden eines unterstützten nativen Modells legt die Desktop-App automatisch ein lokales Gedächtnisprofil an. Öffne Hakua memory, kopiere den Profilschlüssel aus dem Dialog und wähle auf der lokalen Gedächtnisseite eine Gedächtnisoption aus und füge ihn dann unter About → Settings ein. Die [Gedächtnisanleitung](serve/MEMORY_HARNESS.md) beschreibt auch die Konfiguration eines Servers aus dem Quellcode.

Auch PrismML/PQ2_0 und TurboQuant nutzen Hakua-memory: Modell laden und Hakua memory in der Seitenleiste öffnen. Der neue Dialog verwendet den lokalen persönlichen Schlüssel automatisch; Lesen und Speichern werden für jede Anfrage getrennt gewählt. Vor dem ersten Öffnen laufende Anfragen abschließen: Der von der App verwaltete Server startet mit Authentifizierung und ohne gemeinsame Caches neu. Alle drei Wege teilen dasselbe lokale Gedächtnisprofil. Beim Start werden GUI-, Host- und Desktop-Version geprüft; gemischte oder nicht ladbare Dateien führen zu Wiederherstellungshinweisen.

Hermes-Werkzeuge synchronisieren freigegebene SOUL.md / MEMORY.md und bieten Ebbinghaus-Speicher, semantischen Graphen, Obsidian-Export und sleep-Konsolidierung. Sie sind vom Chat getrennt; optionale RAG- und Embedding-Pakete gehören nicht zum Basisinstaller.

Für eine lokale PQ2_0-GGUF wählen Sie in den erweiterten Modelleinstellungen das llama-server-Backend `PrismML`. Für Standard-GGUF mit TurboQuant wählen Sie `TurboQuant` und stellen den K-Cache auf `FP16` und V auf `TURBO2`, `TURBO3` oder `TURBO4`. TurboQuant für K ist in diesem Kandidaten wegen fehlerhafter Antworten im Modelltest gesperrt. Laden Sie das Modell nach einem Backendwechsel erneut. Jedes Backend nutzt eigene mitgelieferte Programme und Bibliotheken; PQ2_0 und TurboQuant sind getrennte Wege. Siehe [Einrichtung und Grenzen](docs/LOCAL_LLAMA_BACKENDS.md).

Experimente mit Spin(8)/Triality, Query-v3 und Bonsai erfordern ausdrücklich gewählte, kompatible Einstellungen. Es gibt keine allgemeine Zusage zu Geschwindigkeit oder Qualität.

Wie die offizielle App enthält der Installer privates Node und Python sowie Hakua-memory 0.3.5. GPU-Engines werden separat verteilt: Nach deiner Auswahl lädt die App eine signierte Hakua-Engine-Komponente herunter oder importiert eine bereits heruntergeladene Datei. Diese Komponente enthält native CUDA-, PrismML- und TurboQuant-Laufzeiten. Modellgewichte werden separat geladen. Für die veröffentlichte App brauchst du weder systemweit installiertes Node oder Python noch pip oder einen Compiler.

## Kompatibilität und Updates

Dieses Windows-Paket ist für NVIDIA RTX 50, CUDA sm_120. Andere GPUs, Linux und macOS benötigen eigene kompatible Pakete. Upstream-Installer enthalten diese Änderungen nicht. Gewichte sind separat und können viele GB benötigen. Bevorzuge passende Pakete von ISTA-DASLab, danach Unsloth und Gyro.

Die separat verteilte native Engine dient dem Textchat. Native Bildeingabe und die separate native DeepSeek-Engine sind in dieser Vorschau nicht enthalten.

Modelle und persönliche Erinnerungen bleiben außerhalb des Programmordners. Erinnerungen, Schlüssel und Gewichte werden nicht mitgeliefert. Beende die App vor Updates. Für ein Rollback sichere deine Daten und installiere eine frühere Fork-Version.

Bei aktivierter Ablage im Infobereich blendet × das Fenster aus. Klicke vor einem Update mit der rechten Maustaste auf das Strata-Symbol im Infobereich und wähle Strata beenden, um die App vollständig zu schließen.

[Models](docs/MODELS.md) · [Install](docs/HAKUA_INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Versionen und Prüfung

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `c62d5e3a` · 0.2.9 |

<!-- App version in this preview tree: `0.4.0-preview.20261101.1` -->

Der Windows-Installer hat keine Windows-Codesignatur. Prüfe SHA256SUMS.txt vor der Installation. Die separate Engine-Komponente und ihr Update-Feed sind signiert und werden von der App geprüft. App-Updates erfolgen manuell mit dem Installer; signierte automatische App-Updates sind noch nicht qualifiziert. Das [Prüfprotokoll](docs/HAKUA_RELEASE.md) nennt Ergebnisse und Grenzen einschließlich der Gedächtnistests mit realen Modellen.

## Entwicklung und Hilfe

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

MIT-lizenzierter Strata-Fork. Für Hakua-memory und Modellgewichte gelten eigene Lizenzen. Die Urheberschaft der ursprünglichen Autoren bleibt erhalten.

Der optionale Kontrollvektor aus dem Upstream (480 KB) bleibt standardmäßig aus. Es gilt die [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE). Die vollständigen Modellgewichte werden separat heruntergeladen.
