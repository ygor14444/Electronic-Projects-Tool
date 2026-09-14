@echo off
REM ============================================================
REM  abrir_programa.bat
REM  Abre a Ferramenta de Orcamento de Projetos.
REM  Antes de usar pela primeira vez, rode o "instalar.bat".
REM ============================================================

where python >nul 2>nul
if %errorlevel%==0 (
    python main.py
    goto fim
)

where py >nul 2>nul
if %errorlevel%==0 (
    py main.py
    goto fim
)

echo.
echo [ERRO] Nao foi encontrado nenhum Python instalado neste computador.
echo Instale o Python em https://www.python.org/downloads/ marcando a opcao
echo "Add python.exe to PATH" durante a instalacao.
echo.
pause
exit /b 1

:fim
if errorlevel 1 (
    echo.
    echo O programa fechou com um erro. Veja a mensagem acima.
    pause
)
