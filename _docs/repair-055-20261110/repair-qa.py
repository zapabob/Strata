"""Extend fresh packaged QA with real supervisor-agent and teardown evidence."""
from __future__ import annotations

import json
from pathlib import Path


def replace(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError('Reviewed packaged QA anchor changed: ' + old[:100])
    return text.replace(old, new)


def repair_qa(text: str, kind: str, here: Path) -> str:
    if kind != 'prism':
        return text
    text = replace(text, "STRATA_AGENT:'off'", "STRATA_AGENT:'on'")
    text = replace(text, "const status=await until(async()=>{const value=await call('/api/engine/status');return value.running?value:false;});",
        "const status=await until(async()=>{const value=await call('/api/engine/status');assert.notEqual(value.status,'error','Prism failed before readiness');return value.running?value:false;});")
    # Keep both original plain-chat assertions; a separate UI request must emit
    # the agent start frame, so an ordinary fallback cannot pass this repair.
    anchor = "await page.screenshot({path:join(home,'screenshots',`prism041-cycle-${cycle}.png`),fullPage:true});"
    extra = r'''
   const agentChatId='prism-agent-qa-'+cycle;
   await call('/api/chats/import','POST',{sessions:[{id:agentChatId,title:'Isolated supervisor agent QA',createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),messages:[],tokensIn:0,tokensOut:0,workspace:join(home,'workspace'),preferences:{agent:true,useTools:true,thinking:'Off',thinkingBudget:0}}]});
   await page.goto(base+'/#/chat/'+agentChatId);await page.reload();
   await page.getByRole('heading',{name:'Isolated supervisor agent QA',exact:true}).waitFor();
   const responsePromise=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/chat/stream'&&r.request().method()==='POST',{timeout:180000});
   const input=page.getByRole('textbox',{name:'Message Strata',exact:true});
   await input.fill('What is 2 + 3? Reply with only the number. Do not use tools.');await input.press('Enter');
   const response=await responsePromise;assert.equal(response.status(),200);
   const raw=await response.text();assert.ok(raw.length<2*1024*1024,'Agent response exceeds QA budget');
   const frames=raw.split('\n').filter(line=>line.trim()).map(line=>JSON.parse(line));
   assert.ok(frames.some(f=>f.type==='start'&&f.agent===true),'Actual Harness agent path was not used');
   assert.equal(frames.some(f=>f.type==='error'||f.demo===true||['agent-skipped','agent-unavailable'].includes(f.code)),false,'Agent errored or silently fell back');
   assert.ok(frames.some(f=>f.type==='done'),'Agent stream did not complete');
   const agentReply=await until(async()=>{const value=await call('/api/chats/'+agentChatId);return value.session.messages.find(m=>m.role==='assistant'&&m.content?.trim()&&!m.streaming);});
   assert.equal(agentReply.content.trim(),'5');assert.notEqual(agentReply.demo,true);assert.equal(agentReply.error,undefined);
   result.actualSupervisorAgent=true;result.agentCycles=(result.agentCycles??0)+1;
   result.checks.push('actual-supervisor-backed-agent-answer-'+cycle);
'''
    text = replace(text, anchor, extra + '\n   ' + anchor)
    old = "await browser?.close().catch(()=>{});browser=null;if(child?.exitCode===null)child.kill();if(child)await until(()=>child.exitCode!==null||child.signalCode!==null,15);child=null;base=null;"
    close = json.dumps((here / 'close-qa-window.py').as_posix())
    new = ("if(!child)return;if(child.exitCode===null){const closed=spawnSync(py,['-B'," + close +
        ",'--pid',String(child.pid),'--app',app,'--home',home],{encoding:'utf8',windowsHide:true,timeout:45000});"
        "assert.equal(closed.status,0,closed.stderr);await until(()=>child.exitCode!==null||child.signalCode!==null,60);}"
        "await browser?.close().catch(()=>{});browser=null;child=null;base=null;"
        "const check=spawnSync(py,['-B'," + json.dumps((here / 'probe.py').as_posix()) +
        "],{encoding:'utf8',windowsHide:true,timeout:30000});assert.equal(check.status,0,check.stderr);"
        "assert.deepEqual(JSON.parse(check.stdout).processCounts,{shell:0,native:0,llama:0});"
        "result.actualTeardownChecks=(result.actualTeardownChecks??0)+1;")
    return replace(text, old, new)
