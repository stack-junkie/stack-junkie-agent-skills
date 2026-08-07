@echo off
setlocal

where py >nul 2>nul
if not errorlevel 1 goto use_py

python %*
exit /b %ERRORLEVEL%

:use_py
py -3 %*
exit /b %ERRORLEVEL%
