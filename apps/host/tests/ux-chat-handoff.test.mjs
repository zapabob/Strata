/** Runs actual ChatScreen submit closures and MessageView's early user return. No browser/GUI claim. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {build} from 'esbuild';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

async function chat(){
  const file=fileURLToPath(new URL('../src/screens/Chat.tsx',import.meta.url)),source=readFileSync(file,'utf8');
  const key='chat'+Math.random().toString(36).slice(2),c={states:[],cursor:0,sent:[],store:{sessions:[{id:'a',messages:[],preferences:{agent:false,useTools:false}}],parked:{},quotes:{},activeSession:'a',activeWorkspace:'root',streaming:false,connection:'live',library:{loaded:'hikari',variants:[{id:'hikari',label:'Existing Hikari'}],mode:'real'},remoteModel:null,providers:{connections:[]}}};globalThis[key]=c;
  Object.defineProperty(globalThis,'localStorage',{configurable:true,value:{getItem:()=>null,setItem:()=>{}}});Object.defineProperty(globalThis,'sessionStorage',{configurable:true,value:{getItem:()=>null,setItem:()=>{}}});
  const imports=new Map();for(const match of source.matchAll(/import\s*\{([\s\S]*?)\}\s*from\s*['"]([^'"]+)['"]/g)){const names=match[1].split(',').map(s=>s.trim()).filter(s=>s&&!s.startsWith('type '));imports.set(match[2],[...new Set([...(imports.get(match[2])??[]),...names])]);}
  const custom={
    useStore:'fn=>fn(c.store)',sendMessage:'async(text,options)=>{c.sent.push({text,options});c.store.sessions[0].messages.push({id:"sent",role:"user",content:text,at:new Date().toISOString(),webSources:options?.webSearch?.sources.map(({url,title})=>({url,title}))});}',
    useLocation:'()=>({route:"chat",param:"a"})',useNative:'()=>({instances:[]})',useChatPhotos:'()=>[]',usePlan:'()=>null',usePlanQuiet:'()=>null',useLiveStatus:'()=>null',
    tr:'v=>v',localeTag:'()=>"en"',relTime:'()=>"now"',timeSkipPrompt:'()=>null',noModelNotice:'()=>null',previewWidth:'()=>400',DEFAULT_PREVIEW_FRACTION:'0.5',PREVIEW_SPLIT_KEY:'"preview"',KEYS_UP:'[]',PILL_DISTANCE:'100',getSlashCommands:'()=>[]',
  };
  const compiled=await build({stdin:{contents:source+'\nexport { MessageView };',resolveDir:dirname(file),sourcefile:file,loader:'tsx'},bundle:true,write:false,format:'esm',platform:'node',jsx:'automatic',logLevel:'silent',plugins:[{name:'chat-boundaries',setup(b){b.onResolve({filter:/.*/},args=>args.path==='../lib/quotes'?{path:resolve(dirname(file),'../lib/quotes.ts')}:{path:args.path,namespace:'stub'});b.onLoad({filter:/.*/,namespace:'stub'},args=>{
    if(args.path==='react/jsx-runtime')return {contents:'export const Fragment="Fragment";export const jsx=(type,props)=>({type,props});export const jsxs=jsx;'};
    if(args.path==='react')return {contents:`const c=globalThis[${JSON.stringify(key)}];export const memo=f=>f,useMemo=f=>f(),useCallback=f=>f,useEffect=()=>{};export function useState(initial){const i=c.cursor++;if(!(i in c.states))c.states[i]=typeof initial==='function'?initial():initial;return [c.states[i],v=>c.states[i]=typeof v==='function'?v(c.states[i]):v];}export const useRef=v=>useState({current:v})[0];`};
    return {contents:`const c=globalThis[${JSON.stringify(key)}];`+(imports.get(args.path)??[]).map(name=>`export const ${name}=${custom[name]??(/^[A-Z]/.test(name)?JSON.stringify(name):'()=>null')};`).join('\n')};
  });}}]});
  const module=await import('data:text/javascript;base64,'+Buffer.from(compiled.outputFiles[0].text).toString('base64'));
  return {c,module,render(){c.cursor=0;return module.ChatScreen();}};
}
function nodes(node,predicate){if(!node||typeof node!=='object')return [];if(Array.isArray(node))return node.flatMap(n=>nodes(n,predicate));return [...(predicate(node)?[node]:[]),...Object.values(node.props??{}).flatMap(v=>nodes(v,predicate))];}
const composer=tree=>nodes(tree,n=>n.type?.name==='Composer')[0];
test('external typed research opens explicit search once, then selected results send an ordinary question to the same model',async()=>{
  const h=await chat();let tree=h.render();composer(tree).props.setDraft('/research topic');tree=h.render();composer(tree).props.onSubmit();
  tree=h.render();let dialog=nodes(tree,n=>n.type==='WebSearchDialog')[0];assert.equal(dialog.props.open,true);assert.equal(h.c.sent.length,0);
  const result={resultId:'record',sources:[{url:'https://example.com/source',title:'Source',snippet:'Snippet'}],expiresAt:Date.now()+60000};dialog.props.onUse(result);dialog.props.onClose();
  tree=h.render();composer(tree).props.onSubmit();
  assert.equal(h.c.sent.length,1);assert.equal(h.c.sent[0].text,'topic');assert.equal(h.c.sent[0].options.webSearch.resultId,'record');assert.equal(h.c.store.library.loaded,'hikari');assert.equal(h.c.store.remoteModel,null);
});
test('sent user message renders source URLs and snippet-only disclosure through its actual early-return branch',async()=>{
  const h=await chat();let tree=h.render();composer(tree).props.setDraft('Question');tree=h.render();composer(tree).props.onSearch();tree=h.render();const dialog=nodes(tree,n=>n.type==='WebSearchDialog')[0];
  dialog.props.onUse({resultId:'record',sources:[{url:'https://example.com/source',title:'Source',snippet:'Snippet'}],expiresAt:Date.now()+60000});dialog.props.onClose();tree=h.render();composer(tree).props.onSubmit();
  const message=h.c.store.sessions[0].messages.at(-1);assert.equal(message.role,'user');h.c.cursor=0;tree=h.module.MessageView({message,isLast:true});
  assert.equal(nodes(tree,n=>n.type==='a'&&n.props.href==='https://example.com/source').length,1);
  assert.equal(nodes(tree,n=>n.type==='p'&&n.props.children==='Search references · snippets only').length,1);
});
test('supervised agent research retains the current main-line route',async()=>{
  const h=await chat();h.c.store.engine={engine:{running:true}};h.c.store.sessions[0].preferences.agent=true;
  let tree=h.render();composer(tree).props.setDraft('/research topic');tree=h.render();composer(tree).props.onSubmit();
  assert.equal(h.c.sent.length,1);assert.equal(h.c.sent[0].text,'/research topic');
  assert.equal(nodes(h.render(),n=>n.type==='WebSearchDialog')[0].props.open,false);
});
test('selected references coexist with current quote composition and are consumed once',async()=>{
  const h=await chat();h.c.store.quotes.a=[{id:'q',text:'Quoted passage',messageId:'earlier',role:'assistant'}];
  let tree=h.render();composer(tree).props.setDraft('Question');tree=h.render();composer(tree).props.onSearch();
  const dialog=nodes(h.render(),n=>n.type==='WebSearchDialog')[0];
  dialog.props.onUse({resultId:'record',sources:[],expiresAt:Date.now()+60000});dialog.props.onClose();
  composer(h.render()).props.onSubmit();
  assert.equal(h.c.sent[0].text,'Quoting:\n「Quoted passage」\n→ Reply: Question');assert.equal(h.c.sent[0].options.webSearch.resultId,'record');
  tree=h.render();composer(tree).props.setDraft('Next');composer(h.render()).props.onSubmit();
  assert.equal(h.c.sent[1].options.webSearch,undefined);
});
