# Strata · Hakua

Lokalne modele, czat, narzędzia i opcjonalna pamięć Hakua. To [fork zapabob](https://github.com/zapabob/Strata) projektu [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Wersja testowa dla Windows

Ta beta jest nadal sprawdzana i nie została jeszcze opublikowana. Poniższe nazwy plików i kroki instalacji opisują planowane wydanie; zobacz [aktualny stan](docs/HAKUA_RELEASE.md).

**0.4.1-beta.1** wymaga ręcznej aktualizacji i nie ma podpisu kodu Windows. [Wydanie](https://github.com/zapabob/Strata/releases/tag/v0.4.1-beta.1) · [Instalacja](docs/HAKUA_INSTALL.md) · [Testy i ograniczenia](docs/HAKUA_RELEASE.md).

1. Pobierz [instalator](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/Strata_0.4.1-beta.1_x64-setup.exe) i porównaj jego sumę kontrolną z [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/SHA256SUMS.txt).
2. Zamknij Strata, także ikonę w zasobniku, i uruchom instalator. Modele i dane osobiste przechowuj poza folderem aplikacji.
3. Pobierz `strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz` z tego wydania beta i zaimportuj plik na ekranie przygotowania. Kanał latest nadal udostępnia poprzedni silnik.
4. Wybierz pasujący model lub **Use a local GGUF**, aby użyć istniejących plików. Node i Python są dołączone; systemowy interpreter ani kompilator nie są potrzebne.

Wersje są zgodne z [SemVer 2.0.0](https://semver.org/): aplikacja `0.4.1-beta.1`, silnik natywny/Control `0.4.1`; niezmienione środowiska PrismML/TurboQuant pozostają w wersji `0.4.0`. Typowy folder aplikacji to `%LOCALAPPDATA%\Programs\Strata` na C:, niezależnie od modeli. Istniejąca instalacja może zachować inną lokalizację.

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

Aplikacja/Host: `0.4.1-beta.1`; silnik natywny/Control: `0.4.1`; Node: `24.22.2`; CPython: `3.12.15`; Hakua-memory: `0.3.5`. Wersja źródeł upstream: `ffa80d73` / `0.2.10`.

Kandydat osobnego komponentu CUDA zawiera silnik natywny 0.4.1 oraz niezmienione środowiska PrismML/TurboQuant 0.4.0. Po weryfikacji jego nowy manifest zostanie podpisany kluczem komponentów tego forka. Po publikacji zaimportuj plik z tej wersji beta; stabilny kanał zachowuje poprzedni pakiet. Podpis komponentu jest odrębny od podpisu kodu Windows aplikacji. Identyfikatory znajdują się w [rejestrze wydania](docs/HAKUA_RELEASE.md).

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
