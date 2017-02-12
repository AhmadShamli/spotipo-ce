@echo off

REM add C:\Program Files\MySQL\MySQL Server 5.7\bin to path
set PATH=%PATH%;C:\Program Files\MySQL\MySQL Server 5.7\bin
set PATH=%PATH%;C:\Python27;C:\Python27\Scripts

set PATH=%PATH%;C:\spotipo\tools;C:\Program Files (x86)\Git\bin

REM check if python installed
where /q python.exe
IF ERRORLEVEL 1 (
    ECHO Python is missing. Ensure it is installed and placed in your PATH.
    ECHO After fixing, rerun C:\spotipo\scripts\postinstall.bat
    pause
    EXIT /B
) 
where /q pip
IF ERRORLEVEL 1 (
    python C:\spotipo\tools\get-pip.py

) 
where /q pip
IF ERRORLEVEL 1 (
    ECHO pip is missing. Ensure python scripts folder is added to path.
    ECHO After fixing, rerun C:\spotipo\scripts\postinstall.bat
    pause
    EXIT /B
) 

where /q mysql
IF ERRORLEVEL 1 (
    ECHO mysql is missing. Ensure MySQL server bin is added to path.
    ECHO After fixing, rerun C:\spotipo\scripts\postinstall.bat
    pause
    EXIT /B

) 

where /q git
IF ERRORLEVEL 1 (
    ECHO git is missing. something went wrong with install
    ECHO After fixing, rerun C:\spotipo\scripts\postinstall.bat
    pause
    EXIT /B
) 

cd C:\spotipo


python C:\spotipo\manage.py db migrate
python C:\spotipo\manage.py db upgrade
