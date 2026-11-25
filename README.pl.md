# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

**Lokalna AI zaprojektowana, by wykorzystać każdy zasób Twojego komputera z Windows — GPU, fizyczne rdzenie + wątki SMT procesora, pamięć RAM oraz dyski NVMe/SSD.** Hakua to niezależny fork `zapabob/Strata` projektu [Niko1221/Strata](https://github.com/Niko1221/Strata), zsynchronizowany z oficjalnym upstreamem **v0.2.21** (`d46f5f268`, silnik/Control `0.1.67`), przy zachowaniu wszystkich własnych silników forka, przepływów pamięci/agentów oraz optymalizacji Blackwell CUDA 13.5.

## Nowości w 0.8.1 (Silnik 0.7.0)

- **Pełnomaszynowa heterogeniczna inferencja na wszystkich 4 warstwach sprzętu (GPU + CPU 6P/6SMT + RAM + SSD)**:
  - **Natywny backend Windows `aux_cpus` CPU Sets + podział SMT dla I/O** (`engine/include/strata/platform/aux_cpus.hpp`, `ssd_stream_scheduler.hpp`, `direct_file.cpp`): przypina pętlę hosta GPU oraz obliczenia AVX2 MoE wyłącznie do fizycznych rdzeni głównych, a wszystkie poboczne wątki SMT (`io_smt=[1,3,5,7,9,11]` na CPU 6C/12T) przeznacza na 6-wątkowe nakładane Direct I/O oraz asynchroniczny streaming `PrefetchVirtualMemory`.
  - **5 świeżo skompilowanych silników natywnych CUDA 13.5 / SM120 Blackwell** (`strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`) z mapowanymi doorbellami zero-copy Gen-K/L, ochroną VRAM WDDM 1536 MiB, bezpiecznymi pod względem commit budżetami RAM w Windows (`hy4_cpu_experts.cpp`, `inkling2_engine.cu`), przypinaniem do rdzeni fizycznych Windows + oczekiwaniem `_mm_pause` (`ink_hybrid.cuh`) oraz buforowaniem embeddingów w przypiętym RAM-ie i grupowym `PrefetchVirtualMemory` dla SM120 Q38 (`engine/q38/src/engine.cu`).
  - **Zunifikowany launcher pełnomaszynowy i presety**: `tools/full_machine_infer.py` (`--list-models`, `--plan`, `--bench`, `--serve`) automatycznie wykrywa GPU, topologię fizyczną/SMT CPU, zapas RAM/commit oraz dyski SSD, generując 3-warstwowe plany wykonania i gotowe konfiguracje serwera w `configs/`.
- **3-drożny merge z oficjalnym upstreamem v0.2.21**: integruje oficjalny zunifikowany 4-warstwowy MoE (GPU+RAM+CPU+SSD), multi-GPU `--layer-split`, aktualizacje GUI/hosta i poprawki Control/silnika `0.1.67` wraz ze wszystkimi funkcjami forka (`/btw`, `/deepresearch`, RustXNG Full, umiejętności przepływów pracy, gęsty runner Q38, rozszerzenie DeepSeek, dostawca Hermes `inkling2` oraz tabele profili MIT Inkling-2 od kuraneko1).

## Zmierzona wydajność na rzeczywistym sprzęcie

Zmierzono na **NVIDIA GeForce RTX 5060 Ti 16 GB (SM120, CUDA 13.5) · AMD Ryzen 5 4500 (6C/12T) · 32 GB DDR4 · Dwa SSD (`C:` Crucial P3 NVMe + `H:` S5-1TB SSD)** dla promptów 16-tokenowych i zachłannego dekodowania 32 tokenów:

| Model (Rozmiar) | Silnik i kontekst | Aktywne warstwy | Prefill (`pp`) | Decode (`tg`) | Zgodność |
|---|---|---|---:|---:|---|
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | GPU 10.85 GiB (2232 eksp.) + przypięty RAM 4.34 GiB (840 eksp.) + 6P/6SMT | **85.08 t/s** | **42.22–42.33 t/s** | **32/32 dokładna** |
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | Spill 3-warstwowy: GPU 10.85 GiB + RAM 3.60 GiB + **SSD mmap 0.74 GiB (`prefetch=on`)** + 6P/6SMT | 64.80 t/s | 14.24 t/s | **32/32 dokładna** |
| **Inkling-2-Mini UD Q4_K_M** (15.47 GiB) | `strata-inkling2.exe` · 16K (Q8 KV) | GPU 10.42 GiB (2339 eksp.) + przypięty RAM 3.34 GiB (733 eksp.) + 6P/6SMT | **109.64 t/s** | **53.28 t/s** | Czysty greedy |
| **Qwen3.8-27B 3.69bpw MTP** (11.73 GiB) | `strata-q38.exe` · 4K (F16 KV) | Wagi GPU SM120 (10.44 GiB) + staging emb w przypiętym RAM + `PrefetchVirtualMemory` | 6.21 s na zimno | **29.95 t/s** | Czysty greedy |

*Uwaga o wątkach CPU (test A/B na Ryzen 5 4500)*: utrzymanie workerów obliczeniowych na 6 rdzeniach fizycznych (`host=0`, `workers=2,4,6,8,10`) z wątkami SMT (`1,3,5,7,9,11`) zarezerwowanymi dla I/O osiągnęło **42.22–42.33 t/s**, wobec **29.68 t/s** (-21.9%) przy przeciążeniu 11 workerami obliczeniowymi na wątkach SMT.

## Wersja i pobieranie

Aktualne wydanie: **0.8.1** — GitHub Latest: [strona wydania v0.8.1](https://github.com/zapabob/Strata/releases/tag/v0.8.1).

- **Instalator Desktop**: `Strata-0.8.1-windows-x64-setup.exe` (aplikacja Tauri/NSIS na użytkownika z wbudowanym Node 24.22.3, Pythonem, Control 0.6.3 i RustXNG Full).
- **Pakiet instalatora**: `Strata-0.8.1-windows-x64.tar.7z` (instalator + `SHA256SUMS.txt`).
- **Komponent silnika CUDA 13.5 SM120 (opcjonalny)**: `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` (wszystkie pięć przebudowanych silników SM120: `strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`).
- **Komponent Hy4-Flash (opcjonalny)**: `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`.

Zawsze pobieraj bezpośrednio z listy **Assets** wydania i weryfikuj sumy SHA-256. Weryfikacja podpisu ed25519 komponentów została usunięta (brak klucza podpisującego); brak podpisu Windows Authenticode; **`releaseQualified=false`**.

![Hakua / Strata prawdziwy czat japoński na Qwen3.8-27B](docs/media/native-qwen38-japanese-chat.png)
*Aplikacja desktopowa Hakua / Strata uruchamiająca `qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf` przez `strata-q38.exe` (CUDA 13.5 / RTX 5060 Ti 16 GB).*

## Szybki start (CLI pełnomaszynowe i Desktop)

### Instalacja desktopowa lub aktualizacja przez nadpisanie

1. Zakończ aktywne zapytania, odładuj modele, wykonaj kopię zapasową danych aplikacji i zamknij Strata (wraz z ikoną w zasobniku systemowym).
2. Uruchom `Strata-0.8.1-windows-x64-setup.exe` do dotychczasowego katalogu instalacji, aby zaktualizować aplikację z zachowaniem modeli, czatów, pamięci, narzędzi, kluczy API i zatwierdzeń.
3. Zaimportuj `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` przez *I already have the file*, wybierz zgodny model lub lokalny plik GGUF i kliknij **Load**. Zobacz [instalacja i wycofanie zmian](docs/HAKUA_INSTALL.md).

### Launcher pełnomaszynowy (`tools/full_machine_infer.py`)

```powershell
# Sprawdź warstwy GPU/CPU/RAM/SSD i wykryj lokalne modele
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --list-models

# Uruchom benchmark Sakura Inkling-2-Mini 131K z ustawieniami pełnomaszynowymi
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --bench --model Sakura --max-new 32

# Uruchom lokalny serwer API OpenAI/Anthropic (127.0.0.1:8092) z RAM squeeze
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model Sakura --port 8092 --squeeze
```

## Polecany GGUF i funkcje forka

- **Lokalny czat Qwen3.8-27B na 16 GB VRAM**: przetestowany z [mieszanym GGUF 3.69 bpw od soyaakinohara](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf) (podziękowania dla **soyaakinohara** i **AEON-7**). Zacznij od kontekstu 4 096 tokenów; etykieta `12GB` w nazwie pliku nie gwarantuje zmieszczenia się na karcie 12 GB.
- **Własny gęsty runner Q38 (`strata-q38.exe`)**: polimorfizm mieszanej kwantyzacji na tensor w 11 formatach (`F32`, `F16`, `BF16`, `Q8_0`, `Q4_K`, `Q5_K`, `Q6_K`, `IQ3_S`, `IQ2_S`, `IQ4_XS`, `PQ2_0`), prefill na rdzeniach Tensor, tryby KV Spin(8) / TurboQuant (`auto`: `f16` → `f16_turbo4` → `spin8_k8v4`), draft/verify MTP `K=3` i opcjonalny profil ortografii japońskiej. Zobacz [QWEN38_DENSE_NATIVE.md](docs/QWEN38_DENSE_NATIVE.md).
- **Narzędzia agentów i przepływów pracy**: beznarzędziowy subagent pytań pobocznych `/btw` z niezależnym zatrzymywaniem, `/research` i `/deepresearch` z wbudowanym RustXNG Full (odpytuje zewnętrznych dostawców po włączeniu), opcjonalne prywatne uczenie i stosowanie umiejętności przepływu, CRUD plików w obszarze roboczym/pasku bocznym oraz pamięć czatu z zakresem. Zobacz [WORKFLOW_SKILLS.md](docs/WORKFLOW_SKILLS.md) i [BROWSER_SEARCH.md](docs/BROWSER_SEARCH.md).

## Progi bezpieczeństwa i ograniczenia

Bez zmian: **3 GiB wolnego RAM**, **4 GiB zapasu commit**, **>= 768 MiB rezerwy GPU** (`1536 MiB` domyślnej rezerwy WDDM dla Inkling-2 `<= 17 GiB`), **5 GiB wolnego na `C:`** i **10 GiB wolnego na `H:`**. Ogólna jakość modeli, generowanie pełnego okna kontekstu oraz jednoczesna wielokliencka współbieżność GPU pozostają niezakwalifikowane (**`releaseQualified=false`**). To wydanie forka dla Windows nie obejmuje natywnego wejścia obrazu ani zakwalifikowanej inferencji na Linux/macOS. Zapisy historyczne zachowują oryginalne wersje w [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Dokumentacja i rozwój

[Instalacja](docs/HAKUA_INSTALL.md) · [Dowody wydania](docs/HAKUA_RELEASE.md) · [API i sprzęt](docs/AI_REFERENCE.md) · [Terminal](docs/TERMINAL.md) · [Budowa ze źródeł](docs/SOURCE_INSTALL.md) · [Pakowanie](tools/packaging/README.md) · [Współpraca](.github/CONTRIBUTING.md) · [Bezpieczeństwo](.github/SECURITY.md) · [Licencja](LICENSE)

```powershell
pytest tests/test_full_machine_infer.py
python -m pytest terminal/tests/terminal
```

```powershell
cd app/host
pnpm test
pnpm run build
```

[Niko1221/Strata](https://github.com/Niko1221/Strata) · [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [Informacje o bibliotekach zewnętrznych](third_party/)

## Podziękowania

Serdeczne podziękowania dla **Niko1221/Strata**, **kuraneko1 (`_ryu15_`)**, **ggml & llama.cpp**, **NousResearch (Hermes Agent)**, **Qwen Team (Alibaba Cloud)**, **NVIDIA**, **RustXNG**, **libstrix**, **Node.js / Python / Tauri**, **Microsoft**, **ISTA-DASLab**, **PrismML**, **TurboQuant**, **Spin(8)**, **soyaakinohara** oraz **AEON-7** za fundamenty open-source, wagi i badania umożliwiające rozwój Hakua / Strata.
