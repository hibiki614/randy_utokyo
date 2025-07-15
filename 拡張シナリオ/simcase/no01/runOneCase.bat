@echo off
setlocal

rem ��������CASE��RAND���󂯎��
set CASE=%1
set RAND=%2

rem RAND_SHORT �� "r" + RAND��4�����ڈȍ~�i��: rand20 �� r20�j
set RAND_SHORT=r%RAND:~4%

rem �p�X�ݒ�i�����ɕK���o�b�N�X���b�V���j
set BASEDIR=G:\.shortcut-targets-by-id\1jDNc8Uk8iSfSVyDhM6LkgxOdCfRWaj9h\Hatakenaka-Hibiki\ITL�[�i_20240826_\�g���V�i���I\
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

rem RecordExtraction.exe ����΃p�X�Ŏ��s
"%BIN%RecordExtraction.exe" "%RANDCASE%" vpos.csv "%CONVERT%" "%VPOSDST%"

if errorlevel 1 (
    echo [ERROR] RecordExtraction.exe failed
    exit /b 1
)

rem ���� vpos.csv ���폜
del /Q "%VPOSSRC%"

rem PowerShell�ň��k�i�_�u���N�H�[�g�ɕύX�j
powershell -Command "Compress-Archive -Path \"%VPOSDST%\" -DestinationPath \"%OUTZIP%\" -Force"

if errorlevel 1 (
    echo [ERROR] Compress-Archive failed
    exit /b 1
)

rem ���k��� CSV ���폜
del /Q "%VPOSDST%"

echo === Completed: %CASE% %RAND% ===

exit /b 0