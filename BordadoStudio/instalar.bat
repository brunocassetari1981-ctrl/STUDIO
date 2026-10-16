@echo off
rem ============================================================
rem  BordadoStudio - Instalador
rem  Abre apenas a caixinha "Instalando..." (sem janela de console).
rem  Depuracao: use instalar_console.bat
rem ============================================================
start "" wscript.exe "%~dp0instalar.vbs"
exit /b 0
