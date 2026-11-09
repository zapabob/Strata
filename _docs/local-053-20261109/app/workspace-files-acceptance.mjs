/** Actual sidebar CRUD in the caller's isolated real WebView2; never operates on a user's workspace. */
import assert from 'node:assert/strict';
import {existsSync,readFileSync,writeFileSync} from 'node:fs';
import {join,resolve} from 'node:path';

export async function workspaceFilesAcceptance({getPage,request,home,language,modelScreen}){
 const page=getPage(),expected=join(home,'workspace'),oldName='qa-existing-note.md';
 const roots=(await request('/api/workspaces')).workspaces;
 const workspace=roots.find(item=>resolve(item.path).toLowerCase()===resolve(expected).toLowerCase());
 assert.ok(workspace,'No isolated workspace registered');
 assert.equal(readFileSync(join(expected,oldName),'utf8'),'Isolated workspace file acceptance fixture.\n');
 const checks=[],created='qa-created-note.md',renamed='qa-renamed-note.md';
 assert.equal(existsSync(join(expected,created)),false);assert.equal(existsSync(join(expected,renamed)),false);
 await page.setViewportSize({width:1600,height:1000});
 // The profile contains one explicitly isolated workspace. Pick by the registered name, not global filesystem roots.
 const section=page.getByRole('region',{name:`Files in ${workspace.name}`,exact:true});
 const toggle=section.locator('.workspace-files__toggle');
 if(await toggle.getAttribute('aria-expanded')!=='true')await toggle.click();
 await section.getByRole('button',{name:oldName,exact:true}).click();
 let dialog=page.getByRole('dialog',{name:`File: ${oldName}`,exact:true});
 await dialog.getByRole('textbox',{name:'File contents',exact:true}).fill('Edited through the installed sidebar.\n');
 await page.setViewportSize({width:1100,height:900});await dialog.getByRole('textbox',{name:'File contents',exact:true}).waitFor();
 await page.setViewportSize({width:1600,height:1000});
 await dialog.getByRole('button',{name:'Save',exact:true}).click();await dialog.getByText('Unsaved changes',{exact:true}).waitFor({state:'hidden'});
 assert.equal(readFileSync(join(expected,oldName),'utf8'),'Edited through the installed sidebar.\n');
 await dialog.getByRole('button',{name:'Close',exact:true}).click();checks.push('existing-file-edit-and-resize');
 await section.getByRole('button',{name:'New file',exact:true}).click();dialog=page.getByRole('dialog',{name:'New file',exact:true});
 await dialog.getByRole('textbox',{name:'File or folder name',exact:true}).fill(created);
 const content='Saved text, not executable HTML: <script>window.__workspaceExecution=true</script>';
 await dialog.getByRole('textbox',{name:'File contents',exact:true}).fill(content);await dialog.getByRole('button',{name:'Save',exact:true}).click();await dialog.waitFor({state:'hidden'});
 assert.equal(readFileSync(join(expected,created),'utf8'),content);assert.equal(await page.evaluate(()=>window.__workspaceExecution),undefined);checks.push('create-text-no-html-execution');
 await section.getByRole('button',{name:`Rename ${created}`,exact:true}).click();dialog=page.getByRole('dialog',{name:'Rename item',exact:true});
 await dialog.getByRole('textbox',{name:'File or folder name',exact:true}).fill(renamed);await dialog.getByRole('button',{name:'Save',exact:true}).click();await dialog.waitFor({state:'hidden'});
 assert.equal(existsSync(join(expected,created)),false);assert.equal(readFileSync(join(expected,renamed),'utf8'),content);checks.push('rename-preserves-content');
 await section.getByRole('button',{name:`Move ${renamed} to trash`,exact:true}).click();dialog=page.getByRole('dialog',{name:'Move to workspace trash?',exact:true});
 await dialog.getByRole('button',{name:'Move to trash',exact:true}).click();await dialog.waitFor({state:'hidden'});assert.equal(existsSync(join(expected,renamed)),false);
 await section.getByRole('button',{name:'Undo',exact:true}).click();await section.getByRole('button',{name:renamed,exact:true}).waitFor();assert.equal(readFileSync(join(expected,renamed),'utf8'),content);checks.push('reversible-trash-no-content-loss');
 await section.getByRole('button',{name:'New folder',exact:true}).click();dialog=page.getByRole('dialog',{name:'New folder',exact:true});
 await dialog.getByRole('textbox',{name:'File or folder name',exact:true}).fill('qa-old-folder');await dialog.getByRole('button',{name:'Save',exact:true}).click();await dialog.waitFor({state:'hidden'});
 await section.getByRole('button',{name:'qa-old-folder',exact:true}).click();await section.getByText('This folder is empty.',{exact:true}).waitFor();await section.getByRole('button',{name:'Parent folder',exact:true}).click();checks.push('folder-create-and-navigation');
 await section.getByRole('button',{name:oldName,exact:true}).click();dialog=page.getByRole('dialog',{name:`File: ${oldName}`,exact:true});
 await dialog.getByRole('textbox',{name:'File contents',exact:true}).fill('A stale edit must not replace an external change.');
 writeFileSync(join(expected,oldName),'External editor change retained.');await dialog.getByRole('button',{name:'Save',exact:true}).click();await dialog.getByRole('alert').waitFor();
 assert.equal(readFileSync(join(expected,oldName),'utf8'),'External editor change retained.');await dialog.getByRole('button',{name:'Discard changes',exact:true}).click();checks.push('external-edit-conflict-preserved');
 await language('ja');await page.setViewportSize({width:430,height:900});
 const navigation=page.getByRole('button',{name:/ナビゲーション/}).first();await navigation.waitFor();await navigation.click();
 const mobile=page.locator('.workspace-files').first(),mobileToggle=mobile.locator('.workspace-files__toggle');await mobileToggle.waitFor();assert.match(await mobileToggle.innerText(),/ファイル/);await mobileToggle.click();
 await mobile.getByRole('button',{name:oldName,exact:true}).click();await page.getByRole('textbox',{name:'ファイルの内容',exact:true}).waitFor();
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:join(home,'screenshots/workspace-files-japanese-mobile.png')});
 await page.keyboard.press('Escape');await page.getByRole('dialog',{name:/ファイル：/}).waitFor({state:'hidden'});checks.push('japanese-mobile-keyboard');
 await page.setViewportSize({width:1600,height:1000});await language('en');await modelScreen();
 return {ok:true,noMocks:true,isolatedWorkspace:true,checks};
}
