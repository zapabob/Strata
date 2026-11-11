"""Add the next release above immutable multilingual release history."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
translations = {
 'README.md': ('Stable 0.5.8', 'Repairs the extended context, compaction and search-guard tests. Each agent fixture owns its profile, and the actual Harness child receives the selected environment. CI also checks translation coverage, platform-specific fixtures and independent product/Control/engine versions.'),
 'README.ja.md': ('正式版 0.5.8', '長い会話、要約、検索回数制限の拡張テストを修正しました。エージェントの子プロセスには選択した環境を渡し、テストごとにプロファイルを分離します。翻訳の不足、OS 固有のテスト、本体・Control・エンジンの独立したバージョン情報も CI で検証します。'),
 'README.zh-CN.md': ('正式版 0.5.8', '修复长对话、摘要和搜索次数限制的扩展测试。代理子进程接收所选环境，每个测试使用独立配置目录。CI 同时验证翻译完整性、各平台测试以及应用、Control 和引擎的独立版本。'),
 'README.de.md': ('Stabile Version 0.5.8', 'Behebt die erweiterten Tests für lange Gespräche, Zusammenfassungen und Suchbegrenzungen. Jeder Test nutzt ein eigenes Profil; der Agent-Unterprozess erhält die gewählte Umgebung. CI prüft außerdem Übersetzungen, Plattformtests und die unabhängigen Versionen von App, Control und Engine.'),
 'README.fr.md': ('Version stable 0.5.8', 'Corrige les tests étendus de contexte, de résumé et de limitation des recherches. Chaque test possède son propre profil et le sous-processus agent reçoit l’environnement choisi. La CI vérifie aussi les traductions, les tests par plateforme et les versions indépendantes de l’application, de Control et du moteur.'),
 'README.es.md': ('Versión estable 0.5.8', 'Corrige las pruebas ampliadas de contexto, resumen y límites de búsqueda. Cada prueba usa un perfil propio y el subproceso del agente recibe el entorno elegido. CI también verifica traducciones, pruebas por plataforma y las versiones independientes de la aplicación, Control y motor.'),
 'README.pt-BR.md': ('Versão estável 0.5.8', 'Corrige os testes ampliados de contexto, resumo e limites de pesquisa. Cada teste usa um perfil próprio e o subprocesso do agente recebe o ambiente escolhido. A CI também verifica traduções, testes por plataforma e as versões independentes do aplicativo, Control e mecanismo.'),
 'README.pl.md': ('Wersja stabilna 0.5.8', 'Naprawia rozszerzone testy kontekstu, podsumowań i limitów wyszukiwania. Każdy test ma osobny profil, a proces potomny agenta otrzymuje wybrane środowisko. CI sprawdza również tłumaczenia, testy platformowe oraz niezależne wersje aplikacji, Control i silnika.'),
}
for name, (title, body) in translations.items():
    path = ROOT / name
    text = path.read_text(encoding='utf-8')
    first, rest = text.split('\n', 1)
    section = f'''\n<!-- stable-058 -->
## {title}

{body}

[Windows NSIS](https://github.com/zapabob/Strata/releases/download/v0.5.8/Strata-0.5.8-windows-x64-setup.exe) · [tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.8/Strata-0.5.8-windows-x64.tar.7z) · [SHA256SUMS](https://github.com/zapabob/Strata/releases/download/v0.5.8/SHA256SUMS.txt) · [0.5.8 verification](_docs/2026-11-11_stable-058-context-ci_Codex.md)

RustXNG 0.31.1 Full / app, Terminal, native engine and Control 0.5.8. Native model quality remains unqualified (`releaseQualified=false`). Previous releases and their measurements follow below.

'''
    if '<!-- stable-058 -->' not in text:
        path.write_text(first + '\n' + section + rest, encoding='utf-8', newline='\n')
path = ROOT / 'AGENTS.md'
text = path.read_text(encoding='utf-8')
if 'Hakua product version 0.5.8' not in text:
    text = text.replace('# AGENTS.md', '# AGENTS.md\n\nHakua product version 0.5.8 is the current candidate source; engine 0.5.5 and\nControl 0.5.6 retain their frozen signed payloads. Publication and installation\nare recorded in _docs/2026-11-11_stable-058-context-ci_Codex.md. Historical\nmeasurements below retain their original product versions.', 1)
    path.write_text(text, encoding='utf-8', newline='\n')
for name in ('build.py', 'delivery.py', 'publish.py', 'qa-installed.mjs', 'normal-start.py', 'normal-unload.py', 'nsis-check.mjs'):
    target = HERE / name
    if target.exists():
        continue
    text = (ROOT / '_docs/stable-057-20261111' / name).read_text(encoding='utf-8')
    text = text.replace('stable-057-20261111', 'stable-058-20261111').replace('0.5.7', '0.5.8')
    target.write_text(text, encoding='utf-8', newline='\n')
