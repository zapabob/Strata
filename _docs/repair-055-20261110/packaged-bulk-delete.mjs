/** Bulk history deletion in the caller's real, isolated packaged WebView2. */
import assert from 'node:assert/strict';
import {mkdirSync,readFileSync} from 'node:fs';
import {join} from 'node:path';

export async function packagedBulkDelete({page,request,home,workspace}){
  const otherPath=join(home,'bulk-other-workspace');mkdirSync(otherPath);
  const other=await request('/api/workspaces','POST',{path:otherPath});
  const session=(id,path,archived=false)=>({id,title:id,workspace:path,archived,messages:[],
    createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()});
  const target=Array.from({length:26},(_,n)=>session('bulk-packaged-'+n,workspace.path,n===25));
  const preserved=session('bulk-packaged-other',other.path);
  const imported=await request('/api/chats/import','POST',{sessions:[...target,preserved]});
  assert.equal(imported.failed.length,0);
  await page.reload();
  const rows=(await request('/api/chats')).chats;
  const stored=await Promise.all(rows.map(row=>request('/api/chats/'+encodeURIComponent(row.id))));
  const ids=new Set(stored.filter(row=>row.session.workspace===workspace.path||workspace.aliases?.includes(row.session.workspace)).map(row=>row.session.id));
  assert.ok(ids.size>=26);
  const group=page.locator('.ws__group').filter({has:page.getByRole('button',{name:workspace.name,exact:true})});
  const open=async()=>{await group.locator('.workspace-menu-trigger').click();await page.getByRole('menuitem',{name:'Delete all chats in folder',exact:true}).click();const dialog=page.getByRole('dialog',{name:'Delete all chats in folder?',exact:true});await dialog.getByRole('button',{name:`Delete ${ids.size} chats`,exact:true}).waitFor();return dialog;};
  let dialog=await open();await dialog.getByRole('button',{name:'Cancel',exact:true}).click();
  const afterCancel=new Set((await request('/api/chats')).chats.map(row=>row.id));
  assert.ok([...ids].every(id=>afterCancel.has(id)),'Cancellation removed a chat');
  dialog=await open();
  const later=session('bulk-packaged-later',workspace.path);
  assert.equal((await request('/api/chats/import','POST',{sessions:[later]})).failed.length,0);
  await dialog.getByRole('button',{name:`Delete ${ids.size} chats`,exact:true}).click();await dialog.waitFor({state:'hidden'});
  await page.reload();
  const remaining=new Set((await request('/api/chats')).chats.map(row=>row.id));
  assert.ok([...ids].every(id=>!remaining.has(id)),'A confirmed chat returned after reload');
  assert.ok(remaining.has(preserved.id),'Another folder was deleted');
  assert.ok(remaining.has(later.id),'A chat created after confirmation was deleted');
  assert.equal(readFileSync(join(home,'workspace/qa-existing-note.md'),'utf8'),'External editor change retained.');
  return {ok:true,noMocks:true,isolatedWorkspace:true,confirmedChats:ids.size,
    checks:['bulk-delete-beyond-20-including-archive','bulk-cancel-preserves-history',
      'bulk-keeps-other-folder-and-later-chat','bulk-durable-after-reload-and-files-retained']};
}
