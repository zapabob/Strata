import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {verifyTree,verifyHost,verifyEngine,verifyNativeBuild,hostSources,nativeSources,sha256,verifyPublicAssets,PUBLIC_ASSET_COMMIT} from '../scripts/release-integrity.mjs';

test('release freshness rejects stale, missing and leftover Python sources', t=>{
 const root=mkdtempSync(join(tmpdir(),'hakua-release-'));
 t.after(()=>rmSync(root,{recursive:true,force:true}));
 const source=join(root,'source'),staged=join(root,'staged');
 mkdirSync(source);mkdirSync(staged);
 writeFileSync(join(source,'runtime.py'),'current');
 writeFileSync(join(staged,'runtime.py'),'old');
 assert.throws(()=>verifyTree(source,staged,{pythonOnly:true}),/Stale staged source/);
 writeFileSync(join(staged,'runtime.py'),'current');
 assert.doesNotThrow(()=>verifyTree(source,staged,{pythonOnly:true}));
 writeFileSync(join(source,'memory.py'),'needed');
 assert.throws(()=>verifyTree(source,staged,{pythonOnly:true}),/membership/);
 writeFileSync(join(staged,'memory.py'),'needed');
 writeFileSync(join(staged,'removed.py'),'old');
 assert.throws(()=>verifyTree(source,staged,{pythonOnly:true}),/membership/);
});

test('GUI/host source and generated asset changes stop packaging',t=>{
 const root=mkdtempSync(join(tmpdir(),'hakua-gui-'));
 t.after(()=>rmSync(root,{recursive:true,force:true}));
 for(const name of ['src','public','server','dist'])mkdirSync(join(root,name));
 const source=join(root,'src','app.tsx'),asset=join(root,'dist','index.html');
 writeFileSync(source,'current');writeFileSync(asset,'built');
 writeFileSync(join(root,'dist','release-build.json'),JSON.stringify({sources:hostSources(root),assets:{'index.html':sha256(asset)}}));
 assert.doesNotThrow(()=>verifyHost(root));
 writeFileSync(source,'changed');assert.throws(()=>verifyHost(root),/Stale GUI/);
 writeFileSync(source,'current');writeFileSync(asset,'tampered');assert.throws(()=>verifyHost(root),/Changed GUI/);
});

test('public asset provenance rejects replaced artwork, missing notices and supplied fonts',t=>{
 const root=mkdtempSync(join(tmpdir(),'hakua-public-assets-'));t.after(()=>rmSync(root,{recursive:true,force:true}));
 mkdirSync(join(root,'icons'));mkdirSync(join(root,'licenses'));
 const icon=join(root,'icons','sprite.svg'),notice=join(root,'licenses','Lucide-LICENSE.txt');
 writeFileSync(icon,'approved icons');writeFileSync(notice,'copyright and license');
 const record={lucide_commit:PUBLIC_ASSET_COMMIT,files:{'icons/sprite.svg':sha256(icon),'licenses/Lucide-LICENSE.txt':sha256(notice)}};
 assert.doesNotThrow(()=>verifyPublicAssets(root,record));
 writeFileSync(icon,'different icons');assert.throws(()=>verifyPublicAssets(root,record),/payload changed/);writeFileSync(icon,'approved icons');
 rmSync(notice);assert.throws(()=>verifyPublicAssets(root,record),/membership/);writeFileSync(notice,'copyright and license');
 const font=join(root,'GTWalsheimPro.woff2');writeFileSync(font,'unqualified font');record.files['GTWalsheimPro.woff2']=sha256(font);
 assert.throws(()=>verifyPublicAssets(root,record),/Unapproved/);
});

test('engine payload hash, version and entrypoint are required',t=>{
 const root=mkdtempSync(join(tmpdir(),'hakua-engine-'));
 t.after(()=>rmSync(root,{recursive:true,force:true}));
 const exe=join(root,'strata.exe');writeFileSync(exe,'same-length');
 const manifest={id:'strata-engine',version:'0.1.54',entrypoint:'strata.exe',files:[{path:'strata.exe',bytes:11,sha256:sha256(exe)}]};
 const save=()=>writeFileSync(join(root,'engine-component.json'),JSON.stringify(manifest));save();
 assert.doesNotThrow(()=>verifyEngine(root,'0.1.54'));
 writeFileSync(exe,'wrong-bytes');assert.throws(()=>verifyEngine(root,'0.1.54'),/Changed engine payload/);
 writeFileSync(exe,'same-length');assert.throws(()=>verifyEngine(root,'0.1.55'),/Stale/);
 writeFileSync(join(root,'leftover.dll'),'old');assert.throws(()=>verifyEngine(root,'0.1.54'),/membership/);rmSync(join(root,'leftover.dll'));
 manifest.entrypoint='missing.exe';save();assert.throws(()=>verifyEngine(root,'0.1.54'),/entrypoint/);
 manifest.entrypoint='strata.exe';manifest.files[0].path='../outside';save();assert.throws(()=>verifyEngine(root,'0.1.54'),/entrypoint|Unsafe/);
});
