import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {nativeSources,sha256,verifyNativeBuild} from '../scripts/release-integrity.mjs';

test('packaging rejects an engine from previous native source or a substituted binary',t=>{
 const root=mkdtempSync(join(tmpdir(),'hakua-native-'));t.after(()=>rmSync(root,{recursive:true,force:true}));
 const stage=join(root,'stage');mkdirSync(stage);mkdirSync(join(root,'src'));
 const source=join(root,'src','engine.cpp'),exe=join(stage,'strata.exe');
 writeFileSync(source,'current code');writeFileSync(exe,'fresh binary');
 const manifest={version:'0.3.3',entrypoint:'strata.exe'};
 writeFileSync(join(stage,'native-build.json'),JSON.stringify({...manifest,sha256:sha256(exe),sources:nativeSources(root)}));
 assert.doesNotThrow(()=>verifyNativeBuild(stage,root,manifest));
 writeFileSync(source,'newer code');assert.throws(()=>verifyNativeBuild(stage,root,manifest),/sources changed/);
 writeFileSync(source,'current code');writeFileSync(exe,'older binary');assert.throws(()=>verifyNativeBuild(stage,root,manifest),/identity/);
});

test('packaging binds the reviewed CUDA budget and rejects changed or escaping budgets',t=>{
 const root=mkdtempSync(join(tmpdir(),'hakua-native-budget-'));t.after(()=>rmSync(root,{recursive:true,force:true}));
 const stage=join(root,'stage');mkdirSync(stage);mkdirSync(join(root,'src'));
 const exe=join(stage,'strata.exe'),budget=join(root,'budget.json');
 writeFileSync(exe,'fresh binary');writeFileSync(budget,'reviewed measurements');
 const manifest={version:'0.3.3',entrypoint:'strata.exe'};
 const record={...manifest,sha256:sha256(exe),sources:nativeSources(root),recipe:{cudaSpillBaseline:{path:'budget.json',sha256:sha256(budget)}}};
 const save=()=>writeFileSync(join(stage,'native-build.json'),JSON.stringify(record));
 save();assert.doesNotThrow(()=>verifyNativeBuild(stage,root,manifest));
 writeFileSync(budget,'different allowances');assert.throws(()=>verifyNativeBuild(stage,root,manifest),/baseline changed/);
 record.recipe.cudaSpillBaseline.path='../budget.json';save();assert.throws(()=>verifyNativeBuild(stage,root,manifest),/Unsafe/);
 record.recipe.cudaSpillBaseline.path='..\\budget.json';save();assert.throws(()=>verifyNativeBuild(stage,root,manifest),/Unsafe/);
});
