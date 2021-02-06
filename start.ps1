if (-Not (Get-InstalledModule Set-PsEnv -ErrorAction Ignore)) {
    Install-Module Set-PsEnv -Scope CurrentUser 
}
if (-Not (Get-Module -All Set-PsEnv -ErrorAction Ignore)) {
    Import-Module Set-PsEnv
}
Set-PsEnv
if (-Not (Test-Path Env:DISCORD_TOKEN -WarningAction SilentlyContinue)) {
    $Env:DISCORD_TOKEN = 'PASTE_YOUR_TOKEN_HERE'
}
if (-Not (Test-Path Env:DISCORD_PREFIXES -WarningAction SilentlyContinue)) {
    $Env:DISCORD_PREFIXES = 'TYPE_PREFIXES_HERE'
}
python bot.py
Pause