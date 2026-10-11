$ErrorActionPreference = 'Stop';
$packageName = 'lenovo-loq-backlight-customizer'
$toolsDir    = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url64       = 'https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer/releases/download/v1.0.1/Lenovo_LOQ_Backlight_Customizer_Setup.exe'
$checksum64  = '7BD3DC74D2B4AA437BF7AC1FFA0A38E5BAD12F67B1CA81B4D9D3193DECCFD02B'

$packageArgs = @{
  packageName   = $packageName
  fileType      = 'exe'
  url64bit      = $url64
  silentArgs    = '--silent'
  validExitCodes= @(0)
  checksum64    = $checksum64
  checksumType64= 'sha256'
}

Install-ChocolateyPackage @packageArgs
