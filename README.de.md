# Hakua / Strata

Hakua-Chatbot auf Basis von Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · Installationsschritte in 30 Sekunden

Lade den Windows-Installer dieses Forks herunter, führe ihn aus und lade ein kompatibles Modell. Hakua memory in der Seitenleiste öffnet den Gedächtnis-Chat. Die Schritte dauern etwa 30 Sekunden; Download, Installation und Modellstart benötigen zusätzliche Zeit.

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Strata_0.3.3-preview.20261030.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/SHA256SUMS.txt)

Das 7z-Archiv enthält denselben Installer. Entpacke es und starte dann die Setup-EXE.

## Besonderheiten dieses Forks

Hakua liest Erinnerungen und speichert Zusammenfassungen nur nach deiner Zustimmung für die jeweilige Anfrage. Beide Optionen sind unabhängig und werden danach zurückgesetzt. Der Chat benötigt ein aktiviertes `hakua_harness`-Profil und dessen eigenen Schlüssel. Der gewöhnliche Chat-Schlüssel ist getrennt. Siehe [Gedächtnisanleitung](serve/MEMORY_HARNESS.md).

Hermes-Werkzeuge synchronisieren freigegebene SOUL.md / MEMORY.md und bieten Ebbinghaus-Speicher, semantischen Graphen, Obsidian-Export und sleep-Konsolidierung. Sie sind vom Chat getrennt; optionale RAG- und Embedding-Pakete gehören nicht zum Basisinstaller.

Für eine lokale PQ2_0-GGUF wählen Sie in den erweiterten Modelleinstellungen das llama-server-Backend `PrismML`. Für Standard-GGUF mit TurboQuant wählen Sie `TurboQuant` und stellen den K-Cache auf `FP16` und V auf `TURBO2`, `TURBO3` oder `TURBO4`. TurboQuant für K ist in diesem Kandidaten wegen fehlerhafter Antworten im Modelltest gesperrt. Laden Sie das Modell nach einem Backendwechsel erneut. Jedes Backend nutzt eigene mitgelieferte Programme und Bibliotheken; PQ2_0 und TurboQuant sind getrennte Wege. Siehe [Einrichtung und Grenzen](docs/LOCAL_LLAMA_BACKENDS.md).

Experimente mit Spin(8)/Triality, Query-v3 und Bonsai erfordern ausdrücklich gewählte, kompatible Einstellungen. Es gibt keine allgemeine Zusage zu Geschwindigkeit oder Qualität.

Privates Node und Python, Hakua-memory 0.3.5 und eine aus diesem Fork gebaute CUDA-Engine sind enthalten. Beim Modellstart werden keine Python-Pakete installiert und kein Code kompiliert.

## Kompatibilität und Updates

Dieses Windows-Paket ist für NVIDIA RTX 50, CUDA sm_120. Andere GPUs, Linux und macOS benötigen eigene kompatible Pakete. Upstream-Installer enthalten diese Änderungen nicht. Gewichte sind separat und können viele GB benötigen. Bevorzuge passende Pakete von ISTA-DASLab, danach Unsloth und Gyro.

Modelle und persönliche Erinnerungen bleiben außerhalb des Programmordners. Erinnerungen, Schlüssel und Gewichte werden nicht mitgeliefert. Beende die App vor Updates. Für ein Rollback sichere deine Daten und installiere eine frühere Fork-Version.

[Models](docs/MODELS.md) · [Install](docs/INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Versionen und Prüfung

| | |
| --- | --- |
| GUI / Product | `0.3.3-preview.20261030.1` |
| Engine | `0.3.3` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `46c152a1` · 2026-10-28 |

<!-- App version in this preview tree: `0.3.3-preview.20261030.1` -->

Diese Vorschau ist unsigniert. Prüfe SHA256SUMS.txt vor der Installation. Das [Prüfprotokoll](docs/HAKUA_RELEASE.md) nennt tatsächliche Ergebnisse und Grenzen. Ein erfolgreicher Build beweist keine funktionierende Inferenz. Diese unsignierte Vorschau wird manuell über das Installationsprogramm aktualisiert; signierte automatische Updates sind noch nicht geprüft.

## Entwicklung und Hilfe

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

MIT-lizenzierter Strata-Fork. Für Hakua-memory und Modellgewichte gelten eigene Lizenzen. Die Urheberschaft der ursprünglichen Autoren bleibt erhalten.
