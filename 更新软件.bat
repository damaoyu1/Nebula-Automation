@echo off
cd /d "%~dp0"
git fetch --all
git reset --hard origin/master
git pull
pause