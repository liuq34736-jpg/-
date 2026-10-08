function Resolve-LocalNode {
    $candidates = @()
    $command = Get-Command node -ErrorAction SilentlyContinue
    if ($command) { $candidates += $command.Source }
    $profileDir = [Environment]::GetFolderPath('UserProfile')
    $candidates += (Join-Path $profileDir '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe')
    $candidates += (Join-Path $env:ProgramFiles 'nodejs\node.exe')
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $candidate) {
            $version = & $candidate --version 2>$null
            if ($LASTEXITCODE -eq 0 -and $version -match '^v24\.') { return (Resolve-Path -LiteralPath $candidate).Path }
        }
    }
    throw '未找到兼容的 Node 24。请安装 Node 24 或恢复现有本机 Node 文件。'
}

function Get-LocalServiceState($ProjectRoot, $ServiceName) {
    $stateFile = Join-Path $ProjectRoot ("runtime\service-$ServiceName.json")
    if (!(Test-Path -LiteralPath $stateFile)) { return $null }
    try { return (Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json) }
    catch { return $null }
}

function Get-LocalServiceLauncher($ProjectRoot, $State) {
    if (!$State -or $State.root -ne $ProjectRoot -or $State.instance_id -notmatch '^[a-f0-9]{32}$') { return $null }
    $launcher = Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$State.launcher_pid)" -ErrorAction SilentlyContinue
    $helperPath = Join-Path $ProjectRoot 'scripts\local-service.py'
    if ($launcher -and $launcher.CommandLine -and $launcher.CommandLine.Contains($helperPath) -and $launcher.CommandLine.Contains($State.instance_id)) { return $launcher }
    return $null
}

function Test-LocalPortOwner($ProjectRoot, $State, $OwnerId) {
    $launcher = Get-LocalServiceLauncher $ProjectRoot $State
    if (!$launcher) { return $false }
    $currentId = [int]$OwnerId
    for ($level = 0; $level -lt 8; $level++) {
        if ($currentId -eq [int]$launcher.ProcessId) { return $true }
        $current = Get-CimInstance Win32_Process -Filter "ProcessId = $currentId" -ErrorAction SilentlyContinue
        if (!$current -or !$current.ParentProcessId -or $current.ParentProcessId -eq $currentId) { return $false }
        $currentId = [int]$current.ParentProcessId
    }
    return $false
}

function Stop-LocalServiceState($ProjectRoot, $State) {
    $launcher = Get-LocalServiceLauncher $ProjectRoot $State
    if (!$launcher) { return }
    # Enumerate only descendants of the validated, instance-specific launcher.
    $allProcesses = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, CreationDate)
    $owned = @($launcher)
    $parentIds = @([int]$launcher.ProcessId)
    for ($level = 0; $level -lt 8 -and $parentIds.Count -gt 0; $level++) {
        $children = @($allProcesses | Where-Object { $parentIds -contains [int]$_.ParentProcessId })
        $owned += $children
        $parentIds = @($children | ForEach-Object { [int]$_.ProcessId })
    }
    [array]::Reverse($owned)
    foreach ($entry in $owned) {
        $live = Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$entry.ProcessId)" -ErrorAction SilentlyContinue
        if ($live -and $live.CreationDate -eq $entry.CreationDate) {
            Stop-Process -Id ([int]$entry.ProcessId) -ErrorAction SilentlyContinue
        }
    }
}
