# Strata · Hakua

Lokale Modelle, Chat, Werkzeuge und optionale Hakua-Erinnerungen. Dies ist der [zapabob-Fork](https://github.com/zapabob/Strata) von [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Windows-Veröffentlichung

Diese Version ist für Windows x64 CUDA sm_120 bestimmt. Die lokalen Prüfungen liefen auf einer RTX 5060 Ti mit 16 GB VRAM und 32 GB RAM. Lies vor der Installation die [Prüfergebnisse und verbleibenden Grenzen](docs/HAKUA_RELEASE.md).

**0.4.1** ist eine manuell installierte Version ohne Windows-Codesignatur. [Release](https://github.com/zapabob/Strata/releases/tag/v0.4.1) · [Installationsanleitung](docs/HAKUA_INSTALL.md) · [Prüfungen und Grenzen](docs/HAKUA_RELEASE.md).

1. Lade den [Installer](https://github.com/zapabob/Strata/releases/download/v0.4.1/Strata-0.4.1-windows-x64-setup.exe) herunter und vergleiche seine Prüfsumme mit [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.1/SHA256SUMS.txt).
2. Beende Strata einschließlich des Symbols im Infobereich und starte den Installer. Modelle und persönliche Daten gehören außerhalb des Programmordners.
3. Installiere die signierte CUDA-Komponente im Vorbereitungsbildschirm über den latest-Feed oder die enthaltene Datei `strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz`.
4. Wähle ein passendes Modell oder **Use a local GGUF** für vorhandene Dateien. Node und Python sind enthalten; ein Systeminterpreter oder Compiler ist nicht nötig.

Die Versionen folgen [SemVer 2.0.0](https://semver.org/): App `0.4.1`, native Engine `0.4.1`; Control `0.4.2`; unveränderte PrismML-/TurboQuant-Laufzeiten bleiben `0.4.0`. Der übliche Programmordner ist `%LOCALAPPDATA%\Programs\Strata` auf C:, unabhängig vom Modellordner. Eine bestehende Installation kann einen anderen Speicherort behalten.

Das [tar.7z-Paket](https://github.com/zapabob/Strata/releases/download/v0.4.1/Strata-0.4.1-windows-x64.tar.7z) enthält denselben NSIS-Installer, die signierte CUDA-Komponente, Control, Prüfsummen und eine Installationsanleitung. Modelle und persönliche Daten sind nicht enthalten. Veröffentlicht wird mit `v0.4.1`, dem Tag-Alias `latest` und GitHub Latest.

## Vorhandene Modelle verwenden

Bei einem geteilten GGUF genügt die Auswahl eines Teils; Strata prüft den vollständigen Satz. Importierte Gewichte bleiben an ihrem Speicherort. Generische Metadaten wie `Hf` werden durch den Dateinamen ersetzt. Selbst vergebene Namen bleiben bei erneuter Prüfung und nach einem Neustart erhalten.

Die Einstellungen eines registrierten lokalen Modells lassen sich öffnen, während andere Modelllisten noch geladen werden.

Vor der Vorbereitung eines Katalogmodells sucht Strata begrenzt im ausgewählten Modellordner und dessen Unterordnern nach einem passenden lokalen Satz. Ein eindeutiger gültiger Treffer wird wiederverwendet. Mehrere Treffer erfordern eine Dateiauswahl. Reguläre Downloads behalten ihre Integritätsprüfung und Wiederaufnahme. Engine und optionale Entwurfsschichten werden getrennt behandelt.

Native Qwen-/Swift-Modelle können eine einmalige Pack-Konvertierung benötigen. Der Fortschritt zeigt fertige Schichten, sofern der Packer sie meldet. Beim Fortsetzen eines speichersparenden Packs wird der bereits zugewiesene Platz seiner temporären Datei berücksichtigt. Unterstützte Hikari-/PQ2_0-Dateien verwenden PrismML über **Load with Strata**, ohne native Q2_0-Konvertierung. Für unterstützte gewöhnliche GGUFs bietet TurboQuant K=`FP16` und V=`TURBO2/3/4`; danach neu laden. Siehe [lokale Backends](docs/LOCAL_LLAMA_BACKENDS.md).

## Private Gesprächscaches und Erinnerungen

Der neue Qwen3.6-Pfad behält den Cache innerhalb desselben authentifizierten Gesprächs. Ein anderes Gespräch oder ein anderer Benutzer übernimmt ihn nicht. Wechsel, Abbruch, Fehler oder fünf Minuten Inaktivität löschen den privaten Cache. Anfragen ohne Gesprächskennung verwenden keinen gespeicherten Cache.

Die beiden Ablehnungszweige vor dem Start im Host wurden entfernt. Der Server prüft die INFO-Antwort der laufenden Engine auf Unterstützung privater Caches; auch kompatible lokale Builds sind möglich. Zunächst läuft jeweils eine Anfrage; gemeinsam genutzte Prompt- und Gesprächscaches bleiben deaktiviert. Der mapped expert pack bleibt optional. Die Messungen und noch offenen Prüfungen stehen im [Release-Protokoll](docs/HAKUA_RELEASE.md).

**Hakua memory** in der Seitenleiste bietet getrennte Zustimmung zum Lesen und Speichern je Nachricht. PrismML/TurboQuant startet dafür den eigenen Server mit Authentifizierung und privaten Caches neu; beende aktive Anfragen vorher. [Anleitung](serve/MEMORY_HARNESS.md).

## Komponenten und Grenzen

Desktop/Host: `0.4.1`; native Engine: `0.4.1`; Control `0.4.2`; Node: `24.22.2`; CPython: `3.12.15`; Hakua-memory: `0.3.5`. Upstream-Referenz: `ffa80d73` / `0.2.10`.

Native Engine: `0.4.1`; Control: `0.4.2`. Der signierte stabile Feed enthält dieselbe CUDA-Komponente, die den installierten Qwen3.6-Starttest mit einem Token und 4096 Kontext bestand. Die gespeicherte Einstellung 131072 blieb erhalten; die native Generierung über das volle Kontextfenster ist nicht qualifiziert. App-Updates erfolgen manuell. Siehe [Prüfungen](docs/HAKUA_RELEASE.md).

Die Windows-x64-Prüfungen beziehen sich auf RTX 5060 Ti, CUDA sm_120 und 32 GB RAM. Andere GPUs und Betriebssysteme, native Bildeingabe und eine separate native DeepSeek-Engine sind nicht qualifiziert. Die alte Qwen3.6-Host-Arena kann etwa 18,7 GiB plus Reserve verlangen; 32 GB RAM garantieren keinen Start. Ein kurzer erfolgreicher Test bei 131.072 Kontext-Token bestätigt keine vollständige Kontextauslastung oder Qualität. TurboQuant-K-Modi bleiben nach fehlgeschlagenen Qualitätstests deaktiviert. Spin(8), Triality, Query-v3 und Bonsai sind optionale Experimente. Geschwindigkeit und Ressourcenbedarf hängen vom Modell und Computer ab.

## 96K–128K mit 16 GB Grafikspeicher

Der Editor bietet 96K (98.304) und 128K (131.072). Auf dem geprüften PC mit RTX 5060 Ti 16 GB und 32 GB RAM verarbeitete Qwen3.6 UD-Q4_K_XL mit PrismML, Q8 K/V und 28 CPU-MoE-Schichten 130.792 Eingabetokens ohne Kürzung und fand alle drei weit auseinanderliegenden Codes. Diese einzelne Anfrage dauerte etwa 29 Minuten; sie belegt weder allgemeine Qualität noch Geschwindigkeit anderer Modelle. Siehe [Einstellungen und Tests mit voller Kontextlänge](docs/WINDOWS_16GB_CONTEXT.md).

## Entwicklung

[Modellreferenz](docs/AI_REFERENCE.md) · [Build](packaging/README.md) · [Mitwirken](CONTRIBUTING.md) · [Sicherheit](SECURITY.md)

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

Strata steht unter MIT. Modellgewichte, Hakua-memory und Abhängigkeiten behalten ihre eigenen Lizenzen und Hinweise. Der optionale kleine Steuervektor ist standardmäßig aus und unterliegt der [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
