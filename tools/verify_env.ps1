$machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
$user = [Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = "$user;$machine"

$cmd = Get-Command "strata.cmd" -ErrorAction SilentlyContinue
if ($cmd) {
    Write-Host "Found strata.cmd at:" $cmd.Path
    & $cmd.Path --version
} else {
    Write-Host "strata.cmd not found in PATH."
}
