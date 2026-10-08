$ErrorActionPreference = 'Stop'
$platformRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'local-runtime.ps1')
foreach ($serviceName in @('frontend', 'backend')) {
    $state = Get-LocalServiceState $platformRoot $serviceName
    if ($state) { Stop-LocalServiceState $platformRoot $state }
}
Write-Output '本项目本地预览已停止；不会终止其他程序。'
