@echo off
for %%i in (*.dat) do copy /y %%i storage\%%i
for %%i in (*.dir) do copy /y %%i storage\%%i
for %%i in (*.bak) do copy /y %%i storage\%%i
