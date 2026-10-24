<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <b>Português</b></p>

<h3 align="center">Strata — Cache KV Triality Spin(8), Dialetos CUDA TurboQuant e Mecanismo de Inferência MoE Nativo</h3>

<p align="center">
  <b>Fork de engenharia de <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Atenção Triality Spin(8) $\mathrm{Cl}(8,0)$ · Cache KV Quantizado de Três Visões · Sidecars Query-v3 `.prismq3` · Controle Completo via GUI e CLI
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Visão Geral deste Fork (`zapabob/Strata`)

**`zapabob/Strata`** é um fork avançado de pesquisa e engenharia baseado no [Strata](https://github.com/Niko1221/Strata) (v0.2.2 / mecanismo 0.1.47). Além de rodar modelos Mixture-of-Experts de 125 bilhões de parâmetros (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) em um único PC distribuindo especialistas entre VRAM da GPU, RAM do sistema e SSD, este fork introduz uma pilha completa de **Spin(8) Triality e Cache KV TurboQuant** no mecanismo C++/CUDA, servidor Python, CLI e interface gráfica Desktop/Web:

### Os 4 Pilares Exclusivos deste Fork

1. **Biblioteca de Transformações Ortogonais Spin(8) Triality e $\mathrm{Cl}(8,0)$ ([`spin8/`](spin8/README.md))**
   - Construída sobre a base real dos octônios ($1, e_1, \dots, e_7$) e geradores simétricos $\mathrm{Cl}(8,0)$ ($\Gamma_0, \dots, \Gamma_7$).
   - Decompõe espinores 16×16 por quiralidade em três representações de 8 dimensões: **Vetor ($V$)**, **Semi-Spin Positivo ($S_+$)** e **Semi-Spin Negativo ($S_-$)**, satisfazendo a relação de entrelaçamento $U \Gamma(v) U^\top = \Gamma(Rv)$.
   - Cada plano de rotação passa por auditoria matemática antes da admissão: erro de ortogonalidade de Frobenius $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$, erro máximo de Gram $\le 10^{-12}$ e log-determinante com sinal via fatoração LU com pivoteamento ($\operatorname{sign}=+1, |\log|\det|| \le 10^{-12}$).
   - Inclui transformações de Sylvester Hadamard normalizadas para blocos potência de dois ($n = 1 \dots 1024$, incluindo máscaras Spin(8) 8D e blocos Bonsai 128D) e um monitor de auditoria persistente (`spin8_monitor`) a cada 1.024 tokens ou 60 segundos.

2. **Cache KV Triality de Três Visões e Dialetos CUDA Assíncronos TurboQuant ([`tqcodec/`](tqcodec/README.md))**
   - **Cache CUDA físico de três visões (`cache_cuda.cu`)**: Mantém três arrays de chaves (K) rotacionadas fisicamente independentes ($V, S_+, S_-$) e um array compartilhado de valores (V) quantizados por cabeça de atenção, avaliados via softmax online de passagem única com pesos de consenso no simplex $(\alpha_0, \alpha_1, \alpha_2)$ e correção residual gaussiana **QJL**.
   - **Dialetos CUDA assíncronos exatos**: `TQ4_1S` (4,25 bits/peso), `TQ3_0S` (3,3125 bits/peso) e `PQ2_0` (2,50 bits/peso).
   - **Otimização de memória compartilhada dinâmica para SM120 (RTX série 50)**: O kernel `audit_kernel` utiliza memória compartilhada dinâmica (`65.536` bytes) em vez de arrays locais `float f[128 * 128]` (64 KiB/thread), eliminando a reserva de pilha CUDA de **3,375 GiB (`3.623.878.656 B`)** durante `tqc_cache_cuda_initialize` (`audit_local=0`, `audit_delta=0`) e permitindo que todas as três visões (`off`, `f32`, `compressed`) rodem com estabilidade em uma GPU de 16 GiB / 32 GiB de RAM.

3. **Adaptador Query-v3 Versionado e Sidecars `.prismq3`**
   - Implementa uma carta tangente racional limitada sobre os 7 geradores antissimétricos derivados de blocos $\mathrm{Cl}(8,0)$ auditados, controlada por um adaptador de posto 8 sobre consultas normalizadas ($Q$) antes da codificação posicional (RoPE).
   - Suporta execução CUDA fundida sem alocação (`query_v3_cuda.h`) e arquivos sidecar `.prismq3` vinculados por SHA-256 (`--query-v3-sidecar`) para **Prism / TheTom (`qwen35-9b-thetom-q2kxl`)** e **Hikari / Bonsai (`bonsai-8b-prism-q1_0_g128`)**.

4. **Integração Completa na GUI, CLI e Plano de Controle**
   - **Interface Desktop e Web (`apps/host`)**: Configure **K cache type**, **V cache type** (`f16`, `tq3`, `tq3_spin8_hadamard`, `tq3_spin8_native`), **Spin(8) KV cache mode** (`off`, `f32`, `compressed`), **Spin(8) native config path** e **Spin(8) native config SHA-256** diretamente em **Settings → GPU & memory** com validação pré-inicialização em tempo real (`run-config-check.mjs`).
   - **CLI e Servidor Python (`strata_cli`, `strata_control`, `serve/server.py`)**: Suporte completo via `strata launch --set ...` e `strata serve` com verificação prévia da cápsula JSON e do hash SHA-256.

---

## Último Release do Fork: `v0.3.0-preview.20261024.2`

- **Página do Release**: [GitHub Release `v0.3.0-preview.20261024.2`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2)
- **Pacote Completo (Mecanismo + GUI + Controle)**: `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z`
  - **Tamanho**: `412.311.508` bytes
  - **SHA-256 do arquivo**: `7639fb8ffb3c8fd13857a59c6b5d9d8b392c8b82a496442f0486a9405fd16e21`
  - **SHA-256 do mecanismo (`strata.exe`)**: `564e23b5bcd2b0670d0a2d82e7cd2c20cd5afedf85ddca7c653bea11403727db`
- **Preview CLI anterior**: [`v0.3.0-preview.20261024.1`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.1) · [Notas técnicas](docs/releases/preview030.md) · [PoC Triality](research/triality_poc/README.md)

---

## Início Rápido (Recursos do Fork)

### 1. Pela Interface Gráfica (GUI)

1. Extraia `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z` (primeiro o `.7z` e depois o `.tar`) ou sobrescreva sua instalação local em `%LOCALAPPDATA%\Programs\Strata` e `%LOCALAPPDATA%\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13`.
2. Abra **Settings → GPU & memory**.
3. Configure os parâmetros de cache KV e Spin(8) (`cache_type_k`, `cache_type_v`, `spin8_mode`, `spin8_native_config`, `spin8_native_sha256`).

### 2. Pelo Terminal (`strata` CLI)

```powershell
# Inicialização padrão (compatível com upstream)
strata launch --model q2_0 --yes --no-tui

# Inicialização com cache KV TurboQuant de 3 bits e rotação de Hadamard
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_hadamard \
  --set cache_type_v=tq3_spin8_hadamard \
  --yes --no-tui

# Inicialização com cápsula nativa Spin(8) de três visões verificada por SHA-256
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_native \
  --set cache_type_v=tq3_spin8_native \
  --set spin8_mode=compressed \
  --set spin8_native_config=C:\caminho\para\capsule.json \
  --set spin8_native_sha256=<64-hex-sha256> \
  --yes --no-tui
```

---

## Requisitos de Hardware e Tamanhos de Modelo

**São necessários pelo menos 32 GB somando memória RAM do sistema e VRAM da placa de vídeo**. O Strata fornece endpoints compatíveis com OpenAI (`/v1/chat/completions`, `/v1/responses`) e Anthropic (`/v1/messages`) para Claude Code, Codex CLI e OpenCode.

| Memória combinada (RAM + VRAM) | Modelo recomendado | Observações |
| --- | --- | --- |
| **28–32 GB** | **[Gyro-S](docs/GYRO.md)** (27,6 GB) ou **[Coder](docs/MODELS.md#coder)** | Gyro-S para memória restrita; Coder mantém metade dos especialistas para código. |
| **35–40 GB** | **[Swift 1.5](docs/MODELS.md#swift-15)** IQ2_XS (39,2 GB) ou **Gyro-M** (35 GB) | Swift 1.5 pensa por menos tempo; Gyro-M aproxima-se do IQ3_XXS usando ~20 % menos VRAM. |
| **48 GB** | **IQ3_XXS** (47,0 GB) | Maior precisão que quantizações de 2 bits. |
| **64 GB** | **IQ3_S** (54,8 GB) ou **Q2_0** | IQ3_S iguala o modelo completo nos testes; Q2_0 entrega velocidade máxima (94 tok/s na RTX 5070). |
| **96 GB ou mais** | **UD-IQ4_XS** (72 GB) a **Q8_0** (136 GB), **[NVFP4](docs/NVFP4.md)** | Modelos de 4 a 8 bits quando todos os especialistas cabem na RAM. |

---

## Compilando e Testando a partir do Código-Fonte

```powershell
# Biblioteca de referência Spin(8) (CPU)
cmake -S spin8 -B build\spin8-cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF
cmake --build build\spin8-cpu --config Release
ctest --test-dir build\spin8-cpu -C Release --output-on-failure

# Testes de integração tqcodec (CPU + CUDA + Spin8)
cmake -S tqcodec -B build\tqcodec-cuda -G "Visual Studio 17 2022" -A x64 -DTQCODEC_ENABLE_CUDA=ON -DTQCODEC_SPIN8_TESTS=ON
cmake --build build\tqcodec-cuda --config Release
ctest --test-dir build\tqcodec-cuda -C Release --output-on-failure

# Mecanismo CUDA nativo (strata.exe / spin8_verify)
cmake -S . -B build\engine-cuda -G "Visual Studio 17 2022" -A x64 -DSTRATA_CUDA=ON
cmake --build build\engine-cuda --config Release --target strata spin8_verify

# Testes da interface Host GUI e controle
pnpm --dir apps/host typecheck
pnpm --dir apps/host build
node --test apps/host/tests/native-settings.test.mjs apps/host/tests/spin8-backend.test.mjs apps/host/tests/kv-settings.test.mjs apps/host/tests/kv-engine.test.mjs
py -3 -m pytest -p no:randomly tests/terminal/test_profiles.py
```

---

## Créditos e Licença

- **Engenharia do Fork (`zapabob/Strata`)**: Cache Triality Spin(8) $\mathrm{Cl}(8,0)$, dialetos CUDA `tqcodec`, adaptador Query-v3 `.prismq3`, otimização de memória compartilhada dinâmica SM120 `audit_kernel` e integração completa GUI/CLI.
- **Projeto Upstream ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))**: Mecanismo de streaming MoE em três níveis, cache de especialistas, decodificação especulativa, app Desktop e Terminal CLI.
- **Licença**: Distribuído sob a [Licença MIT](LICENSE). As bibliotecas redistribuíveis CUDA/cuBLAS e Microsoft Visual C++ incluídas nos pacotes mantêm os termos de seus respectivos fabricantes.
