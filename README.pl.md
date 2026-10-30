# Hakua / Strata

Chatbot Hakua oparty na Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · kroki instalacji w 30 sekund

Pobierz i uruchom instalator Windows tego forka, wybierz zgodny model i załaduj go. Hakua memory na pasku bocznym otwiera czat z pamięcią. Same kroki zajmują około 30 sekund; pobieranie, instalacja i ładowanie trwają dłużej.

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Strata_0.3.3-preview.20261030.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/SHA256SUMS.txt)

Archiwum 7z zawiera ten sam instalator. Rozpakuj je, a następnie uruchom plik EXE instalatora.

## Funkcje tego forka

Hakua odczytuje wspomnienia i zapisuje podsumowanie wyłącznie po zgodzie na dane żądanie. Obie zgody są niezależne i potem resetowane. Po załadowaniu obsługiwanego modelu natywnego aplikacja automatycznie tworzy lokalny profil pamięci. Otwórz Hakua memory, skopiuj klucz profilu z okna dialogowego i zaznacz opcję pamięci na stronie lokalnej, a następnie wklej klucz w About → Settings. [Przewodnik pamięci](serve/MEMORY_HARNESS.md) opisuje także konfigurację serwera uruchamianego ze źródeł.

Narzędzia Hermes synchronizują zatwierdzone SOUL.md / MEMORY.md i zapewniają pamięć Ebbinghausa, graf semantyczny, eksport Obsidian i konsolidację sleep. Działają osobno od czatu; opcjonalne zależności RAG i embeddingów nie są w instalatorze podstawowym.

Dla lokalnego pliku GGUF PQ2_0 wybierz backend llama-server `PrismML` w zaawansowanych ustawieniach modelu. Dla standardowego GGUF z TurboQuant wybierz `TurboQuant`, a następnie ustaw K na `FP16`, a V na `TURBO2`, `TURBO3` lub `TURBO4`. Formaty TurboQuant dla K są w tej wersji wyłączone, ponieważ testy z rzeczywistym modelem dały uszkodzone odpowiedzi. Po zmianie backendu ponownie załaduj model. Każdy backend korzysta z własnych dołączonych programów i bibliotek; PQ2_0 i TurboQuant to oddzielne ścieżki. Zobacz [konfigurację i ograniczenia](docs/LOCAL_LLAMA_BACKENDS.md).

Eksperymenty Spin(8)/Triality, Query-v3 i Bonsai wymagają zgodnych, jawnych ustawień. Nie deklarujemy ogólnego wzrostu szybkości ani jakości.

Pakiet zawiera prywatne Node i Python, Hakua-memory 0.3.5 oraz silnik CUDA zbudowany z tego forka. Uruchomienie modelu nie instaluje pakietów Python ani nie kompiluje kodu.

## Zgodność i aktualizacje

Ten pakiet Windows jest dla NVIDIA RTX serii 50, CUDA sm_120. Inne GPU, Linux i macOS wymagają osobnych pakietów. Instalator projektu źródłowego nie zawiera tych zmian. Wagi pobiera się osobno; mogą zajmować dziesiątki lub setki GB. Preferuj zgodne pakiety ISTA-DASLab, następnie Unsloth i Gyro.

Modele i wspomnienia przechowuj poza folderem aplikacji. Osobiste wspomnienia, klucze i wagi nie są dołączone. Zamknij aplikację przed aktualizacją. Aby wrócić, zachowaj kopię danych i zainstaluj starsze wydanie forka.

[Models](docs/MODELS.md) · [Install](docs/HAKUA_INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Wersje i weryfikacja

| | |
| --- | --- |
| GUI / Product | `0.3.3-preview.20261030.1` |
| Engine | `0.3.3` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `870aedd9` · 0.2.8 |

<!-- App version in this preview tree: `0.3.3-preview.20261030.1` -->

Wersja podglądowa jest niepodpisana. Przed instalacją sprawdź SHA256SUMS.txt. [Raport kwalifikacji](docs/HAKUA_RELEASE.md) podaje rzeczywiste wyniki i ograniczenia. Sama kompilacja nie dowodzi poprawnego wnioskowania. Ta niepodpisana wersja testowa wymaga ręcznej aktualizacji instalatorem; podpisane aktualizacje automatyczne nie zostały jeszcze zweryfikowane.

## Rozwój i pomoc

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Fork Strata na licencji MIT. Hakua-memory i wagi mają osobne licencje. Zachowano uznanie autorstwa projektu źródłowego.

Opcjonalny wektor sterujący upstream (480 KB) pozostaje domyślnie wyłączony i podlega [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE). Pełne wagi modelu pobiera się oddzielnie.
