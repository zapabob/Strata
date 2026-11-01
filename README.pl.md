# Hakua / Strata

Chatbot Hakua oparty na Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · kroki instalacji w 30 sekund

Pobierz i uruchom instalator Windows tego forka. Przy pierwszym uruchomieniu zainstaluj proponowany zgodny silnik, a następnie wybierz i załaduj model. Hakua memory na pasku bocznym otwiera czat z pamięcią. Same kroki zajmują około 30 sekund; pobieranie, instalacja i ładowanie trwają dłużej.

Wersja zapoznawcza Windows 0.4.0: wykonane testy i obsługiwane zakresy opisuje [rejestr weryfikacji](docs/HAKUA_RELEASE.md).

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt)

Archiwum 7z zawiera ten sam instalator. Rozpakuj je, a następnie uruchom plik EXE instalatora.

## Funkcje tego forka

Hakua odczytuje wspomnienia i zapisuje podsumowanie wyłącznie po zgodzie na dane żądanie. Obie zgody są niezależne i potem resetowane. Po załadowaniu obsługiwanego modelu natywnego aplikacja automatycznie tworzy lokalny profil pamięci. Otwórz Hakua memory, skopiuj klucz profilu z okna dialogowego i zaznacz opcję pamięci na stronie lokalnej, a następnie wklej klucz w About → Settings. [Przewodnik pamięci](serve/MEMORY_HARNESS.md) opisuje także konfigurację serwera uruchamianego ze źródeł.

PrismML/PQ2_0 i TurboQuant także mogą korzystać z Hakua-memory. Załaduj model i otwórz Hakua memory na pasku bocznym. Nowe okno automatycznie używa lokalnego klucza użytkownika; odczyt i zapis wybiera się osobno dla każdego żądania. Przed pierwszym otwarciem zakończ aktywne żądania: serwer zarządzany przez aplikację uruchomi się ponownie z uwierzytelnianiem i bez wspólnych pamięci podręcznych. Wszystkie trzy ścieżki używają tego samego lokalnego profilu. Przy starcie porównywane są wersje GUI, Host i aplikacji; niezgodne lub niedostępne pliki powodują wyświetlenie instrukcji naprawy.

Narzędzia Hermes synchronizują zatwierdzone SOUL.md / MEMORY.md i zapewniają pamięć Ebbinghausa, graf semantyczny, eksport Obsidian i konsolidację sleep. Działają osobno od czatu; opcjonalne zależności RAG i embeddingów nie są w instalatorze podstawowym.

Dla lokalnego pliku GGUF PQ2_0 wybierz backend llama-server `PrismML` w zaawansowanych ustawieniach modelu. Dla standardowego GGUF z TurboQuant wybierz `TurboQuant`, a następnie ustaw K na `FP16`, a V na `TURBO2`, `TURBO3` lub `TURBO4`. Formaty TurboQuant dla K są w tej wersji wyłączone, ponieważ testy z rzeczywistym modelem dały uszkodzone odpowiedzi. Po zmianie backendu ponownie załaduj model. Każdy backend korzysta z własnych programów i bibliotek w osobnym komponencie silnika; PQ2_0 i TurboQuant to oddzielne ścieżki. Zobacz [konfigurację i ograniczenia](docs/LOCAL_LLAMA_BACKENDS.md).

Eksperymenty Spin(8)/Triality, Query-v3 i Bonsai wymagają zgodnych, jawnych ustawień. Nie deklarujemy ogólnego wzrostu szybkości ani jakości.

Tak jak oficjalna aplikacja, instalator zawiera prywatne Node i Python oraz Hakua-memory 0.3.5. Silniki GPU są dystrybuowane osobno: po wybraniu instalacji aplikacja pobiera podpisany komponent Hakua lub importuje wcześniej pobrany plik. Komponent zawiera środowiska natywnego CUDA, PrismML i TurboQuant. Wagi modeli pobiera się oddzielnie. Wydana aplikacja nie wymaga systemowych Node lub Python, pip ani kompilatora.

## Zgodność i aktualizacje

Ten pakiet Windows jest dla NVIDIA RTX serii 50, CUDA sm_120. Inne GPU, Linux i macOS wymagają osobnych pakietów. Instalator projektu źródłowego nie zawiera tych zmian. Wagi pobiera się osobno; mogą zajmować dziesiątki lub setki GB. Preferuj zgodne pakiety ISTA-DASLab, następnie Unsloth i Gyro.

Osobno dystrybuowany silnik natywny służy do rozmowy tekstowej. Ta wersja podglądowa nie zawiera natywnej obsługi obrazów ani osobnego natywnego silnika DeepSeek.

Modele i wspomnienia przechowuj poza folderem aplikacji. Osobiste wspomnienia, klucze i wagi nie są dołączone. Zamknij aplikację przed aktualizacją. Aby wrócić, zachowaj kopię danych i zainstaluj starsze wydanie forka.

Gdy włączone jest chowanie do zasobnika, × ukrywa okno. Przed aktualizacją kliknij prawym przyciskiem ikonę Strata w zasobniku i wybierz Zakończ Strata, aby całkowicie zamknąć aplikację.

[Models](docs/MODELS.md) · [Install](docs/HAKUA_INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Wersje i weryfikacja

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `c62d5e3a` · 0.2.9 |

<!-- App version in this preview tree: `0.4.0-preview.20261101.1` -->

Instalator nie ma podpisu kodu Windows. Przed instalacją sprawdź SHA256SUMS.txt. Osobny komponent silnika i jego kanał aktualizacji są podpisane i weryfikowane przez aplikację. Aplikację aktualizuje się ręcznie instalatorem; jej podpisane aktualizacje automatyczne nie są jeszcze zweryfikowane. [Raport kwalifikacji](docs/HAKUA_RELEASE.md) podaje wyniki i ograniczenia, w tym testy pamięci z rzeczywistymi modelami.

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
