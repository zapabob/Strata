# Read-only verification of an explicitly approved patch against the base commit.
function Assert-BonsaiSourcePatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$BaseCommit,
        [Parameter(Mandatory)][string]$PatchPath,
        [Parameter(Mandatory)][string]$OutputPath
    )
    $actualCommit = (& git -C $Source rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $actualCommit -ne $BaseCommit) { throw 'Patched worktree revision mismatch.' }
    $untracked = @(& git -C $Source ls-files --others --exclude-standard)
    if ($LASTEXITCODE -ne 0 -or $untracked.Count) { throw 'Patched worktree has unexpected untracked files.' }
    # HEAD is essential: an unstaged-only diff would hide staged tracked changes.
    & git -C $Source diff HEAD --binary --full-index --no-ext-diff --src-prefix=a/ --dst-prefix=b/ "--output=$OutputPath"
    if ($LASTEXITCODE -ne 0) { throw 'Failed to compare patched worktree against its base commit.' }
    $expected = (Get-FileHash -LiteralPath $PatchPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $actual = (Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw 'Patched worktree differs from the exact recorded patch; existing work is preserved.' }
    return $actual
}
