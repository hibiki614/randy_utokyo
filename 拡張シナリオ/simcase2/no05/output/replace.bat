@echo off
REM ------------------------------
REM 変数の設定
REM ------------------------------
set NO=05
set OLD=I_09_1204235410434_auto
set NEW=I_09_1204235410499

echo ==== Case1_no%NO% のファイルを処理します ====

REM ------------------------------
REM 対象ファイルを順番に処理
REM Case1_no03_r01.mavn ～ Case1_no03_r20.mavn を想定
REM ------------------------------
for %%F in (Case1_no%NO%*_r*.mavn) do (
    echo ファイル: %%F
    powershell -Command ^
      "(Get-Content '%%F') -replace '%OLD%','%NEW%' | Set-Content '%%F'"
)

echo ==== 完了しました ====
pause
*