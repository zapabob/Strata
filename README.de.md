# Hakua / Strata

Hakua-Chatbot auf Strata. Dieser Fork liefert eine Windows-Vorschau mit Hakua memory und getrennten GPU-Laufzeiten. [zapabob/Strata](https://github.com/zapabob/Strata) · Upstream [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Installation (Windows-Vorschau)

1. Lade die [Setup-EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) herunter (oder das [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) mit derselben EXE).
2. Vergleiche sie vor dem Start mit [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt). Es gibt keine Windows-Codesignatur. Die Digests dieses Tags wurden am 2026-11-02 aktualisiert; nutze nicht eine alte SUMS-Datei.
3. Beende Strata vollständig (Infobereich → Strata beenden), falls bereits installiert, und starte die EXE.
4. Installiere beim ersten Start die angebotene signierte Engine oder importiere die passende `.tar.gz` derselben Release. Wähle dann einen Modellordner und lade ein Modell.

Die Klickfolge ist kurz. Downloads, Engine-Aktivierung und Modellladen dauern länger und brauchen Speicherplatz sowie VRAM. Details: [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md). Gemessene Grenzen: [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Was der Installer enthält

| Im App-Installer | Separat |
| --- | --- |
| GUI / Host, privates Node 24.22.2, Control / CPython 3.12.15, Hakua-memory 0.3.5, Harness | Signierte CUDA-Engine (~1,4 GB): natives Strata + PrismML + TurboQuant |
| Manuelle App-Updates über diese EXE | Modellgewichte (zehn bis hundert GB) |

Für die veröffentlichte App brauchst du kein systemweites Node, Python, pip oder einen Compiler. Upstream-Installer von Niko1221 enthalten diese Fork-Änderungen nicht.

## Lokales Modell laden

- **Native Strata-Pakete** (unterstützte Qwen-Textpakete): nativen Prepare-/Load-Pfad der App nutzen.
- **Hikari / PQ2_0-GGUF**: **Load with Strata** (PrismML) nutzen. Kein natives Prepare für PQ2_0.
- **Gewöhnliche GGUF + TurboQuant-Cache**: Backend `TurboQuant`, K=`FP16`, V=`TURBO2` / `TURBO3` / `TURBO4`, dann neu laden. TurboQuant-K bleibt wegen korrupter Antworten aus.

PrismML und TurboQuant sind eigene Programme in der Engine-Komponente. Details: [LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md). Passende Pakete: ISTA-DASLab → Unsloth → Gyro.

Läuft ein Modell über den Strata-/Supervisor-Pfad, kann Agent diese lokale Instanz für unterstützte Werkzeuge nutzen (z. B. Websuche). Rein native Sitzungen nutzen denselben Pfad nicht.

## Hakua memory

Nach dem Laden eines unterstützten Modells **Hakua memory** in der Seitenleiste öffnen. Lesen und Speichern sind getrennt und werden pro Anfrage zurückgesetzt.

- Nativ: Schlüssel aus dem Dialog unter About → Settings einfügen und auf der Gedächtnisseite markieren.
- PrismML / TurboQuant: die App liefert den lokalen Schlüssel; vor dem ersten Öffnen laufende Anfragen beenden.

Anleitung: [MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md). Hermes-SOUL/MEMORY-Werkzeuge sind vom Chat getrennt und für die Grundnutzung nicht nötig.

## Versionen

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine / Control | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream-Freeze | `c62d5e3a` · 0.2.9 |

Release: [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1). Engine und Feed sind Ed25519-signiert und werden von der App geprüft. Automatische signierte App-Updates sind nicht qualifiziert; aktualisiere mit diesem Installer.

## Grenzen (gemessene Vorschau)

Windows x64, NVIDIA RTX 50 / CUDA sm_120, geprüft auf RTX 5060 Ti. Nativer Text ist enthalten. Native Bildeingabe und die separate native DeepSeek-Engine fehlen. Andere GPUs und Betriebssysteme brauchen eigene Pakete. Modelle und persönliche Erinnerungen außerhalb des Programmordners belassen. Keine persönlichen Erinnerungen, Schlüssel oder vollständigen Gewichte in der Release.

Spin(8) / Triality / Query-v3 / Bonsai bleiben optionale Experimente. Keine allgemeine Geschwindigkeits- oder Qualitätszusage.

## Entwicklung

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Models](docs/MODELS.md) · [Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

MIT-Strata-Fork. Hakua-memory und Modellgewichte haben eigene Lizenzen. Credits bleiben bei Autoren und Upstream. Der optionale ~480-KB-Kontrollvektor bleibt standardmäßig aus unter [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
