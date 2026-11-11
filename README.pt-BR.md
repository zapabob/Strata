# Strata · Hakua

<!-- skills-057 -->
## Nova prévia 0.5.7-local.1

`/btw` delega a um subagente real sem ferramentas, sob uma sessão pai separada. A conversa principal e sua interrupção permanecem independentes. Em Habilidades, ative separadamente o aprendizado de SKILL.md a partir do trabalho concluído e a aplicação automática de instruções correspondentes. Edições manuais, escopo do espaço de trabalho e aprovações são respeitados.

[Instalador](https://github.com/zapabob/Strata/releases/download/v0.5.7-local.1/Strata-0.5.7-local.1-windows-x64-setup.exe) · [Pacote tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.7-local.1/Strata-0.5.7-local.1-windows-x64.tar.7z) · [Instalação e uso](docs/WORKFLOW_SKILLS.md)

RustXNG 0.31.1 Full / native 0.5.5 / Control 0.5.6. [0.5.7 delivery status](_docs/2026-11-11_workflow-skill-learning_Codex.md). Stable / GitHub Latest: 0.5.1.


## Prévia atual 0.5.6-local.1

`/btw <pergunta>` abre uma resposta separada enquanto o chat principal continua. `/deepresearch <tema>` reúne várias buscas e leituras de páginas, indicando quando as evidências são insuficientes. Em Configurações → Ferramentas → Busca na web, escolha **RustXNG Full**, sem chave.

[Instalador para Windows](https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/Strata-0.5.6-local.1-windows-x64-setup.exe) · [Pacote tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/Strata-0.5.6-local.1-windows-x64.tar.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/SHA256SUMS.txt).

O mecanismo nativo 0.5.5 e o Control 0.5.6 permanecem inalterados. Foram verificados a instalação, o WebView2 e buscas reais do RustXNG; as respostas do modelo nos testes de interface usam uma API de teste isolada. A qualidade do modelo e a execução simultânea na GPU não estão qualificadas. O EXE não tem assinatura do Windows; a versão estável continua sendo 0.5.1. [Verificação atual](_docs/2026-11-11_btw-deepresearch-rustxng_Codex.md). Os pacotes e medições de 0.5.5 e 0.5.1 abaixo pertencem às versões anteriores.

[Instalação rápida](INSTALL.md) · [Pesquisa e navegador](docs/BROWSER_SEARCH.md)

## Prévia 0.5.5-local.1 — fontes oficiais 0.2.13

[Instalador Windows](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64-setup.exe) ·
[Pacote tar.7z completo](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64.tar.7z) ·
[Somas e publicação](https://github.com/zapabob/Strata/releases/tag/v0.5.5-local.1).
Windows x64 / CUDA sm_120; testado em RTX 5060 Ti 16 GB / RAM 32 GB.
O teste de recursos CUDA passa sem violações; os testes instalados de chat, agente e pastas passaram.
A qualidade ampla não está qualificada: **releaseQualified=false**. O timeout histórico do Prism054 foi preservado.
Importe o tar.gz assinado do motor desta prévia pela tela de preparação.
[Guia atual](docs/HAKUA_INSTALL.md) · [Escopo dos testes](docs/HAKUA_RELEASE.md).

## Estável 0.5.1 — guia e medições anteriores

As versões, downloads e medições abaixo correspondem a 0.5.1.
GitHub Latest e o feed padrão continuam nessa versão estável.

A versão 0.5.1 carrega modelos manualmente e corrige a inicialização do Qwen3.6 nativo. Preserva os modelos existentes e os pacotes de especialistas verificados.

Modelos locais, chat, ferramentas e memória Hakua opcional. Este é o [fork de zapabob](https://github.com/zapabob/Strata) de [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Versão para Windows

O Qwen3.6 nativo atingiu READY em 41,250 segundos com capacidade de 4096 células e passou em seis testes curtos de cache privado. Entradas completas de 98K/131K e a qualidade do modelo com FP16/NVFP4 não foram validadas. Leia os [resultados e limites](docs/HAKUA_RELEASE.md).

Esta versão se destina ao Windows x64 CUDA sm_120. As verificações locais usaram uma RTX 5060 Ti com 16 GB de VRAM e 32 GB de RAM. Leia os [resultados e limites restantes](docs/HAKUA_RELEASE.md) antes de instalar.

**0.5.1** exige atualização manual e não tem assinatura de código do Windows. [Versão](https://github.com/zapabob/Strata/releases/tag/v0.5.1) · [Instalação](docs/HAKUA_INSTALL.md) · [Testes e limites](docs/HAKUA_RELEASE.md).

1. Baixe o [instalador](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64-setup.exe) e compare seu hash com [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.1/SHA256SUMS.txt).
2. Feche o Strata, inclusive o ícone na bandeja, e execute o instalador. Mantenha modelos e dados pessoais fora da pasta do aplicativo.
3. Instale o componente CUDA assinado na tela de preparação pelo canal latest ou pelo arquivo incluído `strata-engine-0.5.1-windows-x86_64-cuda-cuda13.tar.gz`.
4. Escolha um modelo adequado ou **Use a local GGUF** para arquivos existentes. Node e Python já estão incluídos; não é necessário um interpretador do sistema nem um compilador.

As versões seguem [SemVer 2.0.0](https://semver.org/): aplicativo `0.5.1`, mecanismo nativo `0.5.1`; Control `0.5.1`; os ambientes PrismML/TurboQuant sem alterações permanecem em `0.4.0`. O local habitual do aplicativo é `%LOCALAPPDATA%\Programs\Strata` em C:, separado dos modelos. Uma instalação existente pode manter outro local.

O [pacote tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64.tar.7z) inclui o mesmo instalador NSIS, o componente CUDA assinado, Control, as somas de verificação e as instruções. Modelos e dados pessoais não estão incluídos. A publicação usa `v0.5.1`, o alias de tag `latest` e GitHub Latest.

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

Aplicativo/Host: `0.5.1`; mecanismo nativo: `0.5.1`; Control `0.5.1`; Node: `24.22.2`; CPython: `3.12.15`; Hakua-memory: `0.3.5`. Referência upstream: `5d37280d` / `0.2.11`.

0.5.1 integra o upstream 0.2.11 e correções até `5d37280d`: arquivos por conversa, reconexão de respostas ativas, correções de IME e do renderizador, novos modelos, isolamento de fluxos e Pillow 13. Preserva a memória Hakua, a reutilização de GGUF locais e os caches privados do Qwen3.6. A nova compilação CUDA exige verificação própria; as medições de 0.4.1 não validam os novos padrões. A geração nativa com toda a janela permanece sem validação. Consulte os [testes e o estado de publicação](docs/HAKUA_RELEASE.md).

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

## Apoiadores do projeto original Strata

Obrigado a todas as pessoas que apoiam o Strata.

<!-- supporters:start (one line per public supporter, newest last; copy a line and change the GitHub name in all four places) -->
<a href="https://github.com/ryan4yin"><img src="https://github.com/ryan4yin.png?size=96" width="48" height="48" alt="ryan4yin" title="ryan4yin"></a>
<a href="https://github.com/themactep"><img src="https://github.com/themactep.png?size=96" width="48" height="48" alt="themactep" title="themactep"></a>
<a href="https://github.com/macintog"><img src="https://github.com/macintog.png?size=96" width="48" height="48" alt="macintog" title="macintog"></a>
<a href="https://github.com/bisonbet"><img src="https://github.com/bisonbet.png?size=96" width="48" height="48" alt="bisonbet" title="bisonbet"></a>
<a href="https://github.com/vizv"><img src="https://github.com/vizv.png?size=96" width="48" height="48" alt="vizv" title="vizv"></a>
<a href="https://github.com/kod88vn"><img src="https://github.com/kod88vn.png?size=96" width="48" height="48" alt="kod88vn" title="kod88vn"></a>
<a href="https://github.com/seoulworker"><img src="https://github.com/seoulworker.png?size=96" width="48" height="48" alt="seoulworker" title="seoulworker"></a>
<a href="https://github.com/jackyini"><img src="https://github.com/jackyini.png?size=96" width="48" height="48" alt="jackyini" title="jackyini"></a>
<a href="https://github.com/router0mail"><img src="https://github.com/router0mail.png?size=96" width="48" height="48" alt="router0mail" title="router0mail"></a>
<!-- supporters:end -->

## Agradecimentos

Agradecemos aos desenvolvedores do [Strata](https://github.com/Niko1221/Strata) pelo cuidado com a inferência local e uma experiência de desktop acessível. Este fork se apoia nesse trabalho significativo.

Também reconhecemos o [llama.cpp](https://github.com/ggml-org/llama.cpp) e seus colaboradores por aproximarem a inferência em C/C++ de desenvolvedores e usuários, e o [RustXNG](https://github.com/sahenjp/RustXNG) por oferecer um serviço aberto e útil de busca e consulta de fontes para IA local. A engenharia e a manutenção contínua desses projetos merecem reconhecimento.

As integrações e alterações deste fork são mantidas de forma independente. Estes agradecimentos não representam um endosso dos projetos citados.
