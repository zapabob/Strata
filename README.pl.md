# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Polski](README.pl.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md)

Lokalna sztuczna inteligencja dla Windows, z czatem, pracą agentów, badaniami i wyborem kompatybilnych modeli. Hakua to fork zapabob projektu Niko1221/Strata, utrzymywany niezależnie.

<!-- upstream v0.2.20 -->
v0.8.0 zachowuje wszystkie funkcje fork-a i dostarcza **cztery nowo zoptymalizowane natywne silniki CUDA 13.5 / SM120** (rodzina **0.6.8**, upstream **v0.2.20**). Wszystkie zbudowano z commitu `9b4b8b09f` z 5 watkami i zweryfikowano pelnym SHA-256:
- `strata-inkling2.exe`: AVX2 CPU MoE bez przelewow, podwojny bufor PCIe bez kopiowania (`moe_up` 39,5 do 3,5 ms, -91 %), bootstrap ST-MoE Rho; Sakura 131K 20,93 do 29,76 t/s (+42,2 %), 32/32 dokladnych tokenow.
- `strata.exe`: matematyka AVX2 Gen-F/G i poprawiony czytnik warstw GGUF.
- `strata-q38.exe`: jadro norm float4 i poprawki sciezek CMake dla SM120.
- `strata-hy4.exe`: MUFU.TANH Blackwell, wektoryzacja float4 i bootstrap ST-MoE.
Takze: oficjalne wejscie v0.2.20, naprawa pustej odpowiedzi Sakura 98K, dostawca `inkling2` Hermes Agent z autostartem i tabele Ryu (kuraneko1, MIT, PR #6571). Weryfikacja podpisu usunieta; SHA-256 zachowany. `releaseQualified=false`.

## Co zmieniło się w 0.8.0

Uwaga: wartości DS4 2,84x / FLA 4,86x / Sakura 22,44 t/s pochodzą z dzienników rozwoju Antigravity i nie zostały niezależnie odtworzone w tej sesji budowy. Ta sesja zmierzyła 9,09 t/s prefill / 11,78 t/s decode na kanonicznym GGUF przy 32K.

To wydanie zachowuje wszystkie funkcje forkowe i dodaje natywne optymalizacje z 22/23-11. Produkt to **0.8.0**, rodzina silników natywnych **0.6.8**, źródło upstream **Niko1221/Strata v0.2.20** (Control/engines 0.1.66). Optymalizacje RTX 5060 Ti (sm_120a) / CUDA 13.5: DS4-9B prefill 2,84x szybciej, decode +13,4%, E2E +22,7%; FLA GDN + Spin(8) exp2f prefill 4,86x i kompresja KV 59,4%; branchless router Inkling-2 (1,16x); Sakura Inkling-2-Mini 65K–98K (`--expert-vram 7.8` daje decode 22,44 t/s, 12,7x, 32/32 identyczne tokeny). Warstwa serve czyta tokenizator i szablon czatu osadzone w GGUF oraz udostępnia parser wyjścia Inkling; Hermes Agent ma providera `inkling2`. Tablice profili SM × VRAM Ryu (kuraneko1, MIT) zostały włączone do oficjalnego CUDA Inkling-2 i odesłane upstream jako PR #6571. Weryfikacja podpisu usunięta (brak klucza); hashe SHA-256 pozostają. `releaseQualified=false`.


Aktualizacja Gen-H (commit 21bedf91c): strata-inkling2.exe i strata.exe uzywaja float4 k_stack_rms_norm/k_mix z exp2f, cache Zipf i zero-copy h_tok_buf; moe_up 39,5 do 4,6 ms (-88 %), 32/32 dokladnych tokenow na Sakura 131K.

## Wersja i pobieranie

Bieżące wydanie: **0.8.0** — GitHub Latest: [strona wydania](https://github.com/zapabob/Strata/releases/tag/v0.8.0). Instalator desktop pobierz z **Assets**; plik nazywa się `Strata-0.8.0-windows-x64-setup.exe` (binarny aplikacji nie był przebudowany dla 0.8.0, zmienił się tylko silnik). Pakiet: `Strata-0.8.0-windows-x64.tar.7z`. Silniki GPU to opcjonalne komponenty w tych samych Assets: `strata-engine-0.6.8-windows-x86_64-cuda-cuda13.tar.gz` (Q38 27B/9B + Inkling-2, CUDA 13.5) i `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`. Zawsze otwieraj stronę wydania i wybieraj dokładny plik z Assets. SHA-256 pozostaje kontrolą integralności; `releaseQualified=false`.


## Zachowane funkcje forkowe

Q38 27B/9B dense, DS4/DeepSeek, RAM32, Hakua UI/pamięć, workflow skills, 8 języków README. Szczegóły: [README.md](README.md).
