@echo off
setlocal

rem 引数からCASEとRANDを受け取る
set CASE=%1
set RAND=%2

rem RAND_SHORT は "r" + RANDの4文字目以降（例: rand20 → r20）
set RAND_SHORT=r%RAND:~4%

rem パス設定（末尾に必ずバックスラッシュ）
set BASEDIR=G:\.shortcut-targets-by-id\1jDNc8Uk8iSfSVyDhM6LkgxOdCfRWaj9h\Hatakenaka-Hibiki\ITL納品_20240826_\拡張シナリオ\
set BIN=%BASEDIR%bin\
set RANDCASE=%BASEDIR%simcase\%CASE%\%RAND%\
set CONVERT=%BASEDIR%convert\%CASE%\

set CASEFILE=Case1_%CASE%_%RAND_SHORT%

echo CASEFILE: %CASEFILE%
echo RANDCASE : %RANDCASE%

echo === Running simulation for %CASE% %RAND% ===
"%BIN%itlts.exe" -v -mode mav -csv "%RAND%\%CASEFILE%" -casepfx "%CASEFILE%" -caseext .mavn


set VPOSSRC=%RANDCASE%vpos.csv
set VPOSDST=%CONVERT%vpos_%CASE%_%RAND_SHORT%.csv
set OUTZIP=%CONVERT%vpos_%CASE%_%RAND_SHORT%.zip

if not exist "%VPOSSRC%" (
    echo [ERROR] vpos.csv not found in %RANDCASE%
    exit /b 1
)

rem RecordExtraction.exe も絶対パスで実行
"%BIN%RecordExtraction.exe" "%RANDCASE%" vpos.csv "%CONVERT%" "%VPOSDST%"

if errorlevel 1 (
    echo [ERROR] RecordExtraction.exe failed
    exit /b 1
)

rem 元の vpos.csv を削除
del /Q "%VPOSSRC%"

rem PowerShellで圧縮（ダブルクォートに変更）
powershell -Command "Compress-Archive -Path \"%VPOSDST%\" -DestinationPath \"%OUTZIP%\" -Force"

if errorlevel 1 (
    echo [ERROR] Compress-Archive failed
    exit /b 1
)

rem 圧縮後に CSV を削除
del /Q "%VPOSDST%"

echo === Completed: %CASE% %RAND% ===

exit /b 0