/** Pure acceptance-contract tests only: no HTTP server, mocked API, app or model. */
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {validateQ36ProjectionSettings,validateQ36ProjectionObservation} from './q36-projection-acceptance.mjs';

const settings=()=>({fields:[{id:'refusal_direction_removal',supported:false,unavailableReason:'Qwen3.6 unsupported'}],values:{refusal_direction_removal:null},refusalProjection:{requested:false,supported:false,reason:'Qwen3.6 unsupported'}});
const instance=()=>({status:'ready',q36Run:{observed:{status:'observed',generation:'current',processId:12}},metrics:{engine:{cvec:0,native_child:{alive:true,admitted:true,generation:'current',process_id:12}}}});

test('Q36 negative capability needs both actual unsupported fields and reasons',()=>{
 assert.equal(validateQ36ProjectionSettings(settings()).supported,false);
 for(const change of [s=>{s.fields=[];},s=>{s.fields[0].supported=true;},s=>{s.fields[0].unavailableReason='';},s=>{s.refusalProjection.supported=true;},s=>{s.refusalProjection.reason='';}]){
  const s=settings();change(s);assert.throws(()=>validateQ36ProjectionSettings(s));
 }
});
test('saved enable intent is never evidence of runtime application',()=>{
 const s=settings();s.values.refusal_direction_removal=true;s.refusalProjection.requested=true;
 assert.throws(()=>validateQ36ProjectionSettings(s));
 for(const state of ['loaded','applied','request-off','unverified','unknown'])assert.throws(()=>validateQ36ProjectionObservation(instance(),state));
});
test('OFF requires real zero INFO and current live-child generation/PID',()=>{
 assert.equal(validateQ36ProjectionObservation(instance(),'off').state,'off');
 for(const change of [i=>{i.metrics.engine.cvec=undefined;},i=>{i.metrics.engine.native_child.alive=false;},i=>{i.metrics.engine.native_child.admitted=false;},i=>{i.metrics.engine.native_child.generation='old';},i=>{i.metrics.engine.native_child.process_id=11;}]){
  const i=instance();change(i);assert.throws(()=>validateQ36ProjectionObservation(i,'off'));
 }
});
test('unload and absent INFO are unobserved, not a stale OFF or positive badge',()=>{
 assert.equal(validateQ36ProjectionObservation(undefined,'unobserved',{unloaded:true}).state,'unobserved');
 assert.throws(()=>validateQ36ProjectionObservation(instance(),'off',{unloaded:true}));
 const stopped=instance();stopped.status='stopped';assert.throws(()=>validateQ36ProjectionObservation(stopped,'off'));
 const stale=instance();stale.metrics.engine.cvec='project:4-44';assert.throws(()=>validateQ36ProjectionObservation(stale,'unobserved'));
});
