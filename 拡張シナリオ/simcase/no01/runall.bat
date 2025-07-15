@echo off
setlocal 

:: ==== シナリオ番号を設定 ====
set CASE=no01

:: ==== 乱数リスト ====
set RAND_LIST1=rand01 rand02 rand03 rand04 rand05   
set RAND_LIST2=rand06 rand07 rand08 rand09 rand10
set RAND_LIST3=rand11 rand12 rand13 rand14 rand15
set RAND_LIST4=rand16 rand17 rand18 rand19 rand20

:: ==== 各フォルダにある ProcessOne.bat を並列に実行 ====
for %%A in (%RAND_LIST1%) do (
    start "" "%~dp0runOneCase.bat" %CASE% %%A
    timeout /t 1 > nul
)

for %%B in (%RAND_LIST2%) do (
    start "" "%~dp0runOneCase.bat" %CASE% %%B
    timeout /t 1 > nul
)

for %%C in (%RAND_LIST3%) do (
    start "" "%~dp0runOneCase.bat" %CASE% %%C
    timeout /t 1 > nul
)

for %%D in (%RAND_LIST4%) do (
    start "" "%~dp0runOneCase.bat" %CASE% %%D
    timeout /t 1 > nul
)

exit /b

