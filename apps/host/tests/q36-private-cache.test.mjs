import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareQ36Launch,Q36_PRIVATE_CACHE_DIGESTS} from '../server/q36-run-contract.mjs';

test('private Qwen3.6 binds the binary and preserves zero shared-cache flags with scoped reuse',()=>{
 const digest='e'.repeat(64);
 const input={args:['--max-context','4096'],privacyRequired:true,binarySha256:digest,requested:{parallel:1}};
 assert.equal(prepareQ36Launch(input).error.code,'q36_private_cache_unsupported');
 Q36_PRIVATE_CACHE_DIGESTS.add(digest);
 try{
  const out=prepareQ36Launch(input);assert.equal(out.ok,true);
  assert.deepEqual(out.argv,['--max-context','4096','--prompt-cache','0','--conversation-cache-mib','0','--private-conversation-cache']);
  assert.equal(out.contract.effective.scopedConversationCache,true);
  assert.deepEqual(input.args,['--max-context','4096']);
  assert.equal(prepareQ36Launch({...input,requested:{parallel:2}}).error.code,'q36_private_cache_parallel');
  for(const args of [['--prompt-cache','1'],['--prompt-cache=0'],['--prompt-cache','0','--prompt-cache','0']]){
   assert.equal(prepareQ36Launch({...input,args}).error.code,'unsupported_setting');
  }
  assert.equal(prepareQ36Launch({...input,privacyRequired:false,args:['--prompt-cache','0']}).ok,false);
  const noCache=prepareQ36Launch({...input,privacyRequired:false,args:['--prompt-cache','0','--conversation-cache-mib','0']});
  assert.equal(noCache.ok,true);assert.equal(noCache.contract.effective.scopedConversationCache,false);
 }finally{Q36_PRIVATE_CACHE_DIGESTS.delete(digest);}
});
