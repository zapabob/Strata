import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const root = resolve(import.meta.dirname, '../..');
const edit = (name, fn) => { const path = resolve(root, name); writeFileSync(path, fn(readFileSync(path, 'utf8'))); };
for (const name of ['apps/host/package.json', 'apps/host/package-lock.json', 'apps/desktop/package.json', 'apps/desktop/package-lock.json']) edit(name, text => text.replaceAll('"version": "0.5.8"', '"version": "0.5.9"'));
for (const name of ['apps/desktop/src-tauri/Cargo.toml', 'apps/desktop/src-tauri/Cargo.lock']) edit(name, text => text.replaceAll('version = "0.5.8"', 'version = "0.5.9"'));
for (const name of ['VERSION', 'CONTROL_VERSION']) edit(name, () => '0.5.9\n');
edit('CMakeLists.txt', text => text.replace('project(strata VERSION 0.5.8', 'project(strata VERSION 0.5.9'));
edit('strata_cli/__init__.py', text => text.replace('PRODUCT_VERSION = "0.5.8"', 'PRODUCT_VERSION = "0.5.9"'));
edit('docs/data/release.json', text => {
  const value = JSON.parse(text);
  for (const key of ['product_version', 'control_version', 'engine_version']) value[key] = '0.5.9';
  value.tag = 'v0.5.9'; value.assets = value.assets.map(name => name.replaceAll('0.5.8', '0.5.9'));
  if (!value.historical_releases.some(row => row.tag === 'v0.5.8')) value.historical_releases.push({ tag: 'v0.5.8', product_version: '0.5.8', assets: ['Strata-0.5.8-windows-x64-setup.exe', 'Strata-0.5.8-windows-x64.tar.7z'] });
  return JSON.stringify(value, null, 1) + '\n';
});
const translations = {
  'README.md': ['Stable 0.5.9', 'Protects available system RAM throughout Windows local-model loading and generation. Research can only search and read pages, then writes its answer without tools. Inventory CSV audits use calculated comparison results: a passed check needs no additional evidence.'],
  'README.ja.md': ['正式版 0.5.9', 'Windowsでローカルモデルのロード中と生成中の空きRAMを監視します。調査中は検索とページ取得だけを許可し、最終回答はツールを使わず作成します。在庫CSVの監査は規則に従って件数を計算し、成功済みのチェックに追加の証拠を要求しません。'],
  'README.zh-CN.md': ['正式版 0.5.9', '在Windows本地模型加载和生成期间监控可用内存。研究阶段只允许搜索和读取网页，最终回答不使用工具。库存CSV审核使用确定性计算结果；已通过的检查不需要额外证据。'],
  'README.de.md': ['Stabile Version 0.5.9', 'Überwacht den verfügbaren Arbeitsspeicher beim Laden und Generieren lokaler Windows-Modelle. Recherche erlaubt nur Suche und Seitenabruf; die Antwort entsteht ohne Werkzeuge. CSV-Bestandsprüfungen berechnen Abweichungen nach festen Regeln; bestandene Prüfungen benötigen keine zusätzlichen Nachweise.'],
  'README.fr.md': ['Version stable 0.5.9', 'Surveille la mémoire disponible pendant le chargement et la génération des modèles locaux sous Windows. La recherche autorise uniquement la recherche web et la lecture des pages, puis rédige sans outils. Les audits CSV calculent les écarts selon des règles fixes ; un contrôle réussi ne nécessite aucune preuve supplémentaire.'],
  'README.es.md': ['Versión estable 0.5.9', 'Supervisa la RAM disponible al cargar y ejecutar modelos locales en Windows. La investigación solo permite buscar y leer páginas; la respuesta final se redacta sin herramientas. Las auditorías CSV calculan las diferencias con reglas fijas; una comprobación aprobada no necesita pruebas adicionales.'],
  'README.pt-BR.md': ['Versão estável 0.5.9', 'Monitora a RAM disponível durante o carregamento e a geração de modelos locais no Windows. A pesquisa permite apenas buscar e ler páginas; a resposta final é escrita sem ferramentas. Auditorias CSV calculam divergências por regras fixas; verificações aprovadas não exigem evidências adicionais.'],
  'README.pl.md': ['Wersja stabilna 0.5.9', 'Monitoruje dostępną pamięć RAM podczas ładowania i generowania modeli lokalnych w Windows. Badanie pozwala tylko wyszukiwać i czytać strony; odpowiedź powstaje bez narzędzi. Audyt CSV oblicza różnice według stałych reguł; zaliczone kontrole nie wymagają dodatkowych dowodów.'],
};
for (const [name, [title, body]] of Object.entries(translations)) edit(name, text => {
  if (text.includes('<!-- stable-059 -->')) return text;
  const at = text.indexOf('\n');
  return text.slice(0, at + 1) + `\n<!-- stable-059 -->\n## ${title}\n\n${body}\n\n[Windows NSIS](https://github.com/zapabob/Strata/releases/download/v0.5.9/Strata-0.5.9-windows-x64-setup.exe) · [tar.7z](https://github.com/zapabob/Strata/releases/download/v0.5.9/Strata-0.5.9-windows-x64.tar.7z) · [SHA256SUMS](https://github.com/zapabob/Strata/releases/download/v0.5.9/SHA256SUMS.txt) · [Verification](_docs/2026-11-13_stable-059-workflow-safety_Codex.md)\n\nApp / Terminal / Control / native engine 0.5.9; RustXNG 0.31.1 Full. Build, installation and publication evidence is recorded in the linked verification log. General model quality and full-window generation remain unqualified (releaseQualified=false). Earlier releases and acknowledgements remain below.\n\n` + text.slice(at + 1);
});
