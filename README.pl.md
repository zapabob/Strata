# Hakua / Strata

Czatbot Hakua na Stracie. Ten fork oferuje podgląd Windows z Hakua memory i osobnymi runtime’ami GPU. [zapabob/Strata](https://github.com/zapabob/Strata) · upstream [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Instalacja (podgląd Windows)

1. Pobierz [EXE instalatora](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) (albo [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) z tym samym EXE).
2. Porównaj z [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt) przed uruchomieniem. Brak podpisu kodu Windows. Skróty tej etykiety odświeżono 2026-11-02; nie używaj starego SUMS.
3. Jeśli Strata jest już zainstalowana, całkowicie ją zamknij (zasobnik → Quit Strata) i uruchom EXE.
4. Przy pierwszym starcie zainstaluj oferowany podpisany silnik albo zaimportuj pasujący `.tar.gz` z tej samej wersji. Potem wybierz folder modeli i wczytaj model.

Ścieżka kliknięć jest krótka. Pobieranie, aktywacja silnika i wczytywanie modelu trwają dłużej i wymagają miejsca na dysku oraz VRAM. Szczegóły: [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md). Zmierzona zakres: [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Co zawiera instalator

| W instalatorze aplikacji | Osobno |
| --- | --- |
| GUI / Host, prywatny Node 24.22.2, Control / CPython 3.12.15, Hakua-memory 0.3.5, Harness | Podpisany komponent CUDA (~1,4 GB): natywne Strata + PrismML + TurboQuant |
| Ręczne aktualizacje aplikacji tym EXE | Wagi modeli (dziesiątki lub setki GB) |

Do opublikowanej aplikacji nie potrzeba systemowego Node, Pythona, pip ani kompilatora. Instalator upstream Niko1221 nie zawiera zmian tego forka.

## Wczytywanie lokalnego modelu

- **Natywne pakiety Strata** (obsługiwane pakiety tekstowe Qwen): natywna ścieżka prepare / load w aplikacji.
- **Hikari / PQ2_0 GGUF**: użyj **Load with Strata** (PrismML). Nie używaj natywnego prepare dla PQ2_0.
- **Zwykły GGUF + cache TurboQuant**: backend `TurboQuant`, K=`FP16`, V=`TURBO2` / `TURBO3` / `TURBO4`, potem przeładuj. Tryby K TurboQuant pozostają wyłączone po uszkodzonych odpowiedziach w testach rzeczywistych.

PrismML i TurboQuant to osobne pliki wykonywalne w komponencie silnika. Szczegóły: [LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md). Preferuj pakiety mieszczące się w GPU: ISTA-DASLab → Unsloth → Gyro.

Gdy model działa ścieżką Strata / supervisor, Agent może użyć tej lokalnej instancji do narzędzi wspieranych przez model (np. wyszukiwanie w sieci). Sesja wyłącznie natywna nie udostępnia tej samej ścieżki.

## Hakua memory

Po wczytaniu obsługiwanego modelu otwórz **Hakua memory** na pasku bocznym. Zgody odczytu i zapisu są osobne i resetują się co turę.

- Natywna: wklej klucz z dialogu do About → Settings i zaznacz pamięć na stronie lokalnej.
- PrismML / TurboQuant: aplikacja podaje lokalny klucz; przed pierwszym otwarciem dokończ aktywne żądania.

Przewodnik: [MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md). Narzędzia Hermes SOUL/MEMORY są oddzielne od czatu i nie są wymagane do podstawowego użycia.

## Wersje

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine / Control | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Zamrożenie upstream | `c62d5e3a` · 0.2.9 |

Strona wydania: [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1). Silnik i feed mają podpis Ed25519 i są sprawdzane przez aplikację. Automatyczne podpisane aktualizacje aplikacji nie są kwalifikowane; aktualizuj tym instalatorem.

## Ograniczenia (zmierzony podgląd)

Windows x64, NVIDIA RTX 50 / CUDA sm_120, sprawdzone na RTX 5060 Ti. Zawiera natywny tekst. Bez natywnego wejścia obrazu i osobnego natywnego silnika DeepSeek. Inne GPU i systemy potrzebują własnych pakietów. Modele i pamięć osobistą trzymaj poza folderem aplikacji. Wydanie nie zawiera osobistych pamięci, kluczy ani pełnych pakietów wag.

Spin(8) / Triality / Query-v3 / Bonsai pozostają opcjonalnymi eksperymentami. Brak ogólnej obietnicy szybkości lub jakości.

## Rozwój

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Models](docs/MODELS.md) · [Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Fork Strata na licencji MIT. Hakua-memory i wagi mają własne licencje. Zachowane kredyty autorów i upstreamu. Opcjonalny wektor kontrolny (~480 KB) domyślnie wyłączony na [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
