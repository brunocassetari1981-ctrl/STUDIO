@echo off
chcp 65001 >nul
setlocal
title BordadoStudio - Instalador (console)
cd /d "%~dp0"

echo.
echo  ============================================
echo     BordadoStudio - Instalador (console)
echo     (sem login, sem ativacao, sem limites)
echo  ============================================
echo.

rem --- procura o Python ---
set PY=
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo  [ERRO] Python nao encontrado neste computador.
    echo.
    echo  1^) Baixe o Python em: https://www.python.org/downloads/
    echo  2^) Na instalacao, MARQUE a opcao "Add Python to PATH"
    echo  3^) Execute este instalador novamente.
    echo.
    pause
    exit /b 1
)

echo  [1/3] Criando ambiente virtual...
%PY% -m venv .venv
if errorlevel 1 (
    echo  [ERRO] Falha ao criar o ambiente virtual.
    pause
    exit /b 1
)

echo  [2/3] Instalando componentes ^(pode levar 1-2 minutos^)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo  [ERRO] Falha ao instalar. Verifique sua conexao com a internet.
    pause
    exit /b 1
)

echo  [3/3] Criando atalho de inicializacao...
> "Abrir BordadoStudio.bat" (
    echo @echo off
    echo cd /d "%%~dp0"
    echo if not exist ".venv\Scripts\pythonw.exe" goto :naoinstalado
    echo start "" ".venv\Scripts\pythonw.exe" main.py
    echo exit /b 0
    echo :naoinstalado
    echo echo Execute o instalar.bat primeiro.
    echo pause
)

echo.
echo  ============================================
echo    Instalacao concluida!
echo.
echo    Para usar: clique duas vezes em
echo    "Abrir BordadoStudio.bat"
echo  ============================================
echo.
pause
exit /b 0
