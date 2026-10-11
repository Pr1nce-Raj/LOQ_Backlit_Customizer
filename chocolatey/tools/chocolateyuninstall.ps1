$ErrorActionPreference = 'Stop';
$packageName = 'lenovo-loq-backlight-customizer'
$localApp = [System.IO.Path]::Combine($env:LOCALAPPDATA, 'Programs', 'LenovoLOQBacklightCustomizer', 'uninstall.exe')

if (Test-Path $localApp) {
    Start-Process -FilePath $localApp -ArgumentList '--quiet' -Wait
}
