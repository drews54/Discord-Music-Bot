if (-Not (Get-InstalledModule Set-PsEnv -ErrorAction Ignore)) {
    Install-Module Set-PsEnv -Scope CurrentUser 
}
if (-Not (Get-Module -All Set-PsEnv -ErrorAction Ignore)) {
    Import-Module Set-PsEnv
}
Set-PsEnv
if (-Not (Test-Path Env:DISCORD_TOKEN -WarningAction SilentlyContinue)) {
    $Env:DISCORD_TOKEN = 'PASTE_TOKEN_HERE'
}
if (-Not (Test-Path Env:DISCORD_PREFIXES -WarningAction SilentlyContinue)) {
    $Env:DISCORD_PREFIX = 'TYPE_PREFIX_HERE'
}
if (-Not (Test-Path Env:LANG -WarningAction SilentlyContinue)) {
    $Env:LANG = 'EN_or_RU'
}
python bot.py
Pause