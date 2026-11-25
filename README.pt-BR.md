# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

**IA local projetada para utilizar todos os recursos do seu PC com Windows — GPU, núcleos físicos + threads SMT da CPU, RAM do sistema e armazenamento NVMe/SSD.** Hakua é o fork independente `zapabob/Strata` de [Niko1221/Strata](https://github.com/Niko1221/Strata), acompanhando o upstream oficial **v0.2.21** (`d46f5f268`, engine/Control `0.1.67`) enquanto mantém todos os motores exclusivos do fork, fluxos de memória/agentes e otimizações Blackwell CUDA 13.5.

## Novidades na 0.8.1 (Engine 0.7.0)

- **Inferência heterogênea de máquina completa nas 4 camadas de hardware (GPU + CPU 6P/6SMT + RAM + SSD)**:
  - **Backend nativo Windows `aux_cpus` CPU Sets + divisão SMT para E/S** (`engine/include/strata/platform/aux_cpus.hpp`, `ssd_stream_scheduler.hpp`, `direct_file.cpp`): fixa o loop host da GPU e o cálculo AVX2 MoE estritamente nos núcleos físicos primários, dedicando todas as threads SMT secundárias (`io_smt=[1,3,5,7,9,11]` em CPU 6C/12T) a Direct I/O sobreposto de 6 threads e streaming assíncrono `PrefetchVirtualMemory`.
  - **5 motores nativos recém-compilados com CUDA 13.5 / SM120 Blackwell** (`strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`) com doorbells mapeados zero-copy Gen-K/L, proteção VRAM WDDM de 1536 MiB, orçamentos de RAM Windows seguros quanto a commit (`hy4_cpu_experts.cpp`, `inkling2_engine.cu`), afinidade em núcleos físicos no Windows + espera `_mm_pause` (`ink_hybrid.cuh`), e staging de embeddings em RAM fixada + `PrefetchVirtualMemory` em lote no SM120 Q38 (`engine/q38/src/engine.cu`).
  - **Lançador unificado de máquina completa e presets**: `tools/full_machine_infer.py` (`--list-models`, `--plan`, `--bench`, `--serve`) detecta automaticamente GPU, topologia física/SMT de CPU, folga de RAM/commit e SSDs para gerar planos de execução em 3 camadas e arquivos de configuração prontos em `configs/`.
- **Merge 3-way com o upstream oficial v0.2.21**: integra MoE unificado de 4 camadas GPU+RAM+CPU+SSD, `--layer-split` multi-GPU, atualizações de GUI/host e correções de Control/engine `0.1.67` junto com todos os recursos do fork (`/btw`, `/deepresearch`, RustXNG Full, habilidades de fluxo de trabalho, runner denso Q38, extensão DeepSeek, provedor Hermes `inkling2` e tabelas de perfis MIT Inkling-2 do kuraneko1).

## Benchmarks medidos em hardware real

Medido em **NVIDIA GeForce RTX 5060 Ti 16 GB (SM120, CUDA 13.5) · AMD Ryzen 5 4500 (6C/12T) · 32 GB DDR4 · Dual SSD (`C:` Crucial P3 NVMe + `H:` S5-1TB SSD)** com prompts de 16 tokens e decodificação greedy de 32 tokens:

| Modelo (Tamanho) | Engine e contexto | Camadas ativas | Prefill (`pp`) | Decode (`tg`) | Paridade |
|---|---|---|---:|---:|---|
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | GPU 10.85 GiB (2232 exps) + RAM fixada 4.34 GiB (840 exps) + 6P/6SMT | **85.08 t/s** | **42.22–42.33 t/s** | **32/32 exato** |
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | Spill 3 camadas: GPU 10.85 GiB + RAM 3.60 GiB + **SSD mmap 0.74 GiB (`prefetch=on`)** + 6P/6SMT | 64.80 t/s | 14.24 t/s | **32/32 exato** |
| **Inkling-2-Mini UD Q4_K_M** (15.47 GiB) | `strata-inkling2.exe` · 16K (Q8 KV) | GPU 10.42 GiB (2339 exps) + RAM fixada 3.34 GiB (733 exps) + 6P/6SMT | **109.64 t/s** | **53.28 t/s** | Greedy limpo |
| **Qwen3.8-27B 3.69bpw MTP** (11.73 GiB) | `strata-q38.exe` · 4K (F16 KV) | Pesos GPU SM120 (10.44 GiB) + staging emb em RAM fixada + `PrefetchVirtualMemory` | 6.21 s a frio | **29.95 t/s** | Greedy limpo |

*Nota de threads de CPU (A/B no Ryzen 5 4500)*: manter os workers de cálculo nos 6 núcleos físicos (`host=0`, `workers=2,4,6,8,10`) com as threads SMT (`1,3,5,7,9,11`) reservadas para E/S alcançou **42.22–42.33 t/s**, contra **29.68 t/s** (-21.9%) ao sobrescrever 11 workers de cálculo em threads irmãs SMT.

## Versão e downloads

Versão atual: **0.8.1** — GitHub Latest: [página da release v0.8.1](https://github.com/zapabob/Strata/releases/tag/v0.8.1).

- **Instalador Desktop**: `Strata-0.8.1-windows-x64-setup.exe` (app Tauri/NSIS por usuário com Node 24.22.3, Python, Control 0.6.3 e RustXNG Full embutidos).
- **Pacote do Instalador**: `Strata-0.8.1-windows-x64.tar.7z` (instalador + `SHA256SUMS.txt`).
- **Componente de Engine CUDA 13.5 SM120 (opcional)**: `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` (todos os cinco motores SM120 recompilados: `strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`).
- **Componente Hy4-Flash (opcional)**: `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`.

Baixe sempre diretamente da lista **Assets** da release e verifique os digests SHA-256. A verificação de assinatura ed25519 dos componentes foi removida (sem chave de assinatura); assinatura Windows Authenticode ausente; **`releaseQualified=false`**.

![Hakua / Strata chat em japonês real com Qwen3.8-27B](docs/media/native-qwen38-japanese-chat.png)
*Desktop Hakua / Strata executando `qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf` via `strata-q38.exe` (CUDA 13.5 / RTX 5060 Ti 16 GB).*

## Início rápido (CLI de máquina completa e Desktop)

### Instalação desktop ou atualização por sobrescrita

1. Conclua solicitações ativas, descarregue os modelos, faça backup dos dados do aplicativo e encerre o Strata (incluindo o ícone na bandeja do sistema).
2. Execute `Strata-0.8.1-windows-x64-setup.exe` no diretório de instalação existente para atualizar preservando modelos, chats, memória, ferramentas, chaves de API e aprovações.
3. Importe `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` em *I already have the file*, selecione um modelo compatível ou GGUF local e clique em **Load**. Veja [instalação e reversão](docs/HAKUA_INSTALL.md).

### Lançador de máquina completa (`tools/full_machine_infer.py`)

```powershell
# Inspecionar camadas GPU/CPU/RAM/SSD e descobrir modelos locais
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --list-models

# Executar benchmark Sakura Inkling-2-Mini 131K com ajustes de máquina completa
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --bench --model Sakura --max-new 32

# Iniciar servidor API local OpenAI/Anthropic (127.0.0.1:8092) com RAM squeeze
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model Sakura --port 8092 --squeeze
```

## GGUF recomendado e recursos do fork

- **Chat local Qwen3.8-27B em 16 GB de VRAM**: testado com [o GGUF de quantização mista 3.69 bpw de soyaakinohara](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf) (créditos para **soyaakinohara** e **AEON-7**). Comece com contexto de 4.096 tokens; o rótulo `12GB` no nome do arquivo não garante encaixe em uma placa de 12 GB.
- **Runner denso próprio Q38 (`strata-q38.exe`)**: polimorfismo de quantização mista por tensor em 11 formatos (`F32`, `F16`, `BF16`, `Q8_0`, `Q4_K`, `Q5_K`, `Q6_K`, `IQ3_S`, `IQ2_S`, `IQ4_XS`, `PQ2_0`), prefill em Tensor Cores, modos KV Spin(8) / TurboQuant (`auto`: `f16` → `f16_turbo4` → `spin8_k8v4`), draft/verify MTP `K=3` e perfil ortográfico japonês opcional. Veja [QWEN38_DENSE_NATIVE.md](docs/QWEN38_DENSE_NATIVE.md).
- **Ferramentas de agentes e fluxos de trabalho**: subagente lateral `/btw` sem ferramentas com parada independente, `/research` e `/deepresearch` com RustXNG Full embutido (consulta provedores externos quando habilitado), aprendizado/aplicação privada opcional de skills de fluxo, CRUD de arquivos no workspace/barra lateral e memória de chat com escopo. Veja [WORKFLOW_SKILLS.md](docs/WORKFLOW_SKILLS.md) e [BROWSER_SEARCH.md](docs/BROWSER_SEARCH.md).

## Pisos de segurança e limites

Mantidos sem alteração: **3 GiB de RAM disponível**, **4 GiB de folga de commit**, **>= 768 MiB de reserva GPU** (`1536 MiB` WDDM padrão para Inkling-2 `<= 17 GiB`), **5 GiB livres em `C:`** e **10 GiB livres em `H:`**. Qualidade geral de modelos, geração de janela completa e concorrência multi-cliente simultânea na GPU permanecem não qualificadas (**`releaseQualified=false`**). Esta release Windows do fork não inclui entrada nativa de imagens nem inferência qualificada em Linux/macOS. Registros históricos preservam suas versões originais em [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Documentação e desenvolvimento

[Instalação](docs/HAKUA_INSTALL.md) · [Evidências da release](docs/HAKUA_RELEASE.md) · [API e hardware](docs/AI_REFERENCE.md) · [Terminal](docs/TERMINAL.md) · [Compilação do código-fonte](docs/SOURCE_INSTALL.md) · [Empacotamento](tools/packaging/README.md) · [Contribuir](.github/CONTRIBUTING.md) · [Segurança](.github/SECURITY.md) · [Licença](LICENSE)

```powershell
pytest tests/test_full_machine_infer.py
python -m pytest terminal/tests/terminal
```

```powershell
cd app/host
pnpm test
pnpm run build
```

[Niko1221/Strata](https://github.com/Niko1221/Strata) · [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [Avisos de terceiros](third_party/)

## Agradecimentos

Sinceros agradecimentos a **Niko1221/Strata**, **kuraneko1 (`_ryu15_`)**, **ggml & llama.cpp**, **NousResearch (Hermes Agent)**, **Qwen Team (Alibaba Cloud)**, **NVIDIA**, **RustXNG**, **libstrix**, **Node.js / Python / Tauri**, **Microsoft**, **ISTA-DASLab**, **PrismML**, **TurboQuant**, **Spin(8)**, **soyaakinohara** e **AEON-7** pelas bases de código aberto, pesos e pesquisas que tornam o Hakua / Strata possível.
