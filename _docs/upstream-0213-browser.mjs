/** Fresh real-Host workspace UI check for the merged source, never installed/model qualification. */
import {readFileSync} from 'node:fs';
const fixture='H:/Strata/releases/local-053-20261109-opencode/crud-browser-check.mjs';
let source=readFileSync(fixture,'utf8');
for(const [before,after] of [
  ["base='H:/Strata/releases/local-053-20261109-opencode'", "base='H:/Strata/releases/upstream-0213-20261109-opencode'"],
  ["'crud-browser-r1'", "'crud-browser-0213-r1'"],
  ["const root='C:/Users/downl/Documents/ChatGPT/Strata'", "const browserEnv=Object.fromEntries(Object.entries(process.env).filter(([key])=>!/^(STRATA_|DSH_|WEBVIEW2_)/i.test(key)&&!/(API_KEY|TOKEN|SECRET|PASSWORD)$/i.test(key)));const root='C:/Users/downl/Documents/ChatGPT/Strata'"],
  ["channel:'msedge',headless:true", "channel:'msedge',headless:true,env:browserEnv"],
  [".fill('Edited old note.\\n');", ".fill('Edited old note.\\n');await page.setViewportSize({width:1100,height:900});await dialog.getByRole('textbox',{name:'File contents',exact:true}).waitFor();await page.setViewportSize({width:1600,height:1000});result.checks.push('editor-survives-sidebar-breakpoint');"],
  ["result.error=e.stack", "result.error=e.message"],
]){
  if(source.split(before).length!==2)throw new Error('Reviewed source-browser fixture changed: '+before);
  source=source.replace(before,after);
}
source=source.replaceAll('fullPage:true','fullPage:false');
await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
