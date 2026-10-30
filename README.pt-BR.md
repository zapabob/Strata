# Hakua / Strata

Chatbot Hakua baseado no Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · passos de instalação em 30 segundos

Baixe e execute o instalador Windows deste fork, escolha um modelo compatível e carregue-o. Hakua memory na barra lateral abre o chat com memória. Os passos levam cerca de 30 segundos; download, instalação e carregamento exigem tempo adicional.

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Strata_0.3.3-preview.20261030.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/SHA256SUMS.txt)

O arquivo 7z contém o mesmo instalador. Extraia-o e execute o EXE de instalação.

## Recursos deste fork

Hakua só lê lembranças e salva um resumo com seu consentimento para aquela solicitação. As duas opções são independentes e redefinidas depois. Ao carregar um modelo nativo compatível, o aplicativo cria automaticamente um perfil de memória local. Abra Hakua memory, copie a chave do perfil na caixa de diálogo e marque uma opção de memória na página local e depois cole a chave em About → Settings. O [guia de memória](serve/MEMORY_HARNESS.md) também explica a configuração de um servidor a partir do código-fonte.

As ferramentas Hermes sincronizam SOUL.md / MEMORY.md aprovados e oferecem memória Ebbinghaus, grafo semântico, exportação Obsidian e consolidação sleep. São separadas do chat; dependências opcionais de RAG e embeddings não vêm no instalador básico.

Para um GGUF local PQ2_0, escolha `PrismML` como backend llama-server nas configurações avançadas do modelo. Para um GGUF padrão com TurboQuant, escolha `TurboQuant` e configure K como `FP16` e V como `TURBO2`, `TURBO3` ou `TURBO4`. Os formatos TurboQuant para K estão desativados nesta versão porque os testes reais produziram respostas corrompidas. Recarregue o modelo após trocar o backend. Cada backend usa seus próprios executáveis e bibliotecas incluídos; PQ2_0 e TurboQuant seguem caminhos distintos. Consulte [a configuração e os limites](docs/LOCAL_LLAMA_BACKENDS.md).

Os experimentos Spin(8)/Triality, Query-v3 e Bonsai exigem configurações compatíveis e explícitas, sem promessa geral de ganho de velocidade ou qualidade.

Inclui Node e Python privados, Hakua-memory 0.3.5 e um motor CUDA compilado deste fork. Iniciar um modelo não instala pacotes Python nem compila código.

## Compatibilidade e atualizações

Este pacote Windows atende NVIDIA RTX série 50, CUDA sm_120. Outras GPUs, Linux e macOS exigem pacotes próprios. O instalador original não contém estas alterações. Os pesos são separados e podem ocupar dezenas ou centenas de GB. Prefira pacotes compatíveis ISTA-DASLab, depois Unsloth e Gyro.

Mantenha modelos e lembranças fora da pasta do programa. Lembranças pessoais, chaves e pesos não são distribuídos. Feche o aplicativo antes de atualizar. Para voltar, preserve o backup e instale uma versão anterior deste fork.

[Models](docs/MODELS.md) · [Install](docs/INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Versões e verificação

| | |
| --- | --- |
| GUI / Product | `0.3.3-preview.20261030.1` |
| Engine | `0.3.3` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `870aedd9` · 0.2.8 |

<!-- App version in this preview tree: `0.3.3-preview.20261030.1` -->

Esta prévia não é assinada. Confira SHA256SUMS.txt antes de instalar. O [relatório de validação](docs/HAKUA_RELEASE.md) indica resultados reais e limitações. Compilar não comprova inferência correta. Esta prévia sem assinatura usa atualização manual pelo instalador; atualizações automáticas assinadas ainda não foram verificadas.

## Desenvolvimento e suporte

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Fork do Strata sob licença MIT. Hakua-memory e pesos têm licenças próprias. A autoria e os créditos originais são preservados.

O vetor de controle opcional do upstream (480 KB) fica desativado por padrão e segue a [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE). Os pesos completos do modelo são baixados separadamente.
