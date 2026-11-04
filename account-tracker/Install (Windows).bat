@echo off
setlocal
rem Creates "Account Tracker" shortcuts on the Desktop and in the Start Menu that
rem open the tracker in its own app window (no tabs or address bar), then opens it.

set "HTML=%~dp0index.html"
set "URL=file:///%HTML:\=/%"

set "BROWSER="
for %%B in (
  "%ProgramFiles%\Google\Chrome\Application\chrome.exe"
  "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
  "%LocalAppData%\Google\Chrome\Application\chrome.exe"
  "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
  "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
) do if not defined BROWSER if exist %%B set "BROWSER=%%~B"

if not defined BROWSER (
  echo Could not find Google Chrome or Microsoft Edge. Opening in your default browser instead.
  start "" "%HTML%"
  pause
  exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "foreach ($dir in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {" ^
  "  $s = $ws.CreateShortcut((Join-Path $dir 'Account Tracker.lnk'));" ^
  "  $s.TargetPath = $env:BROWSER;" ^
  "  $s.Arguments = '--app=' + [char]34 + $env:URL + [char]34;" ^
  "  $s.Description = 'Account Tracker';" ^
  "  $s.Save() }"

start "" "%BROWSER%" --app="%URL%"
echo.
echo Done. "Account Tracker" is now on your Desktop and in the Start Menu.
echo Tip: right-click it in the taskbar while it's open and choose "Pin to taskbar".
echo If you move this folder, run this installer again.
timeout /t 8 >nul
