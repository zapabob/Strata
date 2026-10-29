#Requires -Version 5.1
<#
.SYNOPSIS
  Publish docs/ landing files to origin/gh-pages (manual fallback when Actions 422).

.PARAMETER DryRun
  Prepare the worktree and show status, but do not commit or push.

.NOTES
  Docs-only. Does not build NSIS/Tauri/cargo. No force-push.
#>
param(
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repo

$version = (Get-Content -Raw (Join-Path $repo "VERSION")).Trim()
if (-not $version) { throw "VERSION file empty" }

$work = Join-Path $env:TEMP ("strata-gh-pages-" + [guid]::NewGuid().ToString("n"))
$branch = "gh-pages"

Write-Host "Repo: $repo"
Write-Host "Product VERSION: $version"
Write-Host "Worktree: $work"

git fetch origin $branch
git worktree add $work "origin/$branch"
try {
  $dst = $work
  # Landing page at branch root (legacy gh-pages layout).
  Copy-Item (Join-Path $repo "docs\index.html") (Join-Path $dst "index.html") -Force
  New-Item -ItemType Directory -Force -Path (Join-Path $dst "assets") | Out-Null
  Copy-Item (Join-Path $repo "docs\assets\*") (Join-Path $dst "assets") -Recurse -Force
  Copy-Item (Join-Path $repo "docs\UPSTREAM_SYNC.txt") (Join-Path $dst "UPSTREAM_SYNC.txt") -Force
  if (Test-Path (Join-Path $repo "docs\PUBLISH_PAGES.md")) {
    Copy-Item (Join-Path $repo "docs\PUBLISH_PAGES.md") (Join-Path $dst "PUBLISH_PAGES.md") -Force
  }
  # Media referenced relatively from index (favicon).
  if (Test-Path (Join-Path $repo "docs\media\favicon.ico")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $dst "media") | Out-Null
    Copy-Item (Join-Path $repo "docs\media\favicon.ico") (Join-Path $dst "media\favicon.ico") -Force
  }

  Push-Location $dst
  try {
    git status -sb
    if ($DryRun) {
      Write-Host "DryRun: skipping commit/push."
      return
    }
    git add index.html assets UPSTREAM_SYNC.txt PUBLISH_PAGES.md media 2>$null
    $pending = git status --porcelain
    if (-not $pending) {
      Write-Host "Nothing to commit on gh-pages."
      return
    }
    $msg = "[Docs] refresh Pages for $version"
    git commit -m $msg
    git push origin "HEAD:$branch"
    Write-Host "Pushed gh-pages for $version"
  }
  finally {
    Pop-Location
  }
}
finally {
  git worktree remove --force $work 2>$null
  if (Test-Path $work) { Remove-Item -Recurse -Force $work }
}
