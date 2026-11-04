# Hakua / Strata

Hakua-Chatbot auf Strata. Dieser Fork liefert eine Windows-Vorschau mit Hakua memory und getrennten GPU-Laufzeiten. [zapabob/Strata](https://github.com/zapabob/Strata) · Upstream [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Installation (Windows-Vorschau)

1. Lade die [Setup-EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.6/Strata_0.4.0-preview.20261103.6_x64-setup.exe) herunter.
2. Vergleiche sie vor dem Start mit [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.6/SHA256SUMS.txt). Es gibt keine Windows-Codesignatur. SHA-256 der Setup-EXE: `784d4f992443a43076e7de8dbcdc624b35d95e97e13b716ea9de0e13a1baeac9` (113.075.186 Bytes).
3. Beende Strata vollständig (Infobereich → Strata beenden), falls bereits installiert, und starte die EXE.
4. Der Installer aktualisiert die App. Er enthält keine CUDA-Engine. Die Qwen3.6-Engine dieses Tags ist separat, ohne Picture-Reader und nicht Ed25519-signiert (`signature` ist null). Die signierte Engine von [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1) hält weiter PrismML und TurboQuant (Digest `b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1`, unberührt). Dieses Release ersetzt diese Dateien nicht.

Die Klickfolge ist kurz. Downloads, Engine-Aktivierung und Modellladen dauern länger und brauchen Speicherplatz sowie VRAM. Details: [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md). Gemessene Grenzen: [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Was der Installer enthält

| Im App-Installer | Separat |
| --- | --- |
| GUI / Host, privates Node 24.22.2, Control / CPython 3.12.15, Hakua-memory 0.3.5, Harness | CUDA-Engines getrennt. Qwen3.6-Paket dieses Tags unsigniert. PrismML/TurboQuant bleiben in der signierten Komponente von `v0.4.0-preview.20261101.1` (`b5e4d525…`) |
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
| GUI / Product | `0.4.0-preview.20261103.6` |
| Engine / Control | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream-Freeze | `ffa80d73` · 0.2.10 |

Release: [v0.4.0-preview.20261103.6](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.6). Installer und Qwen3.6-Engine-Paket dieses Tags sind nicht signiert. Der Ed25519-Feed und die signierte Engine von `v0.4.0-preview.20261101.1` bleiben. Automatische signierte App-Updates sind nicht qualifiziert; aktualisiere mit diesem Installer. Der Installer enthält keine CUDA-Engine. Das Qwen3.6-Paket hat keinen Picture-Reader und `signature` ist null. PrismML und TurboQuant bleiben in der signierten Komponente. Hauptlinie: Qwen3.6-35B-A3B UD-Q4_K_XL, Context 65536, FP32-KV, MTP 2, Prefill auto. Neue Wege sind opt-in. Nicht angewendete Einstellungen und Private-Cache-Anfragen werden vor dem Start abgelehnt. Mapped expert pack nur bei Anfrage und Engine-SHA-256 `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`, `6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29`, `dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5` oder `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046`. Der ältere Digest bleibt erlaubt. Standard bleibt die alte Host-Arena. T04-Adoption ist NOT_DECIDED. Gepaarte Speed-Checks T06/T07/T08 wurden nicht ausgeführt. Startzeit und Token-Geschwindigkeit sind nicht gemessen. Der CUDA-Spill-Guard ist gegen die geprüfte Baseline nicht bestanden. Auf einem 32-GB-PC kann UD-Q4_K_XL vor dem Start abgelehnt werden, wenn der freie physische RAM die legacy 18,75-GiB-Arena plus Reserve nicht hält. Das ist keine Messung, dass das Modell in 16 GB VRAM passt.

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
