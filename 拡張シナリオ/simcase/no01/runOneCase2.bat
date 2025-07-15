@echo off
setlocal

rem ��������CASE��RAND���󂯎��
set CASE=%1
set RAND=%2

rem RAND_SHORT �� "r" + RAND��4�����ڈȍ~�i��: rand20 �� r20�j
set RAND_SHORT=r%RAND:~4%

rem �p�X�ݒ�i�����ɕK���o�b�N�X���b�V���j
set BASEDIR=D:\.shortcut-targets-by-id\1jDNc8Uk8iSfSVyDhM6LkgxOdCfRWaj9h\Hatakenaka-Hibiki\ITL??_20240826_\??????\
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
set OUTCSV=%CONVERT%vpos_no%CASE%_r%RAND_SHORT%_ext.csv
set OUTZIP=%CONVERT%vpos_no%CASE%_r%RAND_SHORT%.zip

if not exist "%VPOSSRC%" (
    echo [ERROR] vpos.csv not found in %RANDCASE%
    exit /b 1
)

pushd "%BIN%"
RecordExtraction.exe "%RANDCASE%" vpos.csv "%CONVERT%" "%VPOSDST%"
popd


del "%VPOSSRC%"

powershell Compress-Archive -Path "%OUTCSV%" -DestinationPath "%OUTZIP%" -Force

del "%OUTCSV%"

echo === Completed: %CASE% %RAND% ===

exit /b 0
