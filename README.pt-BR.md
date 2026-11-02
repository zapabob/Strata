# Hakua / Strata

Chatbot Hakua no Strata. Este fork oferece uma prévia Windows com Hakua memory e runtimes GPU separados. [zapabob/Strata](https://github.com/zapabob/Strata) · upstream [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Instalação (prévia Windows)

1. Baixe o [EXE de instalação](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) (ou o [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) com o mesmo EXE).
2. Compare com [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt) antes de executar. Não há assinatura de código Windows. Os digests desta tag foram atualizados em 2026-11-02; não use um SUMS antigo.
3. Encerre o Strata por completo (bandeja → Sair do Strata) se já estiver instalado e execute o EXE.
4. Na primeira inicialização, instale o mecanismo assinado oferecido ou importe o `.tar.gz` correspondente da mesma release. Depois escolha uma pasta de modelos e carregue um modelo.

A sequência de cliques é curta. Downloads, ativação do mecanismo e carga do modelo demoram mais e precisam de disco e VRAM. Detalhes: [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md). Limites medidos: [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## O que o instalador traz

| No instalador do app | Separado |
| --- | --- |
| GUI / Host, Node privado 24.22.2, Control / CPython 3.12.15, Hakua-memory 0.3.5, Harness | Componente CUDA assinado (~1,4 GB): Strata nativo + PrismML + TurboQuant |
| Atualizações manuais com este EXE | Pesos do modelo (dezenas ou centenas de GB) |

Não é preciso Node, Python, pip ou compilador do sistema para o app publicado. O instalador upstream Niko1221 não inclui as mudanças deste fork.

## Carregar um modelo local

- **Pacotes Strata nativos** (pacotes de texto Qwen suportados): caminho nativo prepare / load do app.
- **Hikari / PQ2_0 GGUF**: use **Load with Strata** (PrismML). Não use prepare nativo para PQ2_0.
- **GGUF comum + cache TurboQuant**: backend `TurboQuant`, K=`FP16`, V=`TURBO2` / `TURBO3` / `TURBO4`, depois recarregue. Modos K do TurboQuant permanecem desligados após respostas corrompidas em teste real.

PrismML e TurboQuant são executáveis distintos no componente do mecanismo. Detalhes: [LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md). Prefira pacotes que caibam: ISTA-DASLab → Unsloth → Gyro.

Quando um modelo serve pelo caminho Strata / supervisor, o Agent pode usar essa instância local para ferramentas que o modelo suporte (por exemplo busca na web). Uma sessão só nativa não expõe o mesmo caminho.

## Hakua memory

Depois de carregar um modelo suportado, abra **Hakua memory** na barra lateral. Consentimentos de leitura e gravação são separados e reiniciam a cada turno.

- Nativo: cole a chave do diálogo em About → Settings e marque memória na página local.
- PrismML / TurboQuant: o app fornece a chave local; termine pedidos ativos antes da primeira abertura.

Guia: [MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md). Ferramentas Hermes SOUL/MEMORY são separadas do chat e não são necessárias para o uso básico.

## Versões

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine / Control | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Congelamento upstream | `c62d5e3a` · 0.2.9 |

Página da release: [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1). O mecanismo e o feed têm assinatura Ed25519 e o app as verifica. Atualizações automáticas assinadas do app não estão qualificadas; atualize com este instalador.

## Limites (prévia medida)

Windows x64, NVIDIA RTX 50 / CUDA sm_120, verificado em RTX 5060 Ti. Inclui texto nativo. Não inclui entrada de imagem nativa nem o mecanismo DeepSeek nativo separado. Outras GPUs e SOs precisam de pacotes próprios. Mantenha modelos e memória pessoal fora da pasta do app. A release não inclui memórias pessoais, chaves nem packs completos de pesos.

Spin(8) / Triality / Query-v3 / Bonsai continuam experimentos opcionais. Sem promessa geral de velocidade ou qualidade.

## Desenvolvimento

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Models](docs/MODELS.md) · [Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Fork Strata sob MIT. Hakua-memory e pesos têm licenças próprias. Créditos aos autores e ao upstream. O vetor de controle opcional (~480 KB) permanece desligado por padrão sob [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
