/** Bump only app product metadata; independently pinned components stay frozen. */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
if(!process.argv.includes('--execute')){console.log('Dry run: product 0.5.6-local.1 -> 0.5.7-local.1');process.exit(0);}
const root=resolve(import.meta.dirname,'../..');
for(const path of ['VERSION','apps/host/package.json','apps/host/package-lock.json','apps/desktop/package.json','apps/desktop/package-lock.json','apps/desktop/src-tauri/Cargo.toml','apps/desktop/src-tauri/Cargo.lock']){
  const file=resolve(root,path),text=readFileSync(file,'utf8');
  if(!text.includes('0.5.6-local.1'))throw new Error('Unexpected product metadata: '+path);
  writeFileSync(file,text.replaceAll('0.5.6-local.1','0.5.7-local.1'));
}
const build=readFileSync(resolve(root,'_docs/search-056-20261111/build.py'),'utf8');
writeFileSync(resolve(import.meta.dirname,'build.py'),build.replaceAll('search-056-20261111-codex','skills-057-20261111-codex').replaceAll('0.5.6-local.1','0.5.7-local.1'),{flag:'wx'});
