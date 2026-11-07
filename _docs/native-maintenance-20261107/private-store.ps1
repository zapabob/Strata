param([ValidateSet('Init','Verify','SealMockTests')][string]$Mode = 'Verify')
$ErrorActionPreference = 'Stop'
$root = 'H:\Strata\private-backups\native-maintenance-20261107'
$check = 'initialization'
try {
    $sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $parent = [System.IO.DirectoryInfo](Split-Path -Parent $root)
    if (-not $parent.Exists) { throw 'parent' }
    for ($p = $parent; $null -ne $p; $p = $p.Parent) {
        if (($p.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'reparse' }
    }
    if ($Mode -eq 'Init') {
        if (Test-Path -LiteralPath $root) { throw 'not fresh' }
        $acl = New-Object System.Security.AccessControl.DirectorySecurity
        $acl.SetOwner($sid)
        $acl.SetAccessRuleProtection($true, $false)
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
        $acl.AddAccessRule($rule)
        # Create with its DACL, before any private bytes are written.
        [IO.Directory]::CreateDirectory($root, $acl) | Out-Null
    }
    if ($Mode -eq 'SealMockTests') {
        # Python's pytest temp directories can explicitly grant SYSTEM/Administrators.
        # These contain synthetic fixtures only. Tighten just these owned test trees;
        # never repair or silently accept a changed ACL on operational evidence.
        $testRoots = @(Get-ChildItem -LiteralPath $root -Directory -Force | Where-Object { $_.Name -match '^mock-tests-[0-9]+$' })
        foreach ($testRoot in $testRoots) {
            $check = 'enumerating_mock_tree'
            $testItems = @($testRoot) + @(Get-ChildItem -LiteralPath $testRoot.FullName -Force -Recurse)
            foreach ($item in $testItems) {
                $check = 'mock_reparse'
                if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'mock reparse' }
                $check = 'creating_mock_acl'
                $acl = Get-Acl -LiteralPath $item.FullName
                $acl.SetAccessRuleProtection($true, $false)
                foreach ($oldRule in @($acl.GetAccessRules($true,$false,[System.Security.Principal.SecurityIdentifier]))) {
                    $acl.RemoveAccessRuleSpecific($oldRule)
                }
                if ($item.PSIsContainer) {
                    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
                } else {
                    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid,'FullControl','Allow')
                }
                $check = 'mock_owner'
                if ($acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value -ne $sid.Value) { throw 'unexpected mock owner' }
                $acl.AddAccessRule($rule)
                $check = 'sealing_mock_acl'
                $item.SetAccessControl($acl)
            }
        }
    }
    $items = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Force -Recurse)
    foreach ($item in $items) {
        $check = 'reparse'
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'reparse' }
        $acl = Get-Acl -LiteralPath $item.FullName
        $check = 'owner'
        if ($acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value -ne $sid.Value) { throw 'owner' }
        $rules = @($acl.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier]))
        $check = 'dacl'
        if ($rules.Count -ne 1 -or $rules[0].IdentityReference.Value -ne $sid.Value -or
            $rules[0].AccessControlType -ne 'Allow' -or $rules[0].FileSystemRights -ne 'FullControl') { throw 'dacl' }
    }
    $check = 'inheritance'
    if (-not (Get-Acl -LiteralPath $root).AreAccessRulesProtected) { throw 'inheritance' }
    '{"ok":true,"ownerOnly":true}'
} catch {
    # Do not interpolate exceptions or paths derived from private state.
    [pscustomobject]@{ok=$false;code='private_store_acl_failed';check=$check;errorType=$_.Exception.GetType().Name} | ConvertTo-Json -Compress
    exit 1
}
