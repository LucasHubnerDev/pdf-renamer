@echo off
REM ============================================================
REM  Build do PDFRenamer.exe
REM  Requisitos nesta maquina: Python 3.10+, Tesseract (com
REM  portugues) e Poppler instalados conforme o README.
REM ============================================================

REM Cria o ambiente e instala as dependencias na primeira execucao
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --onefile --windowed --name PDFRenamer ^
  --collect-all customtkinter ^
  --add-binary "C:\Program Files\Tesseract-OCR\*;tesseract" ^
  --add-data "C:\Program Files\Tesseract-OCR\tessdata\por.traineddata;tesseract\tessdata" ^
  --add-binary "C:\poppler\poppler-*\Library\bin\*;poppler\bin" ^
  main_gui.py

echo.
echo ============================================================
echo  Executavel gerado em dist\PDFRenamer.exe
echo ============================================================
pause