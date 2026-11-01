# Hakua / Strata

Chatbot Hakua baseado no Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · passos de instalação em 30 segundos

Baixe e execute o instalador Windows deste fork. Na primeira abertura, instale o motor compatível oferecido e depois escolha e carregue um modelo. Hakua memory na barra lateral abre o chat com memória. Os passos levam cerca de 30 segundos; downloads, instalação e carregamento exigem tempo adicional.

Prévia para Windows 0.4.0: veja os testes realizados e os limites no [registro de validação](docs/HAKUA_RELEASE.md).

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt)

O arquivo 7z contém o mesmo instalador. Extraia-o e execute o EXE de instalação.

## Recursos deste fork

Hakua só lê lembranças e salva um resumo com seu consentimento para aquela solicitação. As duas opções são independentes e redefinidas depois. Ao carregar um modelo nativo compatível, o aplicativo cria automaticamente um perfil de memória local. Abra Hakua memory, copie a chave do perfil na caixa de diálogo e marque uma opção de memória na página local e depois cole a chave em About → Settings. O [guia de memória](serve/MEMORY_HARNESS.md) também explica a configuração de um servidor a partir do código-fonte.

PrismML/PQ2_0 e TurboQuant também podem usar Hakua-memory. Carregue o modelo e abra Hakua memory na barra lateral. O novo diálogo usa sua chave local automaticamente; leitura e gravação são escolhidas separadamente a cada solicitação. Conclua as solicitações ativas antes da primeira abertura: o servidor gerenciado pelo aplicativo reinicia com autenticação e sem caches compartilhados. Os três caminhos usam o mesmo perfil local. Na inicialização, as versões da GUI, do Host e do aplicativo são comparadas; arquivos incompatíveis ou que não carregam exibem instruções de recuperação.

As ferramentas Hermes sincronizam SOUL.md / MEMORY.md aprovados e oferecem memória Ebbinghaus, grafo semântico, exportação Obsidian e consolidação sleep. São separadas do chat; dependências opcionais de RAG e embeddings não vêm no instalador básico.

Para um GGUF local PQ2_0, escolha `PrismML` como backend llama-server nas configurações avançadas do modelo. Para um GGUF padrão com TurboQuant, escolha `TurboQuant` e configure K como `FP16` e V como `TURBO2`, `TURBO3` ou `TURBO4`. Os formatos TurboQuant para K estão desativados nesta versão porque os testes reais produziram respostas corrompidas. Recarregue o modelo após trocar o backend. Cada backend usa seus próprios executáveis e bibliotecas no componente de motor separado; PQ2_0 e TurboQuant seguem caminhos distintos. Consulte [a configuração e os limites](docs/LOCAL_LLAMA_BACKENDS.md).

Os experimentos Spin(8)/Triality, Query-v3 e Bonsai exigem configurações compatíveis e explícitas, sem promessa geral de ganho de velocidade ou qualidade.

Como no aplicativo oficial, o instalador inclui Node e Python privados e Hakua-memory 0.3.5. Os motores GPU são distribuídos separadamente: após sua escolha, o aplicativo baixa um componente Hakua assinado ou importa um arquivo já baixado. Esse componente contém os ambientes CUDA nativo, PrismML e TurboQuant. Os pesos dos modelos são outro download separado. O aplicativo publicado não exige Node ou Python do sistema, pip ou compilador.

## Compatibilidade e atualizações

Este pacote Windows atende NVIDIA RTX série 50, CUDA sm_120. Outras GPUs, Linux e macOS exigem pacotes próprios. O instalador original não contém estas alterações. Os pesos são separados e podem ocupar dezenas ou centenas de GB. Prefira pacotes compatíveis ISTA-DASLab, depois Unsloth e Gyro.

O motor nativo distribuído separadamente atende ao chat de texto. Esta prévia não inclui a entrada nativa de imagens nem o motor nativo separado do DeepSeek.

Mantenha modelos e lembranças fora da pasta do programa. Lembranças pessoais, chaves e pesos não são distribuídos. Feche o aplicativo antes de atualizar. Para voltar, preserve o backup e instale uma versão anterior deste fork.

Com a opção de recolher à bandeja ativada, × oculta a janela. Antes de atualizar, clique com o botão direito no ícone do Strata na bandeja e escolha Sair do Strata para encerrar o aplicativo por completo.

[Models](docs/MODELS.md) · [Install](docs/HAKUA_INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Versões e verificação

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `c62d5e3a` · 0.2.9 |

<!-- App version in this preview tree: `0.4.0-preview.20261101.1` -->

O instalador não tem assinatura de código Windows. Confira SHA256SUMS.txt antes de instalar. O componente de motor separado e seu feed de atualização são assinados e verificados pelo aplicativo. O aplicativo é atualizado manualmente pelo instalador; suas atualizações automáticas assinadas ainda não foram verificadas. O [relatório de validação](docs/HAKUA_RELEASE.md) registra resultados e limites, incluindo testes de memória com modelos reais.

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
