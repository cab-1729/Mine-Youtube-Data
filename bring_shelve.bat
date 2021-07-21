@echo off
cd storage
for %%i in (*.dat) do copy /y %%i ..\%%i
for %%i in (*.dir) do copy /y %%i ..\%%i
for %%i in (*.bak) do copy /y %%i ..\%%i
cd ..
