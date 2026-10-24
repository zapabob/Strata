<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <b>Português</b></p>

<h3 align="center">Strata — Cache KV Spin(8) Triality, DeepSeek-V4.1 Sem Censura, Carregador GGUF e Memória de Longo Prazo</h3>

<p align="center">
  <b>Fork de engenharia de <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Upstream Integrado · Atenção Spin(8) $\mathrm{Cl}(8,0)$ Triality · DeepSeek-V4.1-Flash MLA Sem Censura · Carregamento Seguro GGUF · Memória de Longo Prazo Hermes e Hakua · Otimizado para 32 GB RAM
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Visão Geral deste Fork (`zapabob/Strata`)

**`zapabob/Strata`** é um fork avançado de engenharia sincronizado com a versão mais recente v0.2.4.2 / motor 0.1.49.2 de [Strata](https://github.com/Niko1221/Strata). Além de executar modelos MoE de 125B parâmetros (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) em um único PC através de streaming coordenado entre VRAM da GPU, RAM do sistema e SSD, este fork integra **Cache KV Spin(8) Triality**, **derivados sem censura DeepSeek-V4.1**, **carregamento seguro de modelos GGUF endereçados por conteúdo** e **memória de longo prazo para agentes**:

1. **Biblioteca de Transformação Ortogonal Spin(8) Triality e $\mathrm{Cl}(8,0)$ ([`spin8/`](spin8/README.md))**
   - Baseada em octônios reais ($1, e_1, \dots, e_7$) e geradores simétricos de Clifford $\mathrm{Cl}(8,0)$.
   - Decompõe espinores 16×16 por quiralidade em três representações octodimensionais: **Vetor ($V$)**, **Semiespim Positivo ($S_+$)** e **Semiespim Negativo ($S_-$)**.
   - Auditoria matemática rigorosa antes da admissão de qualquer rotação ($E_F \le 10^{-12}$).
   - Transformadas de Sylvester-Hadamard normalizadas e monitor de invariantes em tempo de execução (`spin8_monitor`).

2. **Cache KV Triality de Três Visões e Dialetos TurboQuant CUDA ([`tqcodec/`](tqcodec/README.md))**
   - **Cache CUDA de Três Visões (`cache_cuda.cu`)**: Matrizes de chaves rotacionadas ($V, S_+, S_-$), valores quantizados compartilhados, softmax online e correção residual **QJL**.
   - **Dialetos assíncronos**: `TQ4_1S` (4.25 bpw), `TQ3_0S` (3.3125 bpw) e `PQ2_0` (2.50 bpw).
   - **Otimização SM120 (Série RTX 50)**: Memória compartilhada dinâmica que elimina 3.375 GiB de reserva de pilha de VRAM no CUDA.

3. **Derivados Sem Censura DeepSeek-V4.1-Flash-1017 e Backend MLA ([`strata_control/backends/dsv41.py`](strata_control/backends/dsv41.py))**
   - Suporte nativo a matrizes de projeção Multi-Head Latent Attention (MLA) através do backend dedicado `strata-dsv41`.
   - Modelos pré-qualificados: Linha de base ISTA, receita de substituição abliterada Kiwimaker Maya-S e pacote independente AtomicChat.
   - Supressão automática de vetores de recusa em modelos abliterados para evitar distorção de respostas.

4. **Resolvedor ModelBundle Endereçado por Conteúdo e Roteador Local ([`strata_control/model_bundle.py`](strata_control/model_bundle.py))**
   - Análise delimitada de cabeçalho ($\le 16$ MiB) com proteção contra transbordamento ($\operatorname{rank} \le 4, \operatorname{dim} \le 2^{30}$, mitigando GHSA-vgg9-87g3-85w8).
   - Digest SHA-256 em fluxo contínuo e detecção de adulteração de arquivos.
   - Roteamento local determinístico (`strata-dsv41`, `strata-native`, `prism`, `llama-cpp`) com **proibição estrita de fallback para a nuvem** (100% privacidade offline).

5. **Memória de Longo Prazo Hermes Agent e Hakua ([`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py))**
   - Servidor MCP stdio padrão + CLI:
     - `SOUL.md`: Personalidade e diretiva de afinidade Hakua com backup automático com carimbo de data/hora.
     - `MEMORY.md`: Memória episódica estruturada no formato `§ [category] YYYY-MM-DD: Title`.
     - Banco SQLite do Hermes Agent (`~/.hermes/ebbinghaus_memory.db`, ~5.000 memórias indexadas).
     - Hakua Composite Memory (`~/.hakua-memory`).
   - Injeção automática em turnos de conversa via `apps/host/server/memory.mjs`.

6. **Orçamento de Hardware 32GB RAM / 16GB VRAM e Ciclo de Vida Drafter Zero-VRAM**
   - Verificado no Windows 11 com 32 GB RAM e RTX 5060 Ti 16 GB (`sm_120`).
   - Respeito estrito aos limites: RAM de host $\le 24.0$ GiB, reserva de SO $\ge 4.0$ GiB, orçamento VRAM $\le 14.0$ GiB.
   - Descarregamento automático do modelo rascunho sob pressão de memória sem interromper o processo principal.

---

## Verificação e Integração Upstream: `v0.3.0` Upstream Integrated Edition

- **Upstream SHA**: `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`
- **Correção de segurança GUI**: `c487c875d05075113965bc61d822b27179f70639`
- **Contratos do Fork (F01–F11)**: Preservados integralmente.
- **Testes**: **71/71 testes Python aprovados**, **13/13 testes Node.js aprovados**.

---

## Licença

Distribuído sob a [Licença MIT](LICENSE).
