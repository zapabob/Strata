$srcDist = "apps\host\dist"
$dstDist = "C:\Users\downl\AppData\Local\Programs\Strata\host\dist"
Copy-Item -Path "$srcDist\*" -Destination $dstDist -Recurse -Force

$srcServer = "apps\host\server"
$dstServer = "C:\Users\downl\AppData\Local\Programs\Strata\host\server"
Copy-Item -Path "$srcServer\*" -Destination $dstServer -Recurse -Force

Write-Host "DEPLOY_HOST_SUCCESS: Fully synchronized host dist and server"
