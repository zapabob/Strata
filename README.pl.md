# Strata · Hakua

## Wersja próbna 0.5.4-local.1 — oficjalne źródła 0.2.13

[Instalator Windows](https://github.com/zapabob/Strata/releases/download/v0.5.4-local.1/Strata-0.5.4-local.1-windows-x64-setup.exe) ·
[Pełny pakiet tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.4-local.1/Strata-0.5.4-local.1-windows-x64.tar.7z) ·
[Sumy i wydanie](https://github.com/zapabob/Strata/releases/tag/v0.5.4-local.1).
Windows x64 / CUDA sm_120; testowano na RTX 5060 Ti 16 GB / RAM 32 GB.
Pozostaje dwanaście naruszeń zasobów CUDA: **releaseQualified=false**.
Prism przeszedł niezmienioną próbę po jednym przekroczeniu czasu rozgrzewania.
Importuj podpisany tar.gz silnika tej wersji na ekranie przygotowania.
[Aktualna instrukcja](docs/HAKUA_INSTALL.md) · [Zakres testów](docs/UPSTREAM_0213.md).

## Stabilna wersja 0.5.1 — wcześniejsza instrukcja i pomiary

Poniższe wersje, pliki i pomiary dotyczą 0.5.1.
GitHub Latest i domyślny kanał pozostają przy tej wersji stabilnej.

Wersja 0.5.1 ładuje modele na żądanie i poprawia uruchamianie natywnego Qwen3.6. Zachowuje istniejące modele i zweryfikowane pakiety ekspertów.

Lokalne modele, czat, narzędzia i opcjonalna pamięć Hakua. To [fork zapabob](https://github.com/zapabob/Strata) projektu [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Wydanie dla Windows

Natywny Qwen3.6 osiągnął READY w 41,250 sekundy przy pojemności 4096 komórek i przeszedł sześć krótkich testów prywatnej pamięci podręcznej. Pełne wejścia 98K/131K i jakość modelu przy FP16/NVFP4 nie są zweryfikowane. Zobacz [wyniki i ograniczenia](docs/HAKUA_RELEASE.md).

Ta wersja jest przeznaczona dla Windows x64 CUDA sm_120. Testy lokalne wykonano na RTX 5060 Ti z 16 GB VRAM i 32 GB RAM. Przed instalacją przeczytaj [wyniki i pozostałe ograniczenia](docs/HAKUA_RELEASE.md).

**0.5.1** wymaga ręcznej aktualizacji i nie ma podpisu kodu Windows. [Wydanie](https://github.com/zapabob/Strata/releases/tag/v0.5.1) · [Instalacja](docs/HAKUA_INSTALL.md) · [Testy i ograniczenia](docs/HAKUA_RELEASE.md).

1. Pobierz [instalator](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64-setup.exe) i porównaj jego sumę kontrolną z [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.1/SHA256SUMS.txt).
2. Zamknij Strata, także ikonę w zasobniku, i uruchom instalator. Modele i dane osobiste przechowuj poza folderem aplikacji.
3. Zainstaluj podpisany komponent CUDA na ekranie przygotowania przez kanał latest lub dołączony plik `strata-engine-0.5.1-windows-x86_64-cuda-cuda13.tar.gz`.
4. Wybierz pasujący model lub **Use a local GGUF**, aby użyć istniejących plików. Node i Python są dołączone; systemowy interpreter ani kompilator nie są potrzebne.

Wersje są zgodne z [SemVer 2.0.0](https://semver.org/): aplikacja `0.5.1`, silnik natywny `0.5.1`; Control `0.5.1`; niezmienione środowiska PrismML/TurboQuant pozostają w wersji `0.4.0`. Typowy folder aplikacji to `%LOCALAPPDATA%\Programs\Strata` na C:, niezależnie od modeli. Istniejąca instalacja może zachować inną lokalizację.

[Pakiet tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64.tar.7z) zawiera ten sam instalator NSIS, podpisany komponent CUDA, Control, sumy kontrolne i instrukcje. Nie zawiera modeli ani danych osobistych. Publikacja używa `v0.5.1`, aliasu tagu `latest` i GitHub Latest.

## Istniejące pliki modeli

Dla podzielonego GGUF wybierz jedną część; Strata sprawdzi cały zestaw. Importowane wagi pozostają w pierwotnym miejscu. Ogólna nazwa z metadanych, np. `Hf`, jest zastępowana nazwą pliku. Nazwy nadane przez użytkownika pozostają po ponownym sprawdzeniu i restarcie.

Ustawienia zarejestrowanego modelu lokalnego można otworzyć, gdy pozostałe listy modeli nadal się ładują.

Przed przygotowaniem modelu z katalogu Strata przeszukuje wybrany folder modeli i podfoldery w ograniczonym zakresie. Jeden prawidłowy, pasujący zestaw jest używany ponownie. Kilka wyników wymaga wskazania pliku. Zwykłe pobieranie zachowuje sprawdzanie integralności i wznawianie. Silnik i opcjonalne warstwy pomocniczego modelu do przewidywania tokenów są obsługiwane osobno.

Natywne modele Qwen/Swift mogą wymagać jednorazowej konwersji do pakietu. Postęp pokazuje ukończone warstwy, jeśli konwerter je raportuje. Przy wznawianiu konwersji o małym zużyciu RAM uwzględniane jest miejsce już przydzielone plikowi tymczasowemu. Obsługiwane GGUF Hikari/PQ2_0 używają PrismML przez **Load with Strata**, bez natywnej konwersji Q2_0. Dla obsługiwanych zwykłych GGUF TurboQuant oferuje K=`FP16` i V=`TURBO2/3/4`; po zmianie wczytaj model ponownie. Zobacz [lokalne silniki](docs/LOCAL_LLAMA_BACKENDS.md).

## Prywatna pamięć podręczna rozmowy

Nowy tryb Qwen3.6 zachowuje pamięć podręczną w obrębie tej samej uwierzytelnionej rozmowy. Inna rozmowa ani inny użytkownik jej nie przejmuje. Zmiana rozmowy, anulowanie, błąd lub pięć minut bezczynności usuwa prywatną pamięć podręczną. Żądania bez identyfikatora rozmowy nie korzystają z zachowanego stanu.

Usunięto obie gałęzie Host odrzucające żądania przed uruchomieniem silnika. Serwer sprawdza obsługę prywatnej pamięci podręcznej w odpowiedzi INFO działającego silnika, także w zgodnych kompilacjach lokalnych. Początkowo obsługiwane jest jedno żądanie naraz, a współdzielone pamięci podręczne pozostają wyłączone. Mapped expert pack nadal jest opcjonalny. Pomiary i niewykonane jeszcze testy opisuje [rejestr wydania](docs/HAKUA_RELEASE.md).

Otwórz **Hakua memory** na pasku bocznym. Odczyt i zapis wymagają osobnych decyzji przy każdej wiadomości. PrismML/TurboQuant uruchamia ponownie własny serwer z uwierzytelnianiem i prywatną pamięcią podręczną; najpierw zakończ aktywne żądania. [Instrukcja](serve/MEMORY_HARNESS.md).

## Komponenty i ograniczenia

Aplikacja/Host: `0.5.1`; silnik natywny: `0.5.1`; Control `0.5.1`; Node: `24.22.2`; CPython: `3.12.15`; Hakua-memory: `0.3.5`. Wersja źródeł upstream: `5d37280d` / `0.2.11`.

0.5.1 zawiera upstream 0.2.11 i poprawki do `5d37280d`: osobne pliki rozmów, ponowne łączenie z aktywną odpowiedzią, poprawki IME i renderera, nowe modele, izolację strumieni oraz Pillow 13. Zachowuje pamięć Hakua, ponowne użycie lokalnych GGUF i prywatne pamięci podręczne Qwen3.6. Nowa kompilacja CUDA wymaga osobnych testów; wyniki 0.4.1 nie kwalifikują nowych ustawień domyślnych. Natywne generowanie z pełnym oknem pozostaje niezweryfikowane. Zobacz [testy i stan publikacji](docs/HAKUA_RELEASE.md).

Testy Windows x64 dotyczą RTX 5060 Ti, CUDA sm_120 i 32 GB RAM. Nie kwalifikują innych GPU ani systemów, natywnego wejścia obrazów ani osobnego natywnego silnika DeepSeek. Starszy sposób alokacji Qwen3.6 w RAM może wymagać około 18,7 GiB oraz rezerwy; 32 GB nie gwarantują uruchomienia. Krótka odpowiedź przy kontekście 131 072 tokenów nie potwierdza działania ani jakości całego okna. Tryby K TurboQuant pozostają wyłączone po nieudanych testach jakości. Spin(8), Triality, Query-v3 i Bonsai są opcjonalnymi eksperymentami. Wydajność i wymagane zasoby zależą od modelu i komputera.

## 96K–128K przy 16 GB VRAM

Edytor oferuje 96K (98 304) i 128K (131 072). Na testowanym komputerze z RTX 5060 Ti 16 GB i 32 GB RAM model Qwen3.6 UD-Q4_K_XL, używający PrismML, pamięci K/V Q8 i 28 warstw MoE na CPU, przetworzył 130 792 tokeny bez skracania i odnalazł wszystkie trzy odległe kody. To pojedyncze żądanie trwało około 29 minut; nie potwierdza ogólnej jakości ani szybkości innych modeli. Zobacz [ustawienia i wyniki testów pełnego kontekstu](docs/WINDOWS_16GB_CONTEXT.md).

## Rozwój

[Modele](docs/AI_REFERENCE.md) · [Budowanie](packaging/README.md) · [Wkład](CONTRIBUTING.md) · [Bezpieczeństwo](SECURITY.md)

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

Strata ma licencję MIT. Wagi modeli, Hakua-memory i zależności zachowują własne licencje oraz informacje prawne. Opcjonalny mały wektor sterujący jest domyślnie wyłączony i podlega [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).

## Wspierający oryginalny projekt Strata

Dziękujemy wszystkim, którzy wspierają Stratę.

<!-- supporters:start (one line per public supporter, newest last; copy a line and change the GitHub name in all four places) -->
<a href="https://github.com/ryan4yin"><img src="https://github.com/ryan4yin.png?size=96" width="48" height="48" alt="ryan4yin" title="ryan4yin"></a>
<a href="https://github.com/themactep"><img src="https://github.com/themactep.png?size=96" width="48" height="48" alt="themactep" title="themactep"></a>
<a href="https://github.com/macintog"><img src="https://github.com/macintog.png?size=96" width="48" height="48" alt="macintog" title="macintog"></a>
<a href="https://github.com/bisonbet"><img src="https://github.com/bisonbet.png?size=96" width="48" height="48" alt="bisonbet" title="bisonbet"></a>
<a href="https://github.com/vizv"><img src="https://github.com/vizv.png?size=96" width="48" height="48" alt="vizv" title="vizv"></a>
<a href="https://github.com/kod88vn"><img src="https://github.com/kod88vn.png?size=96" width="48" height="48" alt="kod88vn" title="kod88vn"></a>
<a href="https://github.com/seoulworker"><img src="https://github.com/seoulworker.png?size=96" width="48" height="48" alt="seoulworker" title="seoulworker"></a>
<a href="https://github.com/jackyini"><img src="https://github.com/jackyini.png?size=96" width="48" height="48" alt="jackyini" title="jackyini"></a>
<a href="https://github.com/router0mail"><img src="https://github.com/router0mail.png?size=96" width="48" height="48" alt="router0mail" title="router0mail"></a>
<!-- supporters:end -->
