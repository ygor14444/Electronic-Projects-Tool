@echo off
REM ============================================================
REM  instalar.bat
REM  Instala as dependencias do programa (python-docx).
REM  De um duplo clique neste arquivo uma unica vez, antes de
REM  usar o "abrir_programa.bat" pela primeira vez.
REM ============================================================

echo Procurando o Python instalado neste computador...
echo.

where python >nul 2>nul
if %errorlevel%==0 (
    echo Usando o comando "python"
    python -m pip install -r requirements.txt
    goto fim
)

where py >nul 2>nul
if %errorlevel%==0 (
    echo Usando o comando "py"
    py -m pip install -r requirements.txt
    goto fim
)

echo.
echo [ERRO] Nao foi encontrado nenhum Python instalado neste computador.
echo Instale o Python em https://www.python.org/downloads/ marcando a opcao
echo "Add python.exe to PATH" durante a instalacao, e rode este arquivo de novo.
echo.
pause
exit /b 1

:fim
echo.
echo ============================================================
echo Instalacao concluida! Agora abra o arquivo "abrir_programa.bat"
echo ============================================================
pause
