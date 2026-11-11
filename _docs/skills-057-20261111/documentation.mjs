import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const root=resolve(import.meta.dirname,'../..');
const rows=[
['README.ja.md','新しいプレビュー 0.5.7-local.1','`/btw` は実際のサブエージェントへ質問を渡します。専用の親セッションからツールを持たない子を起動し、本題の会話と停止操作を分離します。スキル画面では、完了した作業から再利用できるSKILL.mdを学ぶ機能と、条件が合うスキルを実行ワークフローへ自動適用する機能を個別に有効化できます。手動編集、ワークスペースの範囲、承認設定を尊重します。','導入と手順','インストーラー','tar.7z一括パッケージ'],
['README.zh-CN.md','新预览版 0.5.7-local.1','`/btw` 现在将问题交给真正的子代理。独立父会话启动无工具子代理，主对话和停止操作保持分离。技能页面可分别启用从已完成工作学习 SKILL.md，以及在执行流程中自动应用匹配技能。手动编辑、工作区范围和审批设置受到尊重。','安装与操作','安装程序','tar.7z 完整包'],
['README.de.md','Neue Vorschau 0.5.7-local.1','`/btw` delegiert an einen echten Unteragenten ohne Werkzeuge unter einer eigenen Elternsitzung. Hauptgespräch und Stoppen bleiben getrennt. Unter Skills lassen sich Lernen aus abgeschlossener Arbeit und automatisches Anwenden passender Anleitungen im Arbeitsablauf getrennt aktivieren. Manuelle Änderungen, Arbeitsbereich und Genehmigungen bleiben maßgeblich.','Installation und Anleitung','Installer','tar.7z-Paket'],
['README.fr.md','Nouvelle préversion 0.5.7-local.1','`/btw` délègue à un vrai sous-agent sans outils, sous une session parente distincte. La conversation principale et son arrêt restent indépendants. La page Compétences permet d’activer séparément l’apprentissage de SKILL.md à partir du travail terminé et l’application automatique des instructions correspondantes. Modifications manuelles, espace de travail et autorisations sont respectés.','Installation et utilisation','Installateur','Archive tar.7z'],
['README.es.md','Nueva versión preliminar 0.5.7-local.1','`/btw` delega en un subagente real sin herramientas, con una sesión principal independiente. La conversación original y su parada quedan separadas. En Habilidades puede activar por separado el aprendizaje de SKILL.md desde trabajos completados y la aplicación automática de instrucciones coincidentes. Se respetan las ediciones manuales, el espacio de trabajo y las aprobaciones.','Instalación y uso','Instalador','Paquete tar.7z'],
['README.pt-BR.md','Nova prévia 0.5.7-local.1','`/btw` delega a um subagente real sem ferramentas, sob uma sessão pai separada. A conversa principal e sua interrupção permanecem independentes. Em Habilidades, ative separadamente o aprendizado de SKILL.md a partir do trabalho concluído e a aplicação automática de instruções correspondentes. Edições manuais, escopo do espaço de trabalho e aprovações são respeitados.','Instalação e uso','Instalador','Pacote tar.7z'],
['README.pl.md','Nowa wersja próbna 0.5.7-local.1','`/btw` przekazuje pytanie prawdziwemu podagentowi bez narzędzi, pod osobną sesją nadrzędną. Główna rozmowa i jej zatrzymywanie pozostają niezależne. Na stronie umiejętności można osobno włączyć uczenie SKILL.md z wykonanej pracy oraz automatyczne stosowanie pasujących instrukcji. Ręczne zmiany, zakres obszaru roboczego i zatwierdzenia są respektowane.','Instalacja i użycie','Instalator','Pakiet tar.7z'],
];
for(const [name,title,text,guide,exe,archive] of rows){
  const file=resolve(root,name),before=readFileSync(file,'utf8');
  if(before.includes('<!-- skills-057 -->'))throw new Error('Preserve prior documentation preparation');
  const end=before.indexOf('\n');
  const block=`\n\n<!-- skills-057 -->\n## ${title}\n\n${text}\n\n[${exe}](https://github.com/zapabob/Strata/releases/download/v0.5.7-local.1/Strata-0.5.7-local.1-windows-x64-setup.exe) · [${archive}](https://github.com/zapabob/Strata/releases/download/v0.5.7-local.1/Strata-0.5.7-local.1-windows-x64.tar.7z) · [${guide}](docs/WORKFLOW_SKILLS.md)\n\nRustXNG 0.31.1 Full / native 0.5.5 / Control 0.5.6. [0.5.7 delivery status](_docs/2026-11-11_workflow-skill-learning_Codex.md). Stable / GitHub Latest: 0.5.1.\n\n`;
  writeFileSync(file,before.slice(0,end)+block+before.slice(end+1));
}
let english=readFileSync(resolve(root,'README.md'),'utf8').replaceAll('0.5.6-local.1','0.5.7-local.1').replaceAll('_docs/2026-11-11_btw-deepresearch-rustxng_Codex.md','_docs/2026-11-11_workflow-skill-learning_Codex.md');
english=english.replace('The **0.5.7-local.1 preview** adds `/btw`, `/deepresearch` and bundled','The **0.5.7-local.1 preview** adds real `/btw` subagents, workflow skill learning\nand automatic skill application. It retains `/deepresearch` and bundled');
english=english.replace('[0.5.5-local.1](https://github.com/zapabob/Strata/releases/tag/v0.5.5-local.1) /','[0.5.6-local.1](https://github.com/zapabob/Strata/releases/tag/v0.5.6-local.1) /');
english=english.replace('A separate answer appears below the conversation, using a snapshot of completed\nmessages with no tools.','A real subagent starts under a dedicated side-question parent and answers below\nthe conversation. It receives a snapshot of completed messages and has no tools.');
english=english.replace('## Existing capabilities','## Learn and apply workflow skills\n\nOpen **Skills** to enable learning from completed agent work and automatic\napplication independently. The same task model reviews bounded, redacted tool\nmetadata and may save a private, editable SKILL.md. Future matching workflows\nreceive complete enabled instructions, with trigger phrases and workspace scope.\nManual edits and approval choices are preserved; revision history and undo are\navailable. New profiles keep both options off.\n[How it works and its limits](docs/WORKFLOW_SKILLS.md).\n\nWe appreciate [Hermes Agent](https://github.com/NousResearch/hermes-agent) for\nits work on reusable procedural skills, which inspired this document-based loop.\n\n## Existing capabilities');
english=english.replace('The preview is [published]','The preview delivery is tracked at [the release]');
writeFileSync(resolve(root,'README.md'),english);
for(const name of ['INSTALL.md','docs/HAKUA_INSTALL.md']){
  const file=resolve(root,name),before=readFileSync(file,'utf8');
  const link=name.startsWith('docs/')?'WORKFLOW_SKILLS.md':'docs/WORKFLOW_SKILLS.md';
  const next=before.replaceAll('0.5.6-local.1','0.5.7-local.1').replaceAll('2026-11-11_btw-deepresearch-rustxng_Codex.md','2026-11-11_workflow-skill-learning_Codex.md');
  const end=next.indexOf('\n');writeFileSync(file,next.slice(0,end)+`\n\n0.5.7 adds real /btw subagents, private workflow skill learning and automatic skill application. [Settings, data and undo](${link}).\n`+next.slice(end));
}
console.log('Updated eight README languages and installation entry points; existing credits and historical assets retained.');
