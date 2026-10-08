$ErrorActionPreference = 'Stop'
$platformRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'local-runtime.ps1')
$runtimeDir = Join-Path $platformRoot 'runtime'
$pythonPath = Join-Path $platformRoot '.venv\Scripts\python.exe'
$vitePath = Join-Path $platformRoot 'frontend\node_modules\vite\bin\vite.js'
$helperPath = Join-Path $PSScriptRoot 'local-service.py'
$created = @()
try {
    if (!(Test-Path -LiteralPath $pythonPath) -or !(Test-Path -LiteralPath $vitePath)) {
        throw '依赖尚未安装，请先按 docs/LOCAL_START.md 完成安装。'
    }
    $nodePath = Resolve-LocalNode
    & $pythonPath -X utf8 -c 'import fastapi, uvicorn' 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Python虚拟环境依赖不完整，请按 docs/LOCAL_START.md 修复。' }
    $services = @(@{ name = 'backend'; port = 8765 }, @{ name = 'frontend'; port = 5173 })
    $needsStart = @()
    foreach ($service in $services) {
        $listeners = @(Get-NetTCPConnection -LocalPort $service.port -State Listen -ErrorAction SilentlyContinue)
        $state = Get-LocalServiceState $platformRoot $service.name
        if ($listeners.Count -eq 0) { $needsStart += $service; continue }
        foreach ($listener in $listeners) {
            if ($listener.LocalAddress -ne '127.0.0.1' -or !(Test-LocalPortOwner $platformRoot $state $listener.OwningProcess)) {
                throw "本地端口 $($service.port) 被其他程序占用；本程序不会终止其他程序，也不会更换端口。"
            }
        }
    }
    New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
    @{ node_path = $nodePath } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeDir 'toolchain.json') -Encoding UTF8
    foreach ($service in $needsStart) {
        $instanceId = [guid]::NewGuid().ToString('N')
        $startupInfo = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }
        $commandLine = '"' + $pythonPath + '" -X utf8 "' + $helperPath + '" ' + $service.name + ' --instance-id ' + $instanceId
        # WMI owns these hidden processes, not the short-lived terminal job.
        $launch = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $commandLine; CurrentDirectory = $platformRoot; ProcessStartupInformation = $startupInfo }
        if ($launch.ReturnValue -ne 0) { throw "无法启动本地服务（Windows错误码 $($launch.ReturnValue)）。" }
        $created += [PSCustomObject]@{ root = $platformRoot; service = $service.name; instance_id = $instanceId; launcher_pid = $launch.ProcessId }
    }
    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        try {
            $allOwned = $true
            foreach ($service in $services) {
                $state = Get-LocalServiceState $platformRoot $service.name
                $listener = Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $service.port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
                if (!$listener -or !(Test-LocalPortOwner $platformRoot $state $listener.OwningProcess)) { $allOwned = $false; break }
            }
            if ($allOwned) {
                $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/v1/health' -TimeoutSec 1
                $web = Invoke-WebRequest -Uri 'http://127.0.0.1:5173/' -UseBasicParsing -TimeoutSec 1
                if ($health.status -eq 'ok' -and $health.mode -eq 'preview' -and $web.StatusCode -eq 200) { $ready = $true; break }
            }
        } catch { }
        Start-Sleep -Milliseconds 400
    }
    if (!$ready) { throw '服务启动超时；请查看本项目日志。' }
    $backendState = Get-LocalServiceState $platformRoot 'backend'
    $frontendState = Get-LocalServiceState $platformRoot 'frontend'
    @{ backend_pid = $backendState.child_pid; frontend_pid = $frontendState.child_pid; root = $platformRoot; launcher_version = 2 } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeDir 'processes.json') -Encoding UTF8
    if ($needsStart.Count -eq 0) { Write-Output '本地预览已在运行，无需重复启动。' }
    Write-Output '网页：http://127.0.0.1:5173/'
    Write-Output '后端：http://127.0.0.1:8765/api/v1/health'
    Write-Output '仅监听本机；服务独立后台运行，关闭启动窗口后仍可访问。'
} catch {
    foreach ($state in $created) { Stop-LocalServiceState $platformRoot $state }
    Write-Output ('启动未完成：' + $_.Exception.Message)
    exit 1
}
