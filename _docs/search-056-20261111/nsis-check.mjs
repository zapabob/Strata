import { spawnSync } from 'node:child_process';
if(!process.argv[2])throw new Error('Pass the observed PowerShell 7 executable path.');
const result=spawnSync(process.argv[2],['-NoProfile','-NonInteractive','-File','C:/Users/downl/Documents/ChatGPT/Strata/tools/test_nsis_upgrade.ps1','-OutputDir','H:/Strata/releases/search-056-20261111-codex/nsis-fixtures-r3'],{stdio:'inherit',windowsHide:true});
if(result.error)throw result.error;
process.exitCode=result.status??1;
