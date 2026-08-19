@echo off
setlocal

where py >nul 2>nul
if errorlevel 1 goto use_python

py -3 %*
exit /b %ERRORLEVEL%

:use_python
python %*
exit /b %ERRORLEVEL%
