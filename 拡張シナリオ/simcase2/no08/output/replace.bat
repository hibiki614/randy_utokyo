@echo off
REM ------------------------------
REM �ϐ��̐ݒ�
REM ------------------------------
set NO=08
set OLD=I_09_1204235410434_auto
set NEW=I_09_1204235410499

echo ==== Case1_no%NO% �̃t�@�C�����������܂� ====

REM ------------------------------
REM �Ώۃt�@�C�������Ԃɏ���
REM Case1_no03_r01.mavn �` Case1_no03_r20.mavn ��z��
REM ------------------------------
for %%F in (Case1_no%NO%*_r*.mavn) do (
    echo �t�@�C��: %%F
    powershell -Command ^
      "(Get-Content '%%F') -replace '%OLD%','%NEW%' | Set-Content '%%F'"
)

echo ==== �������܂��� ====
pause
*