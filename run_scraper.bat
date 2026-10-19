@echo off
REM Double-click to install the libraries and run the scraper on Windows.
REM All output is also written to run_log.txt in this folder.
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo Run started %date% %time% > run_log.txt

set "PY="
py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
if not defined PY (
    python -c "import sys" >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo NO_PYTHON >> run_log.txt
    echo Python was not found on this computer. Install it from python.org and run this file again.
    pause
    exit /b 1
)

%PY% --version >> run_log.txt 2>&1
echo Installing libraries...
%PY% -m pip install --user --disable-pip-version-check -q -r requirements.txt >> run_log.txt 2>&1
echo Scraping books.toscrape.com, this takes about a minute...
%PY% bookstore_scraper.py >> run_log.txt 2>&1
echo EXIT_CODE %errorlevel% >> run_log.txt
echo Done. Results are in competitor_books.csv and run_log.txt. You can close this window.
