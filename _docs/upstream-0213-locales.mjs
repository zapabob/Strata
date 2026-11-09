/** Compare existing locale coverage with the exact pre-merge Git parent. */
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const parent='1f6661441bf7c09791abd6806a0e551477110b48';
const old=name=>JSON.parse(execFileSync('git',['show',`${parent}:apps/host/src/locales/${name}.json`],{encoding:'utf8'}));
const english=Object.keys(old('en'));
const rows=[];
for(const name of ['zh','ja','de','es','fr','pt','ru','ko']){
  const before=old(name),after=JSON.parse(readFileSync(`apps/host/src/locales/${name}.json`,'utf8'));
  const baseline=english.filter(key=>!(key in before)),current=english.filter(key=>!(key in after));
  assert.ok(current.every(key=>baseline.includes(key)),`${name}: new missing keys`);
  rows.push({language:name,baselineMissing:baseline.length,currentMissing:current.length,remainingKeys:current});
}
console.log(JSON.stringify({parent,noNewMissingKeys:true,rows},null,2));
