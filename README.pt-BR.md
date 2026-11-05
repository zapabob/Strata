# Strata · Hakua

Modelos locais, chat, ferramentas e memória Hakua opcional. Este é o [fork de zapabob](https://github.com/zapabob/Strata) de [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Versão para Windows

Esta versão se destina ao Windows x64 CUDA sm_120. As verificações locais usaram uma RTX 5060 Ti com 16 GB de VRAM e 32 GB de RAM. Leia os [resultados e limites restantes](docs/HAKUA_RELEASE.md) antes de instalar.

**0.4.1** exige atualização manual e não tem assinatura de código do Windows. [Versão](https://github.com/zapabob/Strata/releases/tag/v0.4.1) · [Instalação](docs/HAKUA_INSTALL.md) · [Testes e limites](docs/HAKUA_RELEASE.md).

1. Baixe o [instalador](https://github.com/zapabob/Strata/releases/download/v0.4.1/Strata-0.4.1-windows-x64-setup.exe) e compare seu hash com [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.1/SHA256SUMS.txt).
2. Feche o Strata, inclusive o ícone na bandeja, e execute o instalador. Mantenha modelos e dados pessoais fora da pasta do aplicativo.
3. Instale o componente CUDA assinado na tela de preparação pelo canal latest ou pelo arquivo incluído `strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz`.
4. Escolha um modelo adequado ou **Use a local GGUF** para arquivos existentes. Node e Python já estão incluídos; não é necessário um interpretador do sistema nem um compilador.

As versões seguem [SemVer 2.0.0](https://semver.org/): aplicativo `0.4.1`, mecanismo nativo `0.4.1`; Control `0.4.2`; os ambientes PrismML/TurboQuant sem alterações permanecem em `0.4.0`. O local habitual do aplicativo é `%LOCALAPPDATA%\Programs\Strata` em C:, separado dos modelos. Uma instalação existente pode manter outro local.

O [pacote tar.7z](https://github.com/zapabob/Strata/releases/download/v0.4.1/Strata-0.4.1-windows-x64.tar.7z) inclui o mesmo instalador NSIS, o componente CUDA assinado, Control, as somas de verificação e as instruções. Modelos e dados pessoais não estão incluídos. A publicação usa `v0.4.1`, o alias de tag `latest` e GitHub Latest.

## Reutilizar modelos existentes

Para um GGUF dividido, selecione uma parte: o Strata verifica o conjunto completo. Os pesos importados permanecem no local original. Metadados genéricos, como `Hf`, são exibidos usando o nome do arquivo. Nomes personalizados são preservados após nova verificação e reinicialização.

As configurações de um modelo local registrado podem ser abertas enquanto as outras listas de modelos ainda estão carregando.

Antes de preparar um modelo do catálogo, o Strata faz uma busca limitada por conjuntos locais compatíveis na pasta escolhida e nas subpastas. Uma correspondência válida única é reutilizada; várias exigem selecionar o arquivo. Downloads convencionais mantêm a verificação de integridade e a retomada. O mecanismo e as camadas opcionais de rascunho são tratados separadamente.

Modelos nativos Qwen/Swift podem precisar de uma conversão inicial para pack. O progresso mostra camadas concluídas quando o conversor fornece essa informação. A retomada de um pack de baixo consumo de memória considera o espaço já alocado ao arquivo temporário. GGUFs Hikari/PQ2_0 compatíveis usam PrismML por **Load with Strata**, sem conversão nativa Q2_0. Para GGUFs comuns compatíveis, o TurboQuant oferece K=`FP16` e V=`TURBO2/3/4`; recarregue após a escolha. Consulte os [mecanismos locais](docs/LOCAL_LLAMA_BACKENDS.md).

## Cache privado e memória

O novo caminho Qwen3.6 mantém o cache na mesma conversa autenticada. Outra conversa ou outro usuário não o reutiliza. Troca de conversa, cancelamento, erro ou cinco minutos de inatividade apagam o cache privado. Requisições sem identificador de conversa não reutilizam cache.

As duas condições de recusa do Host antes da inicialização foram removidas. O servidor verifica a capacidade de cache privado na resposta INFO do mecanismo em execução, incluindo compilações locais compatíveis. Inicialmente, uma requisição é processada por vez e os caches compartilhados permanecem desativados. O mapped expert pack continua opcional. Medições e verificações pendentes estão no [registro da versão](docs/HAKUA_RELEASE.md).

Abra **Hakua memory** na barra lateral. Ler e salvar dependem de consentimentos separados em cada turno. PrismML/TurboQuant reinicia seu servidor com autenticação e caches privados; conclua as requisições ativas antes. [Guia](serve/MEMORY_HARNESS.md).

## Componentes e limites

Aplicativo/Host: `0.4.1`; mecanismo nativo: `0.4.1`; Control `0.4.2`; Node: `24.22.2`; CPython: `3.12.15`; Hakua-memory: `0.3.5`. Referência upstream: `ffa80d73` / `0.2.10`.

Mecanismo nativo: `0.4.1`; Control: `0.4.2`. O canal estável assinado fornece o componente CUDA que passou no teste instalado do Qwen3.6 com um token e capacidade de contexto de 4096. A configuração salva de 131072 foi preservada; a geração nativa com toda a janela ainda não está validada. A atualização do aplicativo é manual. Consulte as [verificações](docs/HAKUA_RELEASE.md).

Os testes Windows x64 abrangem RTX 5060 Ti, CUDA sm_120 e 32 GB de RAM. Não qualificam outros GPUs ou sistemas, entrada nativa de imagens ou um mecanismo nativo DeepSeek separado. A alocação legada do Qwen3.6 na RAM pode exigir cerca de 18,7 GiB mais reserva; 32 GB não garantem a inicialização. Uma resposta curta com contexto de 131.072 tokens não valida toda a janela nem sua qualidade. Os modos K do TurboQuant continuam desativados após falhas nos testes de qualidade. Spin(8), Triality, Query-v3 e Bonsai são experimentos opcionais. Desempenho e recursos necessários dependem do modelo e do computador.

## 96K–128K com 16 GB de VRAM

O editor oferece 96K (98.304) e 128K (131.072). No PC testado, com RTX 5060 Ti de 16 GB e 32 GB de RAM, o Qwen3.6 UD-Q4_K_XL com PrismML, cache K/V Q8 e 28 camadas MoE na CPU processou 130.792 tokens sem cortes e recuperou os três códigos distantes. Essa solicitação levou cerca de 29 minutos; ela não garante qualidade geral nem velocidade para outros modelos. Consulte as [configurações e os resultados com contexto completo](docs/WINDOWS_16GB_CONTEXT.md).

## Desenvolvimento

[Modelos](docs/AI_REFERENCE.md) · [Compilação](packaging/README.md) · [Contribuir](CONTRIBUTING.md) · [Segurança](SECURITY.md)

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

O Strata usa a licença MIT. Pesos, Hakua-memory e dependências mantêm suas próprias licenças e avisos. O pequeno vetor de controle opcional fica desativado por padrão e usa a [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
