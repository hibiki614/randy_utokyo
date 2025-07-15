@echo off
setlocal 

:: ==== ?V?i???I??????? ====
set CASE=no01

:: ==== ???????X?g ====
set RAND_LIST1=rand03 rand04 rand05   
set RAND_LIST2=rand06 rand07 rand08 rand09 rand10
set RAND_LIST3=rand11 rand12 rand13 rand14 rand15
set RAND_LIST4=rand16 rand17 rand18 rand19 rand20

:: ==== ?e?t?H???_????? ProcessOne.bat ????????s ====
for %%A in (%RAND_LIST1%) do (
    start "" "%~dp0runOneCase2.bat" %CASE% %%A
    timeout /t 1 > nul
)

exit /b

