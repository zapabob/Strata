# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata é a versão independente de [Niko1221/Strata](https://github.com/Niko1221/Strata) voltada para Windows. Executa modelos locais em conversas, programação e tarefas com agentes. Em modelos MoE compatíveis, o motor nativo distribui os pesos dos especialistas entre a memória da GPU, a RAM e o SSD.

## Como começar

Baixe o instalador do Windows para a conta atual na [página de versões do Hakua](https://github.com/zapabob/Strata/releases). O motor CUDA é distribuído separadamente. Na tela **Modelos**, selecione o perfil dos pesos instalados. Para Inkling 2 Mini SC117, os perfis SQ-10, SQ-15 e SQ-20 são distintos. Ajuste a janela de contexto à memória disponível. Consulte o [guia do Windows](docs/HAKUA_INSTALL.md) e a [documentação dos modelos](docs/MODELS.md).

## Reutilize fluxos de trabalho

Em **Configurações → Ferramentas**, ative a busca de habilidades sob demanda. O agente pesquisa os procedimentos necessários sem carregar o catálogo completo. Em **Habilidades**, os controles para aprender com tarefas concluídas e aplicar procedimentos automaticamente são independentes. Cada procedimento é um `SKILL.md` editável. A aplicação automática verifica nomes, frases de ativação e o espaço de trabalho. Habilidades, agentes auxiliares, operações em arquivos e `/goal` têm controles separados. [Guia de fluxos de trabalho](docs/WORKFLOW_SKILLS.md)

## Medições e limites

Na RTX 5060 Ti de 16 GB, o SC117 SQ-10 criou uma cena Pagoda Bench em um único HTML por `/goal` e corrigiu o próprio renderizador após receber diagnósticos. O Chrome mostrou os cinco telhados após afastar a câmera. A cena informou 7.079 voxels. A vista inicial cortou o topo e não foi medida uma pontuação oficial. As [medições do motor 0.8.5](_docs/2026-11-27_v085-release-notes.md) usaram entradas curtas na capacidade de contexto indicada.

Veja o [registro de versões](docs/HAKUA_RELEASE.md) para compatibilidade, assinaturas e limites dos testes. O Hakua usa a [licença MIT](LICENSE). Modelos e componentes seguem seus próprios termos.
