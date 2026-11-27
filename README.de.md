# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata ist der auf Windows ausgerichtete Fork von [Niko1221/Strata](https://github.com/Niko1221/Strata). Lokale Modelle übernehmen Chats, Programmieraufgaben und Agentenabläufe. Bei kompatiblen MoE-Modellen kann die native Engine Expertengewichte auf Grafikspeicher, Arbeitsspeicher und SSD verteilen.

## Einstieg

Den Windows-Installer für das aktuelle Benutzerkonto gibt es auf der [Hakua-Veröffentlichungsseite](https://github.com/zapabob/Strata/releases). Die CUDA-Engine wird separat verteilt. Wähle in **Modelle** das zu den installierten Gewichten passende Profil. Für Inkling 2 Mini SC117 gibt es eigene Profile für SQ-10, SQ-15 und SQ-20. Stelle die Kontextlänge nach dem verfügbaren Speicher ein. Einzelheiten stehen in der [Windows-Anleitung](docs/HAKUA_INSTALL.md) und der [Modellübersicht](docs/MODELS.md).

## Arbeitsabläufe wiederverwenden

Unter **Einstellungen → Werkzeuge** lässt sich die Suche nach Skills bei Bedarf einschalten. Der Agent kann dann passende Skills suchen und gezielt öffnen. In **Skills** lassen sich das Lernen aus abgeschlossenen Aufgaben und die automatische Anwendung einzeln einschalten. Abläufe werden als bearbeitbare `SKILL.md` gespeichert. Namen, Auslöser und Arbeitsbereiche bestimmen die automatische Auswahl. Für Skills, Hilfsagenten, Dateiwerkzeuge und `/goal` gibt es eigene Schalter. [Anleitung für Arbeitsabläufe](docs/WORKFLOW_SKILLS.md)

## Messungen

Auf einer RTX 5060 Ti mit 16 GB erstellte SC117 SQ-10 über `/goal` eine Pagoda-Bench-Szene als einzelne HTML-Datei und korrigierte den eigenen Renderer nach Diagnosehinweisen. Nach dem Herauszoomen zeigte Chrome fünf Dächer. Die Szene meldete 7.079 Voxel. In der Startansicht war die Spitze abgeschnitten. Eine offizielle Wertung liegt noch aus. Die [Messungen der Engine 0.8.5](_docs/2026-11-27_v085-release-notes.md) verwenden kurze Eingaben bei der angegebenen Kontextkapazität.

Kompatibilität, Signierung und Prüfgrenzen stehen im [Veröffentlichungsprotokoll](docs/HAKUA_RELEASE.md). Hakua steht unter der [MIT-Lizenz](LICENSE). Modelle und Komponenten haben eigene Bedingungen.
